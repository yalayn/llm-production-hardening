"""The output contract: what a support ticket extraction is allowed to produce.

This module is the only definition of the target shape. The naive version does
not import it -- it describes the shape in prose inside its prompt, which is the
whole difference being measured.
"""

from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

# Inlined as `enum` arrays in the JSON Schema. An Enum class would produce
# `$ref`/`$defs` indirection instead, which buys nothing here and makes the
# schema harder to read in a request payload.
Category = Literal[
    "billing",
    "technical",
    "account",
    "feature_request",
    "other",
    "unknown",
]

Urgency = Literal["low", "medium", "high", "critical", "unknown"]


class TicketExtraction(BaseModel):
    """Structured triage data pulled out of one free-text support ticket."""

    # `forbid` makes Pydantic emit `additionalProperties: false`, which is what
    # lets the provider constrain the response instead of merely suggesting it.
    model_config = ConfigDict(extra="forbid")

    category: Category = Field(
        description=(
            "What the ticket is about. Use 'other' when the ticket is clear but "
            "fits none of the listed categories, and 'unknown' when the ticket "
            "does not say enough to tell."
        )
    )
    urgency: Urgency = Field(
        description="How quickly this needs a human, judged from the ticket alone."
    )
    entities: List[str] = Field(
        description=(
            "Concrete things named in the ticket: order or invoice IDs, product "
            "names, error codes, URLs. Empty list if the ticket names none."
        )
    )
    suggested_action: str = Field(
        description="One short imperative sentence describing the next step."
    )

    # Private on purpose: the provider is never told this field exists, so it
    # cannot appear in the schema sent with the request.
    #
    # One marker with four values rather than several booleans: two ways to say
    # the same thing is how documents and code start contradicting each other.
    _outcome: str = PrivateAttr(default="answered")

    @property
    def outcome(self) -> str:
        """How this result was reached.

        `answered` -- the provider replied and the reply validated.
        `cached` -- an identical question had already been answered.
        `degraded` -- the provider could not be made to yield a valid reply.
        `empty_input` -- there was nothing to ask about, so nothing was spent.
        """
        return self._outcome
