"""Extract structured data from a support ticket.

The straightforward version: ask the model for JSON, parse it, return it.
"""

import json
from typing import Any, Dict, Optional

import anthropic

MODEL = "claude-sonnet-5"
MAX_TOKENS = 1024

PROMPT = """You are a support ticket triage system.

Read the ticket and reply with JSON in exactly this shape:

{
  "category": "billing | technical | account | feature_request | other | unknown",
  "urgency": "low | medium | high | critical | unknown",
  "entities": ["any order IDs, invoice IDs, product names or error codes"],
  "suggested_action": "one short sentence describing the next step"
}

Use "unknown" if the ticket does not say enough to decide. Reply with the JSON
only."""


def extract_ticket(ticket_text: str, client: Optional[Any] = None) -> Dict[str, Any]:
    """Return the triage data for `ticket_text` as a dict."""
    client = client or anthropic.Anthropic()

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=PROMPT,
        messages=[{"role": "user", "content": ticket_text}],
    )

    for block in response.content:
        if block.type == "text":
            return json.loads(block.text)
    raise ValueError("the response contained no text block")
