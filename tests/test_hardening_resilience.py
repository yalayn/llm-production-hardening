"""Elements 4 to 6: cache, deterministic fallback, structured logging."""

import json

import pytest

from v2_hardened import extractor as ex
from v2_hardened.cache import InMemoryCache
from v2_hardened.client import Reply

TICKET = "You charged me twice for invoice INV-4471."
GOOD = json.dumps({"category": "billing", "urgency": "high", "entities": ["INV-4471"],
                   "suggested_action": "Refund the duplicate charge."})
BAD = json.dumps({"category": "refund_department", "urgency": "high", "entities": [],
                  "suggested_action": "x"})


class StubClient:
    model = "claude-sonnet-5"

    def __init__(self, replies, cost=0.0001, raises=None):
        self._replies = list(replies)
        self._cost = cost
        self._raises = raises
        self.calls = 0

    def complete(self, *, system, user, json_schema):
        self.calls += 1
        if self._raises:
            raise self._raises
        return Reply(text=self._replies.pop(0), cost_usd=self._cost)


def run(client, text=TICKET, cache=None, sink=None):
    return ex.extract_ticket(text, client, cache=cache, log=sink)


# ---------- element 4: cache ----------

def test_the_same_input_twice_costs_one_call():
    client, cache = StubClient([GOOD]), InMemoryCache()

    first = run(client, cache=cache)
    second = run(client, cache=cache)

    assert client.calls == 1
    assert first.model_dump() == second.model_dump()
    assert second.outcome == "cached"


def test_changing_the_prompt_changes_the_key():
    """Keyed on the ticket alone, an edited prompt would serve the old answer."""
    client, cache = StubClient([GOOD, GOOD]), InMemoryCache()

    run(client, cache=cache)
    original = ex.SYSTEM_PROMPT
    try:
        ex.SYSTEM_PROMPT = original + "\nAlso be terse."
        run(client, cache=cache)
    finally:
        ex.SYSTEM_PROMPT = original

    assert client.calls == 2


def test_a_failure_is_not_cached():
    """Caching one turns a transient problem into a permanent wrong answer."""
    cache = InMemoryCache()
    failing = StubClient([BAD] * ex.MAX_ATTEMPTS)
    run(failing, cache=cache)

    recovered = StubClient([GOOD])
    result = run(recovered, cache=cache)

    assert recovered.calls == 1
    assert result.category == "billing"


# ---------- element 5: fallback ----------

def test_a_provider_that_never_validates_yields_a_degraded_result():
    result = run(StubClient([BAD] * ex.MAX_ATTEMPTS))

    assert result.outcome == "degraded"
    assert (result.category, result.urgency) == ("unknown", "unknown")


def test_a_transport_failure_also_degrades_rather_than_raising():
    result = run(StubClient([], raises=ConnectionError("socket died")))

    assert result.outcome == "degraded"


def test_a_programming_error_propagates_and_is_never_degraded():
    """A fallback wide enough to swallow bugs means bugs are never found."""

    class Broken:
        model = "claude-sonnet-5"

        def complete(self, **kwargs):
            raise TypeError("someone changed a signature")

    with pytest.raises(TypeError):
        run(Broken())


# ---------- element 6: logging ----------

def test_every_extraction_writes_one_record_with_the_expected_fields():
    sink = []

    run(StubClient([GOOD]), sink=sink.append)

    assert len(sink) == 1
    assert set(sink[0]) >= {"outcome", "attempts", "cost_usd", "latency_ms",
                            "input_tokens", "output_tokens", "input_sha256"}
    assert sink[0]["outcome"] == "answered"
    assert sink[0]["attempts"] == 1


def test_the_record_never_carries_the_ticket_text():
    sink = []
    secret = "ACME Corporation, account 99887766, phone 555-0134"

    run(StubClient([GOOD]), text=secret, sink=sink.append)

    assert secret not in json.dumps(sink[0])
    assert "99887766" not in json.dumps(sink[0])
    assert len(sink[0]["input_sha256"]) == 64


def test_a_cached_extraction_is_logged_as_such_and_costs_nothing():
    sink, cache = [], InMemoryCache()
    client = StubClient([GOOD])

    run(client, cache=cache, sink=sink.append)
    run(client, cache=cache, sink=sink.append)

    assert [r["outcome"] for r in sink] == ["answered", "cached"]
    assert sink[1]["cost_usd"] == 0


def test_empty_input_is_logged_without_a_call():
    sink = []

    run(StubClient([GOOD]), text="   ", sink=sink.append)

    assert sink[0]["outcome"] == "empty_input"
    assert sink[0]["attempts"] == 0
