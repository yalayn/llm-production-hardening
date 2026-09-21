"""The harness must measure the elements the comparative table credits.

Three things are covered here: that the hardened version is given a cache whose
lifetime is one run, that the diagnostic implementation is a real control, and
that the runs the README cites are committed rather than ignored.

Every test drives a fake SDK; none reaches the network.
"""

import json
import subprocess

import pytest

from evals import runner
from v2_hardened.extractor import SYSTEM_PROMPT
from v2_hardened.schema import TicketExtraction

TICKET = "You charged me twice for invoice INV-4471."
GOOD = json.dumps({
    "category": "billing", "urgency": "high", "entities": ["INV-4471"],
    "suggested_action": "Refund the duplicate charge.",
})
INVENTED = json.dumps({
    "category": "refund_department", "urgency": "high", "entities": [],
    "suggested_action": "x",
})


class _Block:
    def __init__(self, type_, text=None):
        self.type = type_
        self.text = text


class _Usage:
    def __init__(self, input_tokens, output_tokens):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _Response:
    def __init__(self, text):
        self.model = "claude-sonnet-5"
        self.usage = _Usage(100, 20)
        # A thinking block first, as Sonnet 5 really sends.
        self.content = [_Block("thinking"), _Block("text", text)]


class FakeSDK:
    """The SDK's shape, recording every request it was given."""

    def __init__(self, text=GOOD, raises=None):
        self._text = text
        self._raises = raises
        self.requests = []
        outer = self

        class _Messages:
            def create(self, **kwargs):
                outer.requests.append(kwargs)
                if outer._raises:
                    raise outer._raises
                return _Response(outer._text)

        self.messages = _Messages()

    @property
    def kwargs(self):
        return self.requests[-1]


def read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build(name, sdk):
    """Resolve an implementation the way `main` does, and give it a recorder."""
    return runner.IMPLEMENTATIONS[name](), runner.UsageRecorder(sdk)


# --- the cache is wired, and its lifetime is the run -------------------------

def test_the_hardened_version_is_given_a_cache_so_one_question_is_paid_for_once():
    implementation, recorder = build("v2_hardened", FakeSDK())

    first = implementation(TICKET, recorder)
    second = implementation(TICKET, recorder)

    assert first.outcome == "answered"
    assert second.outcome == "cached"
    assert len(recorder.calls) == 1


def test_each_run_starts_with_a_cold_cache():
    """A module-level cache would make the second run in a process start warm."""
    sdk = FakeSDK()
    first_run, recorder = build("v2_hardened", sdk)
    second_run = runner.IMPLEMENTATIONS["v2_hardened"]()

    first_run(TICKET, recorder)
    result = second_run(TICKET, recorder)

    assert result.outcome == "answered"
    assert len(recorder.calls) == 2


def test_a_full_run_hits_the_cache_exactly_once_on_the_duplicate_case(tmp_path):
    """The dataset carries one byte-identical ticket, built to exercise element 4."""
    implementation, recorder = build("v2_hardened", FakeSDK())
    out = tmp_path / "r.jsonl"

    runner.run(implementation, runner.load_cases(), out, budget=1000.0, recorder=recorder)

    cached = [r["id"] for r in read(out) if r["outcome"] == "cached"]
    assert cached == ["edge-duplicate-of-billing"]


def test_the_cached_case_cost_nothing(tmp_path):
    implementation, recorder = build("v2_hardened", FakeSDK())
    out = tmp_path / "r.jsonl"

    runner.run(implementation, runner.load_cases(), out, budget=1000.0, recorder=recorder)

    cached = [r for r in read(out) if r["outcome"] == "cached"]
    assert cached and all(r["usage"] == [] for r in cached)


@pytest.mark.parametrize("name", ["v1_naive", "v1_structured"])
def test_no_cache_reaches_the_versions_that_do_not_have_one(name):
    """They take no such parameter; passing one would raise rather than be ignored."""
    implementation, recorder = build(name, FakeSDK())

    assert implementation(TICKET, recorder)["category"] == "billing"


def test_every_registered_implementation_is_a_factory_that_composes_afresh():
    """`all(callable(v))` passes against a plain function and proves nothing.

    What matters is that resolving a name twice yields two independent
    implementations, so no state can travel from one run into the next.
    """
    for name, factory in runner.IMPLEMENTATIONS.items():
        first, second = factory(), factory()
        assert callable(first), name
        assert first is not second, name


# --- the diagnostic is a real control ---------------------------------------

def test_the_diagnostic_sends_exactly_what_the_hardened_version_sends():
    """The whole point: the two requests differ in nothing the provider sees."""
    diagnostic, diag_recorder = build("v1_structured_described", FakeSDK())
    hardened, hard_recorder = build("v2_hardened", FakeSDK())

    diagnostic(TICKET, diag_recorder)
    hardened(TICKET, hard_recorder)

    seen = ("model", "max_tokens", "system", "messages", "output_config")
    sent = diag_recorder._api.kwargs
    reference = hard_recorder._api.kwargs
    assert {k: sent[k] for k in seen} == {k: reference[k] for k in seen}


def test_the_diagnostic_sends_the_described_schema_rather_than_a_bare_one():
    """The bare array is what `v1_structured` sends; the description is the variable."""
    diagnostic, recorder = build("v1_structured_described", FakeSDK())

    diagnostic(TICKET, recorder)

    entities = recorder._api.kwargs["output_config"]["format"]["schema"]["properties"]["entities"]
    assert "description" in entities
    assert entities == TicketExtraction.model_json_schema()["properties"]["entities"]


def test_the_diagnostic_uses_the_hardened_system_prompt():
    diagnostic, recorder = build("v1_structured_described", FakeSDK())

    diagnostic(TICKET, recorder)

    assert recorder._api.kwargs["system"] == SYSTEM_PROMPT


def test_the_diagnostic_validates_nothing_on_arrival():
    """It is v1's code path. An invented category comes back untouched."""
    diagnostic, recorder = build("v1_structured_described", FakeSDK(INVENTED))

    assert diagnostic(TICKET, recorder)["category"] == "refund_department"


def test_the_diagnostic_neither_retries_nor_degrades():
    diagnostic, recorder = build("v1_structured_described", FakeSDK(raises=RuntimeError("provider down")))

    with pytest.raises(RuntimeError):
        diagnostic(TICKET, recorder)

    assert len(recorder._api.requests) == 1


def test_the_diagnostic_is_not_a_fourth_implementation_at_the_repository_root():
    """It is an instrument. ARCHITECTURE section 0 keeps three columns."""
    from evals import diagnostic

    assert diagnostic.__name__ == "evals.diagnostic"


# --- the evidence is committed ----------------------------------------------

@pytest.mark.parametrize("name", [
    "final-v1-naive.jsonl",
    "final-v1-structured.jsonl",
    "final-v2-hardened.jsonl",
    "final-v1-structured-described.jsonl",
])
def test_the_final_runs_are_not_ignored(name):
    """A repository that reports numbers a reader cannot recompute asks for trust."""
    assert _is_ignored("evals/results/" + name) is False


@pytest.mark.parametrize("name", ["v1-run1.jsonl", "smoke-structured.jsonl", "run.jsonl"])
def test_the_exploratory_runs_are_still_ignored(name):
    """Working notes, not evidence. Committing them would bury the four that matter."""
    assert _is_ignored("evals/results/" + name) is True


def _is_ignored(path):
    result = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=str(__import__("pathlib").Path(__file__).parent.parent),
    )
    if result.returncode not in (0, 1):
        pytest.skip("git could not answer whether {} is ignored".format(path))
    return result.returncode == 0
