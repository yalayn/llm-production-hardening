"""The naive baseline. These tests pin how it works AND how it fails."""

import json
from unittest import mock

import pytest

from v1_naive.extractor import extract_ticket

TICKET = "You charged me twice for invoice INV-4471 this morning. Please fix it."

WELL_FORMED = json.dumps(
    {
        "category": "billing",
        "urgency": "high",
        "entities": ["INV-4471"],
        "suggested_action": "Refund the duplicate charge on invoice INV-4471.",
    }
)


class FakeSDK:
    """Stands in for `anthropic.Anthropic`, shaped like the object v1 talks to.

    Faking the SDK's own shape -- an object with `.messages.create` returning
    content blocks -- rather than a clean interface is the cost of having no
    seam. That cost is one of the things this repository measures, so the
    awkwardness here is deliberate and should not be tidied away.
    """

    def __init__(self, text):
        self._text = text
        self.calls = []
        outer = self

        class _Messages:
            def create(self, **kwargs):
                outer.calls.append(kwargs)
                block = mock.Mock()
                block.text = outer._text
                response = mock.Mock()
                response.content = [block]
                return response

        self.messages = _Messages()


def test_returns_a_plain_dict_for_a_well_formed_response():
    result = extract_ticket(TICKET, FakeSDK(WELL_FORMED))

    assert isinstance(result, dict)
    assert result["category"] == "billing"
    assert result["urgency"] == "high"
    assert result["entities"] == ["INV-4471"]


def test_json_wrapped_in_prose_raises_and_is_not_handled():
    """A documented result of this version, not an accident."""
    client = FakeSDK("Sure! Here is the JSON:\n" + WELL_FORMED)

    with pytest.raises(json.JSONDecodeError):
        extract_ticket(TICKET, client)


def test_an_invented_category_passes_straight_through():
    """Nothing checks the value, so the caller receives it as if it were real."""
    client = FakeSDK(WELL_FORMED.replace('"billing"', '"refund_department"'))

    result = extract_ticket(TICKET, client)

    assert result["category"] == "refund_department"


def test_a_missing_field_is_not_noticed_here():
    """The KeyError lands on the caller, far from the cause."""
    payload = json.loads(WELL_FORMED)
    del payload["urgency"]
    client = FakeSDK(json.dumps(payload))

    result = extract_ticket(TICKET, client)

    assert "urgency" not in result


def test_builds_a_real_client_when_none_is_given():
    """Verified without a request: the constructor is replaced, not called for real."""
    with mock.patch("v1_naive.extractor.anthropic.Anthropic") as constructor:
        constructor.return_value = FakeSDK(WELL_FORMED)

        extract_ticket(TICKET)

        constructor.assert_called_once_with()


def test_does_not_import_from_the_hardened_implementation():
    """Guards the comparison itself, which erodes silently if the two converge."""
    source = (
        __import__("pathlib").Path(__file__).parent.parent / "v1_naive" / "extractor.py"
    ).read_text()

    assert "v2_hardened" not in source
