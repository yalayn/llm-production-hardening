"""Turn one free-text support ticket into validated triage data."""

import time
from typing import Any, Callable, Optional

from pydantic import ValidationError

from v2_hardened import observability
from v2_hardened.cache import key_for
from v2_hardened.client import LLMClient
from v2_hardened.schema import TicketExtraction

# A validation failure is not congestion: the provider answered promptly and
# answered badly, so waiting changes nothing about the next attempt. What the
# maximum buys is a bound on cost and latency.
MAX_ATTEMPTS = 3

# USD for one extraction including its retries. The run harness bounds a whole
# run; this stops one pathological ticket from consuming that allowance alone.
COST_CEILING_USD = 0.02

SYSTEM_PROMPT = (
    "You are a support ticket triage system. Read the ticket and extract the "
    "requested fields.\n"
    "Answer only from what the ticket actually says. When it does not give you "
    "enough to decide, use 'unknown' -- a wrong confident answer costs more "
    "than an honest gap."
)


def _placeholder(outcome: str, action: str) -> TicketExtraction:
    """The full schema with `unknown` in both closed fields.

    The caller needs no special case, and `unknown` already means "not enough to
    decide", which is true here. The marker is what distinguishes this from an
    answer the model actually gave.
    """
    result = TicketExtraction(
        category="unknown", urgency="unknown", entities=[], suggested_action=action
    )
    result._outcome = outcome
    return result


def extract_ticket(
    ticket_text: str,
    client: LLMClient,
    cache: Optional[Any] = None,
    log: Optional[Callable[[dict], None]] = None,
) -> TicketExtraction:
    """Extract triage data from `ticket_text`, and never raise at the model.

    Validation runs here even though the provider was asked to conform: a
    response can satisfy the schema and still be wrong, and a provider can always
    return something the schema did not allow.
    """
    sink = log or observability.emit
    started = time.monotonic()
    schema = TicketExtraction.model_json_schema()
    attempts = 0
    spent = 0.0
    tokens = {"input_tokens": 0, "output_tokens": 0}

    def finish(result: TicketExtraction) -> TicketExtraction:
        sink({
            "outcome": result.outcome,
            "attempts": attempts,
            "cost_usd": round(spent, 6),
            "latency_ms": round((time.monotonic() - started) * 1000, 1),
            "input_sha256": observability.fingerprint(ticket_text),
            **tokens,
        })
        return result

    if not ticket_text.strip():
        # The provider rejects empty content with a 400, so this call cannot
        # succeed. Not making it is what a cost ceiling is for, and `unknown` is
        # what the golden dataset declares to be the right answer anyway.
        return finish(_placeholder(
            "empty_input", "Ask the customer what they need; the ticket was empty."))

    key = key_for(
        ticket_text=ticket_text,
        system_prompt=SYSTEM_PROMPT,
        model=client.model,
        json_schema=schema,
    )
    if cache is not None:
        stored = cache.get(key)
        if stored is not None:
            answer = stored.model_copy()
            answer._outcome = "cached"
            return finish(answer)

    while attempts < MAX_ATTEMPTS and spent < COST_CEILING_USD:
        attempts += 1
        try:
            # Transport errors do not reach the retry: the SDK already retries
            # those with backoff, and the call sits outside the `try` below so
            # this code cannot retry them by accident.
            reply = client.complete(
                system=SYSTEM_PROMPT, user=ticket_text, json_schema=schema
            )
        except TypeError:
            # A broken signature is a defect in this codebase, not a provider
            # failure. Degrading it would hide every future mistake of its kind.
            raise
        except Exception:
            break

        spent += reply.cost_usd
        tokens["input_tokens"] += reply.input_tokens
        tokens["output_tokens"] += reply.output_tokens

        try:
            answer = TicketExtraction.model_validate_json(reply.text)
        except ValidationError:
            continue

        if cache is not None:
            # Successes only. Caching a failure turns a transient provider
            # problem into a permanent wrong answer for this input.
            cache.set(key, answer)
        return finish(answer)

    return finish(_placeholder(
        "degraded", "Route to a human: automated triage could not complete."))
