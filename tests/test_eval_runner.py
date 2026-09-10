"""The run harness. Every test drives it with a stub; none reaches the network."""

import json

import pytest

from evals import runner

CASES = [
    {"id": "a", "family": "normal", "ticket": "one", "expected": {}, "notes": "x"},
    {"id": "b", "family": "normal", "ticket": "two", "expected": {}, "notes": "x"},
    {"id": "c", "family": "normal", "ticket": "three", "expected": {}, "notes": "x"},
]


class StubImpl:
    """Records how many times each case was passed to it."""

    def __init__(self, fail_on=None, usage=(100, 20)):
        self.fail_on = fail_on
        self.usage = usage
        self.seen = []

    def __call__(self, text, recorder):
        self.seen.append(text)
        recorder.record("claude-sonnet-5", *self.usage)
        if text == self.fail_on:
            raise ValueError("the provider said no")
        return {"category": "billing"}


def read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_writes_one_record_per_case_in_order(tmp_path):
    out = tmp_path / "r.jsonl"

    runner.run(StubImpl(), CASES, out, budget=1.0)

    assert [r["id"] for r in read(out)] == ["a", "b", "c"]


def test_a_failing_case_is_recorded_with_its_traceback_and_the_run_continues(tmp_path):
    out = tmp_path / "r.jsonl"

    runner.run(StubImpl(fail_on="two"), CASES, out, budget=1.0)

    records = read(out)
    assert len(records) == 3
    failed = records[1]
    assert failed["ok"] is False
    assert failed["error"]["type"] == "ValueError"
    assert "the provider said no" in failed["error"]["traceback"]
    assert records[2]["ok"] is True


def test_the_run_stops_when_the_budget_is_reached(tmp_path):
    out = tmp_path / "r.jsonl"

    # Each call costs 100/1e6*3 + 20/1e6*15 = 0.0006. Two fit in 0.001, three do not.
    summary = runner.run(StubImpl(), CASES, out, budget=0.001)

    assert summary["ran"] == 2
    assert summary["not_run"] == 1
    assert summary["stopped_on_budget"] is True
    assert len(read(out)) == 2


def test_a_completed_run_does_not_claim_it_stopped_on_budget(tmp_path):
    summary = runner.run(StubImpl(), CASES, tmp_path / "r.jsonl", budget=1.0)

    assert summary["stopped_on_budget"] is False
    assert summary["not_run"] == 0


def test_limit_runs_exactly_that_many_cases(tmp_path):
    out = tmp_path / "r.jsonl"

    runner.run(StubImpl(), CASES[:2], out, budget=1.0)

    assert len(read(out)) == 2


def test_the_runner_calls_each_case_exactly_once_and_never_retries(tmp_path):
    impl = StubImpl(fail_on="two")

    runner.run(impl, CASES, tmp_path / "r.jsonl", budget=1.0)

    assert impl.seen == ["one", "two", "three"]


def test_the_runner_does_not_alter_what_the_implementation_returned(tmp_path):
    out = tmp_path / "r.jsonl"

    runner.run(StubImpl(), CASES, out, budget=1.0)

    assert read(out)[0]["result"] == {"category": "billing"}


def test_starting_without_a_budget_is_an_error_and_runs_nothing():
    with pytest.raises(SystemExit):
        runner.main(["--impl", "v1_naive"])


def test_an_unknown_implementation_exits_listing_the_valid_names(capsys):
    with pytest.raises(SystemExit):
        runner.main(["--impl", "nope", "--budget", "0.01"])

    assert "v1_naive" in capsys.readouterr().err


def test_every_registered_implementation_is_callable():
    assert set(runner.IMPLEMENTATIONS) >= {"v1_naive", "v2_hardened"}
    assert all(callable(v) for v in runner.IMPLEMENTATIONS.values())


def test_the_budget_is_enforced_against_the_recorder_the_implementation_writes_to(tmp_path):
    """Regression: run() used to create its own recorder, so in real use the
    implementation reported usage to one object and the ceiling watched another.
    Every call would have been free as far as the ceiling was concerned."""
    recorder = runner.UsageRecorder()

    summary = runner.run(StubImpl(), CASES, tmp_path / "r.jsonl", budget=0.001, recorder=recorder)

    assert recorder.calls, "the implementation reported usage to this recorder"
    assert summary["stopped_on_budget"] is True
    assert summary["ran"] == 2


def test_failures_are_counted_in_the_summary(tmp_path):
    summary = runner.run(StubImpl(fail_on="two"), CASES, tmp_path / "r.jsonl", budget=1.0)

    assert summary["failures"] == 1


def test_every_record_carries_the_raw_reply(tmp_path):
    out = tmp_path / "r.jsonl"

    class RawStub:
        def __call__(self, text, recorder):
            recorder.record("claude-sonnet-5", 10, 2, raw='{"category":"billing"}')
            return {"category": "billing"}

    runner.run(RawStub(), CASES, out, budget=1.0)

    assert all(r["raw"] == '{"category":"billing"}' for r in read(out))


def test_a_failed_case_still_records_what_the_model_replied(tmp_path):
    """The first real run could not be read because this was missing."""
    out = tmp_path / "r.jsonl"

    class FailingStub:
        def __call__(self, text, recorder):
            recorder.record("claude-sonnet-5", 10, 2, raw="Sure! Here is the JSON:")
            raise ValueError("nope")

    runner.run(FailingStub(), CASES[:1], out, budget=1.0)

    record = read(out)[0]
    assert record["ok"] is False
    assert record["raw"] == "Sure! Here is the JSON:"
