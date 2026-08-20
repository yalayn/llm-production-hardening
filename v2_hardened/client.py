"""The seam between this codebase and the LLM provider.

Everything above this module deals in plain strings. That is deliberate: it
lets the tests drive malformed JSON, schema violations and provider failures
through the real validation path without spending a token. If the seam returned
an already-validated object instead, the hardening this project exists to
demonstrate would never run under test.
"""

from typing import Any, Dict, Optional, Protocol

import anthropic

DEFAULT_MODEL = "claude-sonnet-5"

# The extraction payload is a handful of short fields. This is a cost ceiling,
# not a guess -- the whole experiment runs on a fixed token budget.
DEFAULT_MAX_TOKENS = 1024


class LLMClient(Protocol):
    """One call to a language model. The only thing this project mocks."""

    def complete(self, *, system: str, user: str, json_schema: Dict[str, Any]) -> str:
        """Return the model's raw text response.

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
        api: Optional[anthropic.Anthropic] = None,
    ) -> None:
        # Credentials resolve from the environment; nothing is read or stored here.
        self._api = api or anthropic.Anthropic()
        self._model = model
        self._max_tokens = max_tokens

    def complete(self, *, system: str, user: str, json_schema: Dict[str, Any]) -> str:
        response = self._api.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": json_schema}},
        )
        for block in response.content:
            if block.type == "text":
                return block.text
        raise ValueError("the provider returned a response with no text block")
