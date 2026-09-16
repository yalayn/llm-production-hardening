"""Element 7: stop consulting the model without shipping a release."""

import json

import pytest

from v2_hardened import extractor as ex
from v2_hardened import flags
from v2_hardened.cache import InMemoryCache
from v2_hardened.client import Reply

TICKET = "You charged me twice for invoice INV-4471."
GOOD = json.dumps({"category": "billing", "urgency": "high", "entities": ["INV-4471"],
                   "suggested_action": "Refund the duplicate charge."})


class StubClient:
    model = "claude-sonnet-5"

    def __init__(self, replies=None):
        self._replies = list(replies or [GOOD] * 5)
        self.calls = 0

    def complete(self, *, system, user, json_schema):
        self.calls += 1
        return Reply(text=self._replies.pop(0), cost_usd=0.0001,
                     input_tokens=700, output_tokens=70)


def run(client, text=TICKET, cache=None, sink=None):
    return ex.extract_ticket(text, client, cache=cache, log=sink or (lambda r: None))


def test_the_flag_is_on_when_the_variable_is_absent(monkeypatch):
    monkeypatch.delenv(flags.ENV_VAR, raising=False)
    client = StubClient()

    result = run(client)

    assert result.outcome == "answered"
    assert client.calls == 1


def test_with_the_flag_off_no_call_is_made(monkeypatch):
    monkeypatch.setenv(flags.ENV_VAR, "false")
    client = StubClient()

    result = run(client)

    assert result.outcome == "disabled"
    assert client.calls == 0


@pytest.mark.parametrize("value", ["0", "false", "FALSE", "False", "no", "off", "  off  "])
def test_every_recognised_off_value_turns_it_off(monkeypatch, value):
    """`false` and `0` are truthy strings in Python. Parsing must be explicit."""
    monkeypatch.setenv(flags.ENV_VAR, value)

    assert flags.extraction_enabled() is False


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", ""])
def test_recognised_on_values_leave_it_on(monkeypatch, value):
    monkeypatch.setenv(flags.ENV_VAR, value)

    assert flags.extraction_enabled() is True


def test_an_unrecognised_value_leaves_it_on(monkeypatch):
    """Deliberate: a typo must not be what takes the feature down."""
    monkeypatch.setenv(flags.ENV_VAR, "flase")

    assert flags.extraction_enabled() is True


def test_changing_the_variable_between_calls_changes_the_second(monkeypatch):
    """Read per call, not at import. A switch needing a restart is a deploy."""
    monkeypatch.delenv(flags.ENV_VAR, raising=False)
    client = StubClient()

    first = run(client)
    monkeypatch.setenv(flags.ENV_VAR, "off")
    second = run(client)

    assert (first.outcome, second.outcome) == ("answered", "disabled")
    assert client.calls == 1


def test_a_disabled_result_is_usable_and_distinguishable_from_a_degraded_one(monkeypatch):
    monkeypatch.setenv(flags.ENV_VAR, "off")

    result = run(StubClient())

    assert (result.category, result.urgency) == ("unknown", "unknown")
    assert result.outcome == "disabled"
    assert result.outcome != "degraded"


def test_the_cache_does_not_serve_while_the_flag_is_off(monkeypatch):
    """One rule: do not use the model's answers right now. A cached answer is one."""
    monkeypatch.delenv(flags.ENV_VAR, raising=False)
    cache, client = InMemoryCache(), StubClient()
    run(client, cache=cache)

    monkeypatch.setenv(flags.ENV_VAR, "off")
    result = run(client, cache=cache)

    assert result.outcome == "disabled"


def test_a_disabled_call_is_logged_with_zero_cost(monkeypatch):
    monkeypatch.setenv(flags.ENV_VAR, "off")
    sink = []

    run(StubClient(), sink=sink.append)

    assert len(sink) == 1
    assert sink[0]["outcome"] == "disabled"
    assert sink[0]["cost_usd"] == 0
    assert sink[0]["attempts"] == 0


def test_the_naive_version_has_no_switch(monkeypatch):
    """It is the point: there is nothing to turn off without a release."""
    monkeypatch.setenv(flags.ENV_VAR, "off")
    from v1_naive import extractor as naive

    source = __import__("pathlib").Path(naive.__file__).read_text()
    assert flags.ENV_VAR not in source
