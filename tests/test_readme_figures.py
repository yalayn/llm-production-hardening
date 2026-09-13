"""Every figure in the README must match the runs it claims to come from.

These tests skip when `evals/results/` is absent, which is the normal state of a
fresh clone: the directory is git-ignored. The guard therefore protects the
author from publishing a stale number, not the reader from reading one.
"""

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).parent.parent
RESULTS = ROOT / "evals" / "results"
README = ROOT / "README.md"


def load(name):
    path = RESULTS / name
    if not path.exists():
        pytest.skip("{} is git-ignored and absent from this checkout".format(name))
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_the_readme_exists_and_says_it_is_incomplete():
    text = README.read_text(encoding="utf-8")

    assert "Incomplete" in text
    assert "What breaks in v1 and why" in text


def test_the_fenced_reply_figure_matches_the_run():
    rows = load("v1-run2.jsonl")
    replies = [r for r in rows if r["raw"]]
    fenced = [r for r in replies if r["raw"].lstrip().startswith("```")]

    assert "{} of {}".format(len(fenced), len(replies)) in README.read_text(encoding="utf-8")


def test_the_failure_counts_match_both_runs():
    text = README.read_text(encoding="utf-8")

    for name, label in (("v1-run2.jsonl", "second"), ("v1-run1.jsonl", "first")):
        rows = load(name)
        failed = sum(1 for r in rows if not r["ok"])
        assert "{} of {}".format(failed, len(rows)) in text, (label, failed)


def test_the_thinking_block_figure_matches_the_first_run():
    rows = load("v1-run1.jsonl")
    blocked = sum(
        1 for r in rows
        if not r["ok"] and r["error"]["type"] in {"JSONDecodeError", "AttributeError"}
    )

    assert "{} of {}".format(blocked, len(rows)) in README.read_text(encoding="utf-8")


def test_the_readme_admits_what_the_runs_could_not_measure():
    text = README.read_text(encoding="utf-8")

    assert "prompt injection" in text.lower()
    assert "accuracy" in text.lower()


def test_the_model_and_dates_are_named():
    text = README.read_text(encoding="utf-8")

    assert "claude-sonnet-5" in text
    assert "2026-09-08" in text and "2026-09-13" in text
