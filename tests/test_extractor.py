"""Fase 0 vertical: one extraction, end to end, with no network involved."""

import json

import pytest
from pydantic import ValidationError

from v2_hardened.extractor import extract_ticket
from v2_hardened.schema import TicketExtraction

WELL_FORMED = json.dumps(
    {
        "category": "billing",
        "urgency": "high",
        "entities": ["INV-4471"],
        "suggested_action": "Refund the duplicate charge on invoice INV-4471.",
    }
)

TICKET = "You charged me twice for invoice INV-4471 this morning. Please fix it."


class StubClient:
    """An LLMClient that replays a canned response and records what it was asked.

    This is the entire reason the seam sits at the provider boundary: the stub
    can hand back anything a real provider might, including things it should
    not, and the code under test still does its real work.
    """

    def __init__(self, response: str) -> None:
        self._response = response
        self.calls = []

    def complete(self, *, system: str, user: str, json_schema: dict) -> str:
        self.calls.append({"system": system, "user": user, "json_schema": json_schema})
        return self._response


def test_returns_validated_triage_data_for_a_well_formed_response():
    client = StubClient(WELL_FORMED)

    result = extract_ticket(TICKET, client)

    assert isinstance(result, TicketExtraction)
    assert result.category == "billing"
    assert result.urgency == "high"
    assert result.entities == ["INV-4471"]


def test_asks_the_provider_to_constrain_the_response():
    client = StubClient(WELL_FORMED)

    extract_ticket(TICKET, client)

    schema = client.calls[0]["json_schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "category",
        "urgency",
        "entities",
        "suggested_action",
    }
    assert "billing" in schema["properties"]["category"]["enum"]


def test_rejects_a_category_the_schema_does_not_allow():
    """The provider was asked to constrain its output. It can still fail to."""
    client = StubClient(WELL_FORMED.replace('"billing"', '"refund_department"'))

    with pytest.raises(ValidationError):
        extract_ticket(TICKET, client)


def test_rejects_a_response_that_is_not_json_at_all():
    client = StubClient("Sure! Here is the JSON you asked for:")

    with pytest.raises(ValidationError):
        extract_ticket(TICKET, client)
