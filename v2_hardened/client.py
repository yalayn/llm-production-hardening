"""The seam between this codebase and the LLM provider.

Everything above this module deals in plain strings. That is deliberate: it
lets the tests drive malformed JSON, schema violations and provider failures
through the real validation path without spending a token. If the seam returned
an already-validated object instead, the hardening this project exists to
demonstrate would never run under test.
"""

from typing import Any, Dict, NamedTuple, Optional, Protocol

import anthropic

DEFAULT_MODEL = "claude-sonnet-5"

# Seconds. Short enough to be a decision rather than the SDK's ten-minute default:
# a triage call that has not answered by now is not going to.
DEFAULT_TIMEOUT = 30.0

# USD per million tokens, by model. Owned here because this is where a call is
# made; the eval harness imports it rather than keeping a second copy that could
# drift from this one.
PRICING = {"claude-sonnet-5": (3.0, 15.0)}


class Reply(NamedTuple):
    """One provider answer: the raw text, and what it cost to obtain.

    The text stays raw -- validation belongs to the caller, which is the whole
    reason this seam exists. The cost rides along because a per-request ceiling
    cannot be enforced from a string, and because a measured number beats an
    estimate: the estimate for this project was wrong by a factor of two until a
    real call corrected it.
    """

    text: str
    cost_usd: float
    input_tokens: int = 0
    output_tokens: int = 0


def cost_of(model: str, input_tokens: int, output_tokens: int) -> float:
    per_in, per_out = PRICING.get(model, (0.0, 0.0))
    return input_tokens / 1e6 * per_in + output_tokens / 1e6 * per_out

# The extraction payload is a handful of short fields. This is a cost ceiling,
# not a guess -- the whole experiment runs on a fixed token budget.
DEFAULT_MAX_TOKENS = 1024


class LLMClient(Protocol):
    """One call to a language model. The only thing this project mocks."""

    # Read-only. The cache key has to cover the model: the same question asked of
    # a different model is a different question.
    model: str

    def complete(self, *, system: str, user: str, json_schema: Dict[str, Any]) -> "Reply":
        """Return the model's raw text response and what the call cost.

        Raises whatever the provider raises: transport errors are the caller's
        problem to handle, not this layer's to swallow.
        """
        ...


class AnthropicClient:
    """The real client.

    Sends `json_schema` as a response-format constraint, so the provider is
    asked to produce conforming JSON rather than merely encouraged to. The
    caller still validates what comes back -- see `extractor.extract_ticket`.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout: float = DEFAULT_TIMEOUT,
        api: Optional[anthropic.Anthropic] = None,
    ) -> None:
        # Credentials resolve from the environment; nothing is read or stored here.
        self._api = api or anthropic.Anthropic()
        self.model = model
        self._max_tokens = max_tokens
        self._timeout = timeout

    def complete(self, *, system: str, user: str, json_schema: Dict[str, Any]) -> Reply:
        response = self._api.messages.create(
            model=self.model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": json_schema}},
            timeout=self._timeout,
        )
        usage = response.usage
        cost = cost_of(response.model, usage.input_tokens, usage.output_tokens)
        for block in response.content:
            if block.type == "text":
                return Reply(text=block.text, cost_usd=cost,
                             input_tokens=usage.input_tokens,
                             output_tokens=usage.output_tokens)
        raise ValueError("the provider returned a response with no text block")
