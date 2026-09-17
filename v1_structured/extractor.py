"""Extract structured data from a support ticket, asking the provider to
constrain its reply.

The naive version with one call changed, and nothing else: no validation on
arrival, no retry, no timeout, no budget, no cache, no fallback, no logging, no
switch. It exists to measure where "the provider constrains it for you" stops
being enough.

The forty lines shared with `v1_naive` are copied rather than imported. The three
implementations have to stay independently frozen, or a change to one silently
changes what the comparison is comparing.
"""

import json
from typing import Any, Dict, Optional

import anthropic

MODEL = "claude-sonnet-5"
MAX_TOKENS = 1024

# Declared here as a literal rather than imported from the hardened version, for
# the same reason the golden dataset declares its own vocabulary: three separate
# statements that agree are evidence, while one shared constant hides the day
# they stop agreeing. It is also what someone reaching for structured output the
# first time actually writes -- by hand, from the documentation.
SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["category", "urgency", "entities", "suggested_action"],
    "properties": {
        "category": {
            "type": "string",
            "enum": ["billing", "technical", "account", "feature_request", "other", "unknown"],
        },
        "urgency": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical", "unknown"],
        },
        "entities": {"type": "array", "items": {"type": "string"}},
        "suggested_action": {"type": "string"},
    },
}

PROMPT = """You are a support ticket triage system.

Read the ticket and extract the requested fields. Use "unknown" if the ticket
does not say enough to decide."""


def extract_ticket(ticket_text: str, client: Optional[Any] = None) -> Dict[str, Any]:
    """Return the triage data for `ticket_text` as a dict."""
    client = client or anthropic.Anthropic()

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=PROMPT,
        messages=[{"role": "user", "content": ticket_text}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    )

    for block in response.content:
        if block.type == "text":
            return json.loads(block.text)
    raise ValueError("the response contained no text block")
