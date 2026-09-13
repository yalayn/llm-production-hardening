# Spec — SPEC-readme-failures · "What breaks in v1 and why"

| Field | Value |
|---|---|
| **SPEC** | `SPEC-readme-failures` |
| **featureId** | `readme-failures` |
| **State** | 🔨 `In progress` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-09-13 |
| **Depends on** | `SPEC-run-fidelity` |
| **Implementation directories** | `Python codebase` — adds `README.md` |
| **Integration base** | -- |
| **Spends budget** | `no` — the runs already happened |

---

## 1. Problem and goal

Two baseline runs produced three distinct real failures. Their traces live in
`evals/results/`, which is git-ignored: **delete those two files and the evidence
is gone**, and reproducing it costs another 0.27 USD and depends on a provider
that may not behave identically next month.

This pulls one section of the final phase's README forward, for that reason
alone. It is the section a reader is most likely to believe, because it contains
error output rather than claims.

## 2. Scope

**Includes** — a `README.md` holding **only** the section *What breaks in v1 and
why*, with the three failures, their real traces and the figures from the runs.

**Excludes** — the comparative table, the intro, the structured-output section,
the contact paragraph. Those need `v2` to exist and belong to the final phase.
The file will be incomplete on purpose and must say so, so nobody reads a stub as
the finished argument.

## 3. Domain and data model

No change. The section reports observations; it defines nothing.

**Schema change:** no changes.

## 4. API contract

N/A — see `ARCHITECTURE.md` section 6.

## 5. Content

Three failures, each with the ticket that caused it, what the model actually
returned, and the resulting error, quoted verbatim from the run output.

**1 · The model wrapped the JSON in a code fence.** 45 of 48 replies arrived
inside ` ```json `. `json.loads` fails on the first character. This is the
baseline's defining failure and the one the hardened version addresses directly.

**2 · The code read the wrong block.** The first run, before a correction, took
`response.content[0]`, which on a model that reasons by default is a thinking
block. 43 of 50 cases died there. **It is reported as its own finding, not as a
weakness of the baseline**, because no element of the hardening repairs it — it is
what happens to correct code when a provider starts replying differently.

**3 · Empty input never reached the model.** Two cases returned HTTP 400 before
inference. **Both implementations have this failure**, and the section says so.

Each failure states **how often it happened**, because the intermittency is the
point: 45 of 48 and 43 of 50 both mean a developer testing once by hand has a
real chance of seeing it work.

**Honesty requirements, binding on the text:**
- The two prompt-injection cases the baseline got **right** are stated. They are
  two of only three passes, and hiding that would leave the strongest available
  objection unanswered.
- The section states that the accuracy comparison is **not** available from these
  runs: with 47 of 50 failing to parse, nothing reached the point of being scored.
- Every figure traces to a run recorded in the repository, with its date and
  model. No figure is rounded into a better one.

## 6. Second implementation directory

N/A.

## 7. How a reader meets it

Landing on the repository, they reach a file that is explicitly incomplete, whose
one section shows error output from real runs against a named model on a named
date. Nothing asks them to take a claim on faith.

## 8. Acceptance criteria

- [ ] `README.md` exists, in English, containing the section and a line stating
      the file is incomplete and what is still missing.
- [ ] All three failures appear, each with the ticket, the raw reply where one
      exists, and the verbatim error.
- [ ] Every figure in the section matches the run files — verified by a test that
      recomputes them from `evals/results/` when those files are present, and
      skips when they are not.
- [ ] The section states that the baseline answered the two prompt-injection
      cases correctly.
- [ ] The section states that accuracy could not be compared from these runs.
- [ ] The model and the run dates are named.
- [ ] No test reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **A test that recomputes the figures skips when `evals/results/` is absent** — which is the normal state of a fresh clone, since the directory is git-ignored. So the guard protects the author, not a reader. Making it unskippable would mean committing the raw runs. **Proposed: keep it skippable now; the final phase commits a small summary and the test binds to that instead.** | **Open — decide at the approval gate** | Human |
| A README that is one section may read as abandoned rather than in progress. Mitigation: the opening line says what is missing and why, in one sentence. | Accepted, mitigated | -- |
| The provider may stop wrapping replies in fences, making the headline failure unreproducible. That does not invalidate the finding — it is dated and attributed — but the text must not claim it is permanent. | Accepted | -- |

## 10. References

- `evals/results/v1-run1.jsonl`, `v1-run2.jsonl` (git-ignored) · `SPEC-run-fidelity` · `MASTER_PLAN.md`

## 11. History

| Date | Change |
|---|---|
| 2026-09-13 | Drafted. Pulled forward from the final phase because the evidence lives only in git-ignored files and costs 0.27 USD plus a stable provider to reproduce. |
| 2026-09-13 | Approved by the human in conversation. Build started. |
