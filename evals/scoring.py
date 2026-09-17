"""Judge a run against the golden dataset.

Separate from the runner on purpose. Judging is not executing, and the split buys
something concrete: a run can be re-scored without re-running. Against a provider,
re-running costs money and does not reproduce, so a change to how a field is
judged would otherwise cost another run and change the answers being compared.

The rules themselves belong to `SPEC-golden-dataset` section 5; this implements
them rather than restating them.
"""

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional, Sequence

from v2_hardened.client import cost_of

# An answer reached by defaulting is not an answer. A degraded result carries
# `unknown` in both closed fields, and four dataset cases expect exactly that --
# scored naively, a hardened version that failed completely would look correct on
# them, and the headline number would reward breaking.
NON_ANSWERS = frozenset({"degraded", "disabled"})


def score_case(record: Dict[str, Any], case: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Judge one result. A result with no matching case is an error, not a skip."""
    if case is None:
        raise KeyError("result {!r} has no case in the dataset".format(record.get("id")))

    failed = not record.get("ok", False)
    # The naive implementation has no marker, and the runner writes `null` for it.
    # Absent and null both mean the same thing: judge it on what it returned. This
    # is spelled out rather than left to `.get`'s default, which the real path
    # never reaches -- a key that exists holding None does not fall back.
    marker = record.get("outcome") or "answered"
    answered = not failed and marker not in NON_ANSWERS

    expected = case["expected"]
    produced = record.get("result") or {}
    score = {
        "id": record["id"],
        "family": record["family"],
        "failed": failed,
        "answered": answered,
        "category": answered and produced.get("category") == expected["category"],
        "urgency": answered and produced.get("urgency") == expected["urgency"],
        "entities": answered and _same_entities(produced.get("entities"), expected["entities"]),
        "cost_usd": sum(
            cost_of(c["model"], c["input_tokens"], c["output_tokens"])
            for c in record.get("usage", [])
        ),
        "latency_ms": record.get("latency_ms"),
    }
    return score


def _same_entities(produced: Optional[Sequence[str]], expected: Sequence[str]) -> bool:
    """Whole set, ignoring case and order. No partial credit.

    Precision and recall per case would be defensible and would also invite an
    argument about weighting, in a repository whose value is that its numbers
    cannot be argued with.
    """
    got = {e.strip().lower() for e in (produced or [])}
    want = {e.strip().lower() for e in expected}
    return got == want


def score_run(records: List[Dict[str, Any]], cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_id = {c["id"]: c for c in cases}
    return [score_case(r, by_id.get(r["id"])) for r in records]


def _percentile(values: List[float], fraction: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    index = min(int(round(fraction * (len(ordered) - 1))), len(ordered) - 1)
    return ordered[index]


def _tally(scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(scores)
    answered = sum(1 for s in scores if s["answered"])
    latencies = [s["latency_ms"] for s in scores if s["latency_ms"] is not None]
    tally = {
        "total": total,
        "answered": answered,
        "no_answer": total - answered - sum(1 for s in scores if s["failed"]),
        "failed": sum(1 for s in scores if s["failed"]),
        "cost_usd": round(sum(s["cost_usd"] for s in scores), 6),
        "latency_p50_ms": _percentile(latencies, 0.50),
        "latency_p95_ms": _percentile(latencies, 0.95),
    }
    for field in ("category", "urgency", "entities"):
        correct = sum(1 for s in scores if s[field])
        tally[field + "_correct"] = correct
        # Two figures, named rather than conflated. Over everything, a version is
        # punished for failing, which is the comparison's point. Over what
        # answered, a version that answered three times could look excellent.
        tally[field + "_accuracy_all"] = correct / total if total else None
        tally[field + "_accuracy_answered"] = correct / answered if answered else None
    return tally


def summarise(scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    families: Dict[str, List[Dict[str, Any]]] = {}
    for score in scores:
        families.setdefault(score["family"], []).append(score)
    return {
        "overall": _tally(scores),
        "by_family": {name: _tally(group) for name, group in sorted(families.items())},
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True)
    parser.add_argument("--dataset", default="data/golden.jsonl")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    def read(path: str) -> List[Dict[str, Any]]:
        text = pathlib.Path(path).read_text(encoding="utf-8")
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    summary = summarise(score_run(read(args.results), read(args.dataset)))
    rendered = json.dumps(summary, indent=2, ensure_ascii=False)
    if args.out:
        pathlib.Path(args.out).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
