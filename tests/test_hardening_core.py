"""Elements 1 to 3: validated output, bounded retry, timeout and cost ceiling."""

import json

import pytest
from pydantic import ValidationError

from v2_hardened import extractor as ex
from v2_hardened.client import Reply
from v2_hardened.schema import TicketExtraction

TICKET = "You charged me twice for invoice INV-4471."
GOOD = json.dumps({"category": "billing", "urgency": "high", "entities": ["INV-4471"],
                   "suggested_action": "Refund the duplicate charge."})
BAD = json.dumps({"category": "refund_department", "urgency": "high", "entities": [],
                  "suggested_action": "x"})


class StubClient:
    """Replies in sequence. Each reply carries its own cost, as the real one does."""

    def __init__(self, replies, cost=0.001, raises=None):
        self._replies = list(replies)
        self._cost = cost
        self._raises = raises
        self.calls = []

    def complete(self, *, system, user, json_schema):
        self.calls.append({"system": system, "user": user, "json_schema": json_schema})
        if self._raises:
            raise self._raises
        text = self._replies.pop(0) if self._replies else self._replies_exhausted()
        return Reply(text=text, cost_usd=self._cost)

    def _replies_exhausted(self):
        raise AssertionError("the extractor asked for more replies than the test provided")


def test_a_validation_failure_is_retried_and_the_second_reply_is_returned():
    client = StubClient([BAD, GOOD])

    result = ex.extract_ticket(TICKET, client)

    assert result.category == "billing"
    assert len(client.calls) == 2


def test_attempts_stop_at_the_maximum_when_nothing_ever_validates():
    client = StubClient([BAD] * 10)

    with pytest.raises(ValidationError):
        ex.extract_ticket(TICKET, client)

    assert len(client.calls) == ex.MAX_ATTEMPTS


def test_a_transport_error_is_not_retried_here():
    """The SDK already retries those with backoff. Doing it again would duplicate it."""
    client = StubClient([], raises=ConnectionError("the socket died"))

    with pytest.raises(ConnectionError):
        ex.extract_ticket(TICKET, client)

    assert len(client.calls) == 1


def test_no_further_attempt_is_made_once_the_cost_ceiling_is_reached():
    # One call costs more than the whole ceiling, so there can be no second.
    client = StubClient([BAD] * 10, cost=ex.COST_CEILING_USD)

    with pytest.raises(ValidationError):
        ex.extract_ticket(TICKET, client)

    assert len(client.calls) == 1


def test_empty_input_returns_unknown_without_calling_the_provider():
    client = StubClient([GOOD])

    result = ex.extract_ticket("", client)

    assert (result.category, result.urgency) == ("unknown", "unknown")
    assert client.calls == []
    assert result.consulted_model is False


def test_whitespace_only_input_is_treated_the_same():
    client = StubClient([GOOD])

    result = ex.extract_ticket("   \n\t ", client)

    assert result.category == "unknown"
    assert client.calls == []


def test_a_real_answer_is_marked_as_having_consulted_the_model():
    result = ex.extract_ticket(TICKET, StubClient([GOOD]))

    assert result.consulted_model is True


def test_the_marker_never_reaches_the_provider_schema():
    """It is a private attribute: the provider must not be told about it."""
    assert "consulted" not in json.dumps(TicketExtraction.model_json_schema())


def test_the_real_client_sends_an_explicit_timeout():
    """Checked by inspecting what the SDK received, not by waiting for one."""
    from v2_hardened.client import AnthropicClient, DEFAULT_TIMEOUT

    class FakeSDK:
        def __init__(self):
            self.kwargs = None
            outer = self

            class M:
                def create(self, **kw):
                    outer.kwargs = kw
                    block = type("B", (), {"type": "text", "text": GOOD})()
                    usage = type("U", (), {"input_tokens": 700, "output_tokens": 70})()
                    return type("R", (), {"content": [block], "usage": usage,
                                          "model": "claude-sonnet-5"})()

            self.messages = M()

    sdk = FakeSDK()
    AnthropicClient(api=sdk).complete(system="s", user="u", json_schema={})

    assert sdk.kwargs["timeout"] == DEFAULT_TIMEOUT


def test_the_client_reports_what_the_call_cost():
    from v2_hardened.client import AnthropicClient

    class FakeSDK:
        def __init__(self):
            class M:
                def create(self, **kw):
                    block = type("B", (), {"type": "text", "text": GOOD})()
                    usage = type("U", (), {"input_tokens": 1_000_000, "output_tokens": 0})()
                    return type("R", (), {"content": [block], "usage": usage,
                                          "model": "claude-sonnet-5"})()

            self.messages = M()

    reply = AnthropicClient(api=FakeSDK()).complete(system="s", user="u", json_schema={})

    assert reply.cost_usd == pytest.approx(3.0)   # one million input tokens
