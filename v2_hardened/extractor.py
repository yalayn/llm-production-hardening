"""Turn one free-text support ticket into validated triage data."""

from pydantic import ValidationError

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


def _without_consulting_the_model() -> TicketExtraction:
    """The honest answer when there is nothing to read, reached without paying."""
    result = TicketExtraction(
        category="unknown",
        urgency="unknown",
        entities=[],
        suggested_action="Ask the customer what they need; the ticket was empty.",
    )
    result._consulted_model = False
    return result


def extract_ticket(ticket_text: str, client: LLMClient) -> TicketExtraction:
    """Extract triage data from `ticket_text`.

    Validation runs here even though the provider was asked to conform: a
    response can satisfy the schema and still be wrong, and a provider can
    always return something the schema did not allow.
    """
    if not ticket_text.strip():
        # The provider rejects empty content with a 400, so this call cannot
        # succeed. Not making it is what a cost ceiling is for, and `unknown` is
        # what the golden dataset declares to be the right answer anyway.
        return _without_consulting_the_model()

    schema = TicketExtraction.model_json_schema()
    spent = 0.0
    failure = None

    for _ in range(MAX_ATTEMPTS):
        if spent >= COST_CEILING_USD:
            break

        # Transport errors propagate: the SDK already retries those with backoff,
        # and doing it again here would duplicate a better-tested mechanism.
        reply = client.complete(system=SYSTEM_PROMPT, user=ticket_text, json_schema=schema)
        spent += reply.cost_usd

        try:
            return TicketExtraction.model_validate_json(reply.text)
        except ValidationError as exc:
            failure = exc

    raise failure
