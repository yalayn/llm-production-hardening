"""A control: `v1_structured`'s code path carrying `v2_hardened`'s prompt.

The comparative table credits the seven hardening elements with the gap between
`v1_structured` and `v2_hardened`. Most of that gap might not be theirs. The
hardened version also sends a schema whose fields are described and a system
prompt that tells the model what to do when the ticket is thin -- two better
instructions, which have nothing to do with validation, retries or a cost
ceiling.

This module holds everything except the seven elements fixed, so that whatever
separates it from `v2_hardened` belongs to them and to nothing else.

It imports the schema and the prompt rather than declaring them, which inverts
the rule the three implementations follow (`ARCHITECTURE.md` section 8.1). Those
state their vocabulary independently so that the day two disagree the eval says
so. A control exists for the opposite reason -- to be identical in the dimension
it holds fixed -- and a copy that drifted would stop being a control without
stopping producing a number.

It is an instrument, not a fourth thing this repository recommends, which is why
it lives here and not beside the implementations.
"""

import json
from typing import Any, Dict, Optional

import anthropic

from v2_hardened.extractor import SYSTEM_PROMPT
from v2_hardened.schema import TicketExtraction

# Declared locally, matching `v1_structured`. Not imported from the hardened
# client: if the two ever name different models the control is broken, and a
# test comparing the two requests is what has to notice, not an import that
# quietly keeps them equal.
MODEL = "claude-sonnet-5"
MAX_TOKENS = 1024

SCHEMA: Dict[str, Any] = TicketExtraction.model_json_schema()


def extract_ticket(ticket_text: str, client: Optional[Any] = None) -> Dict[str, Any]:
    """Return the triage data for `ticket_text` as a dict.

    `v1_structured`'s body, unchanged: one call, parsed blindly, returned
    unchecked. Nothing is validated, nothing is retried, nothing degrades.
    """
    client = client or anthropic.Anthropic()

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": ticket_text}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    )

    for block in response.content:
        if block.type == "text":
            return json.loads(block.text)
    raise ValueError("the response contained no text block")
