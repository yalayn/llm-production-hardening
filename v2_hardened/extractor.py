"""Turn one free-text support ticket into validated triage data."""

from v2_hardened.client import LLMClient
from v2_hardened.schema import TicketExtraction

SYSTEM_PROMPT = (
    "You are a support ticket triage system. Read the ticket and extract the "
    "requested fields.\n"
    "Answer only from what the ticket actually says. When it does not give you "
    "enough to decide, use 'unknown' -- a wrong confident answer costs more "
    "than an honest gap."
)


def extract_ticket(ticket_text: str, client: LLMClient) -> TicketExtraction:
    """Extract triage data from `ticket_text`.

    Validation runs here even though the provider was asked to conform: a
    response can satisfy the schema and still be wrong, and a provider can
    always return something the schema did not allow.
    """
    raw = client.complete(
        system=SYSTEM_PROMPT,
        user=ticket_text,
        json_schema=TicketExtraction.model_json_schema(),
    )
    return TicketExtraction.model_validate_json(raw)
