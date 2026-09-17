"""The third variant: the naive version with one call changed, and nothing else."""

import json
from unittest import mock

import pytest

from tests.helpers import imported_modules
from v1_structured.extractor import extract_ticket

TICKET = "You charged me twice for invoice INV-4471."
WELL_FORMED = json.dumps({
    "category": "billing", "urgency": "high", "entities": ["INV-4471"],
    "suggested_action": "Refund the duplicate charge.",
})


class FakeSDK:
    """The SDK's own shape, as the naive versions talk to it directly."""

    def __init__(self, text):
        self._text = text
        self.kwargs = None
        outer = self

        class _Messages:
            def create(self, **kwargs):
                outer.kwargs = kwargs
                thinking = mock.Mock(spec=["type"])
                thinking.type = "thinking"
                block = mock.Mock()
                block.type = "text"
                block.text = outer._text
                response = mock.Mock()
                response.content = [thinking, block]
                return response

        self.messages = _Messages()


def test_returns_a_plain_dict_for_a_well_formed_response():
    result = extract_ticket(TICKET, FakeSDK(WELL_FORMED))

    assert isinstance(result, dict)
    assert result["category"] == "billing"
    assert result["entities"] == ["INV-4471"]


def test_the_request_carries_a_response_format_constraint():
    """The single difference from the naive version."""
    sdk = FakeSDK(WELL_FORMED)

    extract_ticket(TICKET, sdk)

    fmt = sdk.kwargs["output_config"]["format"]
    assert fmt["type"] == "json_schema"
    assert "billing" in fmt["schema"]["properties"]["category"]["enum"]
    assert fmt["schema"]["additionalProperties"] is False


def test_nothing_validates_what_comes_back():
    """The provider was asked to constrain it. This variant takes that on trust."""
    rogue = WELL_FORMED.replace('"billing"', '"refund_department"')

    result = extract_ticket(TICKET, FakeSDK(rogue))

    assert result["category"] == "refund_department"


def test_a_transport_error_propagates_with_no_retry_and_no_fallback():
    class Exploding:
        def __init__(self):
            class M:
                def create(self, **kwargs):
                    raise ConnectionError("the socket died")

            self.messages = M()

    with pytest.raises(ConnectionError):
        extract_ticket(TICKET, Exploding())


def test_it_reads_the_text_block_not_the_first_one():
    """Same lesson the first real run taught the naive version."""
    result = extract_ticket(TICKET, FakeSDK(WELL_FORMED))

    assert result["urgency"] == "high"


def test_builds_a_real_client_when_none_is_given():
    with mock.patch("v1_structured.extractor.anthropic.Anthropic") as constructor:
        constructor.return_value = FakeSDK(WELL_FORMED)

        extract_ticket(TICKET)

        constructor.assert_called_once_with()


def test_it_imports_neither_of_the_other_implementations():
    """The three must be independently frozen, or the comparison stops comparing."""
    from v1_structured import extractor

    assert imported_modules(extractor).isdisjoint({"v1_naive", "v2_hardened"})


def test_the_runner_can_run_it_by_name():
    from evals import runner

    assert "v1_structured" in runner.IMPLEMENTATIONS
    assert callable(runner.IMPLEMENTATIONS["v1_structured"])
