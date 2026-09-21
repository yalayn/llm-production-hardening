# Spec — SPEC-eval-fidelity · Measure the elements the table credits

| Field | Value |
|---|---|
| **SPEC** | `SPEC-eval-fidelity` |
| **featureId** | `eval-fidelity` |
| **State** | 👀 `In review` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-09-19 |
| **Depends on** | `SPEC-eval-runner`, `SPEC-eval-scoring`, `SPEC-v1-structured`, `SPEC-hardening-resilience` |
| **Implementation directories** | `Python codebase` |
| **Integration base** | -- |
| **Spends budget** | `no` to build. One diagnostic run afterwards costs about 0.17 USD and one re-run of `v2_hardened` about 0.21 USD. Both are human acts |

---

## 1. Problem and goal

The three final runs are scored. Two of the numbers in the resulting table do not
mean what the table would be read to say, and a third piece of the evidence is
not in the repository at all.

**The cache is measured at zero, and not because it does not work.** The golden
dataset carries `edge-duplicate-of-billing`, byte-identical to
`billing-duplicate-charge` and declared as such with a `duplicate_of` field. It
exists to exercise element 4. `evals/runner.py` never passes a cache to
`v2_hardened`, so the run paid for that ticket twice. The element the dataset was
built to demonstrate is the one element the harness cannot see — the same species
of defect as the budget that watched the wrong recorder.

**The largest gain in the table is not attributable to hardening.** Entities go
from 18 of 50 in `v1_structured` to 38 of 50 in `v2_hardened`. The cause is not
among the seven elements: `v1_structured` sends `{"type": "array", "items":
{"type": "string"}}` and `v2_hardened` sends the same array with a `description`
saying what an entity is. `v2_hardened` treats its schema as part of the prompt,
and its system prompt differs too. As the table stands, a reader is invited to
credit resilience for what better instructions bought — and the first reader who
opens both files will say so.

**The evidence lives only on the author's machine.** `evals/results/` is
git-ignored, so the README will cite failure counts and real traces that no reader
can recompute, and `tests/test_readme_figures.py` skips entirely on a fresh clone.
`SPEC-run-fidelity` section 9 already recorded this as an accepted risk for the
first baseline; the final runs are the ones the repository's claims rest on, and
accepting it twice would be a decision made by inertia.

**Goal:** every figure the comparative table carries is a figure the harness
actually measured, attributed to the thing that caused it, and recomputable by a
reader who has only cloned the repository.

## 2. Scope

**Includes**
- The runner gives `v2_hardened` a cache whose lifetime is the run.
- A diagnostic implementation, `v1_structured_described`, that isolates the
  prompt surface from the seven elements.
- The three `final-*.jsonl` runs stop being git-ignored and are committed.

**Excludes**
- Any change to `v1_naive`, `v1_structured` or `v2_hardened`. This spec changes
  the instrument, never the things being measured.
- Separating the schema descriptions from the system prompt. One diagnostic
  measures the prompt surface as a whole; splitting it costs a second run and
  answers a question the README does not ask — see section 9.
- Scoring changes. `evals/scoring.py` already handles a fourth run file with no
  modification, and `cached` is already excluded from `NON_ANSWERS` correctly:
  a cached answer is a real answer.
- The README itself. That is the final phase.

## 3. Domain and data model

No change to the domain. `.gitignore` narrows from `evals/results/` to the
generated and exploratory runs, so that `evals/results/final-*.jsonl` is tracked.

**Schema change:** no changes.

## 4. API contract

N/A — see `ARCHITECTURE.md` section 6.

## 5. Implementation

### 5.1 The cache's lifetime is the run

`IMPLEMENTATIONS` maps a name to a **factory** called once per run, which returns
the per-case callable. The `v2_hardened` factory builds one `InMemoryCache` and
closes over it; the two `v1` factories return their function unchanged, because
neither has a cache to give.

A factory rather than a module-level cache: module-level state survives between
runs in the same process, which would make a second run in the test suite start
warm and would let one test's entries reach another's. The lifetime of a cache
is a decision, and here the decision is *one run*.

This is the honest lifetime to measure. A real deployment would hold the cache
across requests and hit it far more often than once in fifty; a cache scoped to
one run is the **floor** of what the element is worth, not a demonstration of it.
Section 9 records that the resulting figure is a floor and why the README must
say so.

### 5.2 The diagnostic isolates the prompt surface

`evals/diagnostic.py` holds one implementation, registered as
`v1_structured_described`. It is `v1_structured`'s code path exactly — one
`messages.create`, `json.loads`, returned unchecked, nothing validated, nothing
retried — sending `v2_hardened`'s schema and `v2_hardened`'s system prompt.

**It imports those two from `v2_hardened` instead of copying them, and that
inverts the rule the three implementations follow.** `ARCHITECTURE.md` section 0
requires the implementations to state their vocabulary independently, so that the
day two disagree the eval reports it. The diagnostic's entire purpose is the
opposite: to be *identical* to `v2_hardened` in the prompt dimension. A copy could
drift, and a drifted copy would silently stop being a control while still
producing a number. Here, importing is what makes the measurement valid.

It lives in `evals/`, not at the repository root, because it is an instrument and
not a fourth thing the repository recommends. `ARCHITECTURE.md` section 0 keeps
three columns.

**What the control is worth.** `v2_hardened` sends `model`, `max_tokens=1024`,
`system`, `messages` and `output_config`, plus a `timeout` the provider does not
see in the payload. The diagnostic sends the same five. So the diagnostic's
request is byte-identical to the hardened version's, and the difference between
their scores is the seven elements and nothing else. A test asserts that
equality rather than leaving it to inspection.

### 5.3 The evidence is committed

`.gitignore` stops ignoring `evals/results/final-*.jsonl`. The three final runs
and the diagnostic run are committed — about 224 KB of JSON lines carrying, for
every case, the raw text the model returned.

This is what lets `tests/test_readme_figures.py` stop skipping, and it is what
separates a repository that reports numbers from one that shows them. The
exploratory runs (`v1-run1`, `v1-run2`, `smoke-*`) stay ignored: they are the
author's working notes, except where the README quotes a trace from them, and
those quotations are already guarded by tests.

## 6. Second implementation directory

N/A — one directory.

## 7. Behaviour walkthrough

1. The runner is invoked with `--impl v2_hardened`. The factory runs once and
   builds an empty cache.
2. Case 1, `billing-duplicate-charge`, misses the cache, costs a call, and is
   stored under a key covering ticket, prompt, model and schema.
3. Cases 2 to 49 miss, as they must: the tickets differ.
4. Case 50, `edge-duplicate-of-billing`, hits. No call is made, the record
   carries `outcome: "cached"`, and the run's spend is one call lower than the
   run that produced the current table.
5. Scoring reads that record as an answer — which it is — and the run is
   comparable to the ones before it.
6. The runner is invoked with `--impl v1_structured_described`. It sends what
   `v2_hardened` sends and does nothing else that `v2_hardened` does.

## 8. Acceptance criteria

- [x] Given a run over the golden dataset, `v2_hardened` produces exactly one
      record whose `outcome` is `cached`, and it is `edge-duplicate-of-billing`.
- [x] That record carries no usage: the cache hit cost nothing.
- [x] Two consecutive runs in the same process do not share a cache — the second
      run's first case is a miss.
- [x] `v1_naive` and `v1_structured` are unchanged: their factories return the
      same function, and no cache reaches them.
- [x] For the same ticket, the request `v1_structured_described` sends and the
      request `v2_hardened` sends are equal on `model`, `max_tokens`, `system`,
      `messages` and `output_config`.
- [x] `v1_structured_described` validates nothing, retries nothing and degrades
      nothing: given a reply that satisfies no schema it raises, exactly as
      `v1_structured` does.
- [x] `git check-ignore evals/results/final-v2-hardened.jsonl` reports it is not
      ignored, and so do the two baseline runs the README quotes. The working
      notes -- smoke tests and ad-hoc output -- are still ignored.
- [x] `tests/test_readme_figures.py` no longer skips on a clean checkout.
- [x] No test reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **The cache figure is a floor, not a result.** One hit in fifty is what a cache scoped to a single run of a deduplicated dataset can show. Under real traffic the same element is worth far more, and this eval cannot demonstrate that. **The README must state the figure as a floor and say what it does not measure** — the alternative, letting "1 of 50" stand unqualified, understates the element as badly as crediting it with the entity gain overstates another. | Accepted, to be written in the final phase | -- |
| **The diagnostic does not separate the schema descriptions from the system prompt.** Chosen deliberately: the question the README asks is how much of the hardened version's advantage belongs to the seven elements, and the diagnostic answers it exactly. The finer split would cost a second run and is recorded here as a question this repository chose not to buy. | Decided by the human, 2026-09-19 | -- |
| **A possible outcome is that the residual is near zero** — that the described schema and the better prompt account for most of the quality gap, and the seven elements buy reliability rather than accuracy. That would be the most valuable finding in the repository and the most uncomfortable to publish. It must be reported as measured, not re-framed. | Accepted in advance | Human |
| Committing the run files freezes a model's behaviour on a date into the repository. Sonnet 5 will change and the figures will age. Mitigation: each committed run is dated and names its model, and the README says when it was measured. | Accepted, mitigated | -- |
| The current table in hand was produced **without** the cache. Publishing it and the post-cache run side by side would be confusing; the re-run replaces it. The superseded numbers stay in this document's section 11, not in the README. | Decided | -- |

## 10. References

- `ARCHITECTURE.md` section 0 (the deliberate divergence, and why the diagnostic inverts it) · `SPEC-run-fidelity` (the same class of defect, found the same way) · `SPEC-eval-runner` section 5 · `MASTER_PLAN.md` section 7.1 (the spending gate)

## 11. History

| Date | Change |
|---|---|
| 2026-09-19 | Drafted after scoring the three final runs. Superseded figures, measured without a cache: `v1_naive` 46 of 50 failed, category 8 %, entities 6 %, 2.70 USD per 1,000; `v1_structured` 2 failed, category 90 %, entities 36 %, 3.48 USD per 1,000; `v2_hardened` 0 failed, category 96 %, entities 76 %, 4.15 USD per 1,000. Median input tokens 203 / 455 / 730. |
| 2026-09-20 | Approved by the human, with both forks decided: the diagnostic controls for the whole prompt surface, and the final runs are committed as evidence. Build started. |
| 2026-09-21 | Built. Six mutations, each red for its own reason: removing the cache, sharing it between runs, sending the bare schema, sending the naive prompt, validating in the diagnostic, and re-ignoring the runs. |
| 2026-09-21 | **Section 5.3 was wrong and was corrected mid-build.** It un-ignored only `final-*.jsonl`, so `tests/test_readme_figures.py` still had nothing to read and went on skipping — the criterion could not be met by the rule written to meet it. Both baseline runs the README quotes are now tracked, and the criterion was verified on a real clone of the branch rather than on the working tree. |
| 2026-09-21 | **Process note:** a mutation was restored with `git checkout` on a file whose changes had never been committed, which discarded the runner's implementation. Re-applied, and the remaining mutations were run only after committing. |
| 2026-09-21 | Criteria met, suite green at 128. Awaiting human approval. |
