"""Judging a run against the dataset."""

import json

import pytest

from evals import scoring

CASES = [
    {"id": "a", "family": "normal",
     "expected": {"category": "billing", "urgency": "high", "entities": ["INV-1"]}},
    {"id": "b", "family": "ambiguous",
     "expected": {"category": "unknown", "urgency": "unknown", "entities": []}},
]


def result(id, family="normal", ok=True, outcome="answered",
           category="billing", urgency="high", entities=("INV-1",), latency_ms=100.0):
    return {
        "id": id, "family": family, "ok": ok, "outcome": outcome,
        "result": None if not ok else {
            "category": category, "urgency": urgency, "entities": list(entities),
            "suggested_action": "whatever",
        },
        "error": None if ok else {"type": "ValueError", "traceback": "..."},
        "usage": [{"model": "claude-sonnet-5", "input_tokens": 700, "output_tokens": 70}],
        "raw": "{}", "latency_ms": latency_ms,
    }


def by_id(cases=CASES):
    return {c["id"]: c for c in cases}


# ---------- per-field rules ----------

def test_an_exact_match_scores_every_field():
    score = scoring.score_case(result("a"), by_id()["a"])

    assert score["category"] is True
    assert score["urgency"] is True
    assert score["entities"] is True


def test_entities_match_as_a_set_ignoring_case_and_order():
    score = scoring.score_case(result("a", entities=["inv-1"]), by_id()["a"])

    assert score["entities"] is True


def test_a_missing_entity_is_wrong_with_no_partial_credit():
    score = scoring.score_case(result("a", entities=[]), by_id()["a"])

    assert score["entities"] is False


def test_the_suggested_action_is_never_scored():
    score = scoring.score_case(result("a"), by_id()["a"])

    assert "suggested_action" not in score


# ---------- the trap ----------

def test_a_degraded_result_matching_the_expected_answer_is_not_correct():
    """Four cases expect unknown. Scored naively, a total failure would look right."""
    degraded = result("b", family="ambiguous", outcome="degraded",
                      category="unknown", urgency="unknown", entities=[])

    score = scoring.score_case(degraded, by_id()["b"])

    assert score["answered"] is False
    assert score["category"] is False
    assert score["urgency"] is False


def test_a_disabled_result_is_treated_the_same():
    disabled = result("b", family="ambiguous", outcome="disabled",
                      category="unknown", urgency="unknown", entities=[])

    assert scoring.score_case(disabled, by_id()["b"])["answered"] is False


def test_an_empty_input_result_is_scored_normally():
    """Reached deliberately, not by defaulting: the dataset says it is the answer."""
    guarded = result("b", family="ambiguous", outcome="empty_input",
                     category="unknown", urgency="unknown", entities=[])

    score = scoring.score_case(guarded, by_id()["b"])

    assert score["answered"] is True
    assert score["category"] is True


def test_a_result_with_no_marker_is_scored_on_its_values():
    """The naive implementation has no outcome; it is judged on what it returned."""
    naive = result("a")
    del naive["outcome"]

    score = scoring.score_case(naive, by_id()["a"])

    assert score["answered"] is True
    assert score["category"] is True


def test_a_failed_case_is_a_failure_and_scores_nothing():
    score = scoring.score_case(result("a", ok=False), by_id()["a"])

    assert score["failed"] is True
    assert score["category"] is False


# ---------- pairing ----------

def test_a_result_with_an_unknown_id_is_an_error_not_a_silent_skip():
    with pytest.raises(KeyError):
        scoring.score_case(result("ghost"), None)


def test_scoring_a_run_pairs_every_result_with_its_case():
    scores = scoring.score_run([result("a"), result("b", family="ambiguous")], CASES)

    assert [s["id"] for s in scores] == ["a", "b"]


# ---------- summary ----------

def test_the_summary_reports_per_family_and_overall():
    scores = scoring.score_run(
        [result("a"), result("b", family="ambiguous", outcome="degraded")], CASES
    )

    summary = scoring.summarise(scores)

    assert summary["overall"]["total"] == 2
    assert summary["overall"]["category_correct"] == 1
    assert summary["overall"]["no_answer"] == 1
    assert set(summary["by_family"]) == {"normal", "ambiguous"}
    assert summary["by_family"]["ambiguous"]["no_answer"] == 1


def test_the_summary_reports_both_accuracy_figures():
    """Over everything, and over what actually answered. Named, not conflated."""
    scores = scoring.score_run(
        [result("a"), result("b", family="ambiguous", outcome="degraded")], CASES
    )

    summary = scoring.summarise(scores)

    assert summary["overall"]["category_accuracy_all"] == pytest.approx(0.5)
    assert summary["overall"]["category_accuracy_answered"] == pytest.approx(1.0)


def test_the_summary_reports_cost_and_latency_percentiles():
    scores = scoring.score_run(
        [result("a", latency_ms=100.0), result("b", family="ambiguous", latency_ms=900.0)],
        CASES,
    )

    summary = scoring.summarise(scores)

    assert summary["overall"]["cost_usd"] == pytest.approx(2 * (700 / 1e6 * 3 + 70 / 1e6 * 15))
    assert summary["overall"]["latency_p50_ms"] == 100.0
    assert summary["overall"]["latency_p95_ms"] == 900.0


def test_the_runner_records_the_outcome_and_the_latency(tmp_path):
    """Neither survived into the results file, and scoring needs both."""
    from evals import runner

    class Stub:
        model = "claude-sonnet-5"

        def __call__(self, text, recorder):
            recorder.record("claude-sonnet-5", 10, 2, raw="{}")
            from v2_hardened.extractor import _placeholder
            return _placeholder("degraded", "x")

    out = tmp_path / "r.jsonl"
    runner.run(Stub(), [{"id": "a", "family": "normal", "ticket": "t"}], out, budget=1.0)

    record = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert record["outcome"] == "degraded"
    assert record["latency_ms"] >= 0


TWO_ENTITIES = {"id": "a", "family": "normal",
                "expected": {"category": "billing", "urgency": "high",
                             "entities": ["INV-1", "INV-2"]}}


def test_finding_only_some_entities_is_wrong():
    """The real partial-credit case: one of two. A mutation exposed that the
    earlier test only covered the empty set, where exact and partial agree."""
    score = scoring.score_case(result("a", entities=["INV-1"]), TWO_ENTITIES)

    assert score["entities"] is False


def test_inventing_an_extra_entity_is_wrong():
    score = scoring.score_case(
        result("a", entities=["INV-1", "INV-2", "INV-9"]), TWO_ENTITIES
    )

    assert score["entities"] is False
