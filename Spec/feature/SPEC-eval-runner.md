# Spec — SPEC-eval-runner · The minimal run harness

| Field | Value |
|---|---|
| **SPEC** | `SPEC-eval-runner` |
| **featureId** | `eval-runner` |
| **State** | 👀 `In review` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-09-07 |
| **Depends on** | `SPEC-v1-naive`, `SPEC-golden-dataset` |
| **Implementation directories** | `Python codebase` — adds `evals/` |
| **Integration base** | -- |
| **Spends budget** | `no` — building and verifying it uses stubs. Running it is a separate, human act |

---

## 1. Problem and goal

Nothing in this repository can run the dataset. The next question the project has
to answer — *does `v1` actually fail?* — cannot be asked without it, and six more
phases are currently resting on the assumption that it does.

This is the smallest thing that answers that question, and the comparison harness
of the final phase needs it anyway.

## 2. Scope

**Includes** — `evals/runner.py`: read the dataset, run **one** implementation
across some or all cases, and write one raw result per case, failures included.
A budget ceiling that stops the run cleanly.

**Excludes** — the comparative table, accuracy scoring, cost and latency metrics,
percentiles. All of that is the final phase, and mixing it in here would mean
building the reporting before knowing whether there is anything to report.

Also excluded: **running it**. That is a human act with a stated cost.

## 3. Domain and data model

Consumes `data/golden.jsonl` as defined in `SPEC-golden-dataset`. Introduces one
new record, written not read: a **run result** — what one implementation did with
one case.

**Schema change:** no changes.

## 4. API contract

N/A — see `ARCHITECTURE.md` section 6.

## 5. Implementation

`evals/runner.py`, invoked as a module:

```
python -m evals.runner --impl v1_naive --budget 0.20 --limit 10 --out results.jsonl
```

Five decisions, each with its reason:

- **`--budget` is required and has no default.** A run harness that can be started
  without saying what it may spend is the thing this project is about not
  building. Refusing to start is cheaper than any recovery.
- **Spend is counted from real usage after each call, and the run stops before the
  next one.** Estimating beforehand would need a token model that could itself be
  wrong; counting actuals cannot. The overshoot is bounded by one call, which is
  measured at roughly 0.004 USD.
- **A failing case is recorded and the run continues.** If one exception ended the
  run, a single bad case would hide the forty-three after it — and failures are
  the data being collected, not an interruption to it.
- **The runner adds no retry, no fallback and no validation of its own.** Any
  resilience here would be resilience the implementation does not have, and would
  mask exactly what is being measured. The runner observes; it does not help.
- **Implementations are registered explicitly**, as a name-to-callable mapping in
  the runner, not resolved by dynamic import. Adding the third variant is one
  line, and a typo fails immediately with a list of valid names.

Each result record carries: the case `id` and `family`, whether the call
succeeded, the raw text returned, the parsed result or `null`, the exception type
and **full traceback** when it failed, and the token usage for that call.

## 6. Second implementation directory

N/A — one directory.

## 7. Behaviour walkthrough

1. The runner refuses to start without `--budget` and a known `--impl`.
2. It loads the dataset, applies `--limit` if given, and for each case resolves
   `ticket` or reads `ticket_file`.
3. It calls the chosen implementation with that text.
4. Success or failure, it writes one result record and adds the call's usage to
   the running total.
5. When the total reaches the budget it stops, reports how many cases were left
   unrun, and exits without pretending the run was complete.
6. It prints a one-line summary: cases run, failures, total spend.

## 8. Acceptance criteria

- [x] Given a stub implementation and a dataset, one result record is written per
      case, in order.
- [x] Given an implementation that raises on a specific case, that case is
      recorded with its exception type and traceback, and the following cases
      still run.
- [x] Given a budget already exceeded by the accumulated usage, the run stops and
      the summary states how many cases were not run.
- [x] Started without `--budget`, the runner exits with an error and runs nothing.
- [x] Given an unknown `--impl`, it exits listing the valid names.
- [x] `--limit` runs exactly that many cases.
- [x] The runner issues no retry and alters no result it receives — verified by a
      stub that counts how many times it was called per case.
- [x] No test reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **Are run outputs committed?** Committing them makes the published numbers checkable by a reader, which is worth something in a repository offered as evidence. It also puts raw machine output in a repo whose value is that it can be read. **Proposed: `evals/results/` is git-ignored now; the final phase commits a small summary alongside the README table.** | **Open — decide at the approval gate** | Human |
| Where the budget cuts is still open for `v2`'s own budget element (before the call, by estimate, or after, by count). The runner answers it for itself only; that decision stays open for its own spec. | Open, scoped out | Human |
| A runner that stops mid-dataset produces a partial result file. Consumers must not mistake it for a complete run. Mitigation: the summary line states cases run against cases total, and the file is one record per case actually attempted — absence is visible. | Accepted, mitigated | -- |

## 10. References

- `data/golden.jsonl` (`SPEC-golden-dataset`) · `ARCHITECTURE.md` section 8.1 · `MASTER_PLAN.md` section 7.1

## 11. History

| Date | Change |
|---|---|
| 2026-09-07 | Drafted. Written after the smoke check measured a real call at 727 in / 70 out tokens, which is what makes the budget ceiling countable rather than estimated. |
| 2026-09-08 | Date corrected from 2026-09-04 to the real commit date. Third instance of the same defect: the date is written when drafting and the commit lands days later. From here it is read from the system clock at write time, not from memory. |
| 2026-09-08 | Approved by the human in conversation, including the proposal that run outputs stay git-ignored and the final phase commits a summary. Build started. |
| 2026-09-08 | Build found a defect that the criteria as written would not have caught: `run()` created its own recorder, so in real use the implementation reported usage to one object while the ceiling watched another, and no call would ever have counted against the budget. Fixed, with a regression test named after the failure. |
