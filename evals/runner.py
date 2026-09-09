"""Run one implementation across the golden dataset and record what happened.

This harness observes; it does not help. It adds no retry, no fallback and no
validation of its own, because any resilience here would be resilience the
implementation under test does not have -- and would hide exactly what is being
measured.
"""

import argparse
import json
import pathlib
import sys
import traceback
from typing import Any, Callable, Dict, List, Optional

from v1_naive.extractor import extract_ticket as _v1_extract
from v2_hardened.client import AnthropicClient
from v2_hardened.extractor import extract_ticket as _v2_extract

DATA = pathlib.Path(__file__).parent.parent / "data"

# USD per million tokens, by model. Read from the response rather than assumed,
# so a change of model cannot silently mis-price a run.
PRICING = {"claude-sonnet-5": (3.0, 15.0)}


class UsageRecorder:
    """Stands in for the SDK client and remembers the usage of every response.

    Both implementations take an injected client, so the same recorder serves
    both: the naive one receives it directly, the hardened one receives it
    wrapped. Neither is modified, and neither knows it is being measured.
    """

    def __init__(self, api: Any = None) -> None:
        self._api = api
        self.calls: List[Dict[str, Any]] = []
        self.messages = _RecordingMessages(self)

    def record(self, model: str, input_tokens: int, output_tokens: int) -> None:
        self.calls.append(
            {"model": model, "input_tokens": input_tokens, "output_tokens": output_tokens}
        )

    def spend(self) -> float:
        total = 0.0
        for call in self.calls:
            per_in, per_out = PRICING.get(call["model"], (0.0, 0.0))
            total += call["input_tokens"] / 1e6 * per_in
            total += call["output_tokens"] / 1e6 * per_out
        return total


class _RecordingMessages:
    def __init__(self, recorder: UsageRecorder) -> None:
        self._recorder = recorder

    def create(self, **kwargs: Any) -> Any:
        response = self._recorder._api.messages.create(**kwargs)
        usage = response.usage
        self._recorder.record(response.model, usage.input_tokens, usage.output_tokens)
        return response


def _run_v1(text: str, recorder: UsageRecorder) -> Any:
    return _v1_extract(text, recorder)


def _run_v2(text: str, recorder: UsageRecorder) -> Any:
    return _v2_extract(text, AnthropicClient(api=recorder))


IMPLEMENTATIONS: Dict[str, Callable[[str, UsageRecorder], Any]] = {
    "v1_naive": _run_v1,
    "v2_hardened": _run_v2,
}


def load_cases(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    path = DATA / "golden.jsonl"
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return cases[:limit] if limit else cases


def ticket_text(case: Dict[str, Any]) -> str:
    if "ticket_file" in case:
        return (DATA / case["ticket_file"]).read_text(encoding="utf-8")
    return case["ticket"]


def run(implementation, cases, out_path, budget: float, recorder=None) -> Dict[str, Any]:
    """Run `implementation` over `cases`, writing one record each, until `budget`.

    The recorder is passed in, not created here: the budget can only be enforced
    against the same object the implementation actually reports usage to.
    """
    recorder = recorder if recorder is not None else UsageRecorder()
    ran = 0
    failures = 0
    stopped = False

    with pathlib.Path(out_path).open("w", encoding="utf-8") as handle:
        for case in cases:
            if recorder.spend() >= budget:
                stopped = True
                break

            before = len(recorder.calls)
            record: Dict[str, Any] = {"id": case["id"], "family": case["family"]}
            try:
                result = implementation(ticket_text(case), recorder)
                record["ok"] = True
                record["result"] = result.model_dump() if hasattr(result, "model_dump") else result
                record["error"] = None
            except Exception as exc:
                record["ok"] = False
                record["result"] = None
                record["error"] = {"type": type(exc).__name__, "traceback": traceback.format_exc()}
                failures += 1

            record["usage"] = recorder.calls[before:]
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            ran += 1

    return {
        "ran": ran,
        "total": len(cases),
        "not_run": len(cases) - ran,
        "failures": failures,
        "spend": round(recorder.spend(), 5),
        "stopped_on_budget": stopped,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--impl", required=True)
    # No default: a harness that can start without saying what it may spend is
    # the thing this project exists not to build.
    parser.add_argument("--budget", type=float, required=True, help="hard ceiling in USD")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", default="evals/results/run.jsonl")
    args = parser.parse_args(argv)

    if args.impl not in IMPLEMENTATIONS:
        parser.error("unknown --impl {!r}; valid names are: {}".format(
            args.impl, ", ".join(sorted(IMPLEMENTATIONS))))

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    import anthropic

    recorder = UsageRecorder(anthropic.Anthropic())
    implementation = IMPLEMENTATIONS[args.impl]
    summary = run(implementation, load_cases(args.limit), out, args.budget, recorder)

    print("ran {ran}/{total} · {failures} failed · spend USD {spend}{stopped}".format(
        stopped=" · STOPPED ON BUDGET" if summary["stopped_on_budget"] else "", **summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
