# Spec — SPEC-eval-scoring · Judging a run

| Field | Value |
|---|---|
| **SPEC** | `SPEC-eval-scoring` |
| **featureId** | `eval-scoring` |
| **State** | 👀 `In review` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-09-16 |
| **Depends on** | `SPEC-eval-runner`, `SPEC-golden-dataset` |
| **Implementation directories** | `Python codebase` |
| **Integration base** | -- |
| **Spends budget** | `no` — it reads runs that already happened |

---

## 1. Problem and goal

The harness records what each implementation did. Nothing yet says whether it was
**right**, and the comparative table is made entirely of that judgement.

The runner also does not record how long a call took, and the table asks for
p50 and p95.

## 2. Scope

**Includes** — scoring a results file against the dataset, grouped by family; and
per-case latency in the runner, which is two lines and belongs with the thing
that needs it.

**Excludes** — the third variant, the table's prose, the README. Scoring is what
makes those possible; it is not those.

## 3. Domain and data model

No new domain concepts. Two derived records, neither persisted: a **case score**
(was each scored field right) and a **run summary** (the same, aggregated by
family and overall).

**Schema change:** no changes.

## 4. API contract

N/A — see `ARCHITECTURE.md` section 6.

## 5. Implementation

**A separate step, not part of the runner.** Judging is not executing, and the
separation buys something concrete: a run can be **re-scored without re-running**.
Re-running costs money and, against a provider, does not reproduce. If scoring
lived inside the runner, every change to how a field is judged would cost another
0.17 USD and produce different answers to compare against.

**How each field is judged** — the rules are `SPEC-golden-dataset` section 5, and
this spec implements rather than restates them: `category` and `urgency` exact,
`entities` as a case-insensitive set, `suggested_action` recorded and never
scored.

**Entities match as a whole set, with no partial credit.** Precision and recall
per case would be defensible and would also invite an argument about weighting in
a repository whose value is that its numbers cannot be argued with.

### The trap this spec exists to avoid

A degraded result carries `unknown` in both closed fields. Four dataset cases
expect exactly that. Scored naively, **a hardened version that failed completely
would score correct on them** — and the headline number would reward breaking.

So: `answered`, `cached` and `empty_input` are scored against the expected
answer. `degraded` and `disabled` are **never counted correct**, whatever they
contain, and are reported in their own column.

`empty_input` is scored normally on purpose: that answer is reached deliberately,
not by defaulting, and it is the one the dataset declares right.

The naive implementation has no outcome marker; a result it produced is scored,
an exception is a failure. That asymmetry is real and is reported rather than
smoothed away.

## 6. Second implementation directory

N/A — one directory.

## 7. Behaviour walkthrough

1. The scorer reads a results file and the dataset, and pairs them by case id.
2. Each pair yields a case score: right or wrong per scored field, or "no answer".
3. Scores aggregate by family and overall: correct per field, no-answer count,
   uncontrolled failures, total cost, and latency percentiles.
4. The summary is written as JSON, so the README's figures can be recomputed from
   a file rather than transcribed by hand.

## 8. Acceptance criteria

- [x] Given a results file and the dataset, one case score per result, paired by id.
- [x] A result whose id is not in the dataset is reported as an error, not ignored.
- [x] `category` and `urgency` score on exact match; `entities` on set equality
      ignoring case and order; `suggested_action` is never scored.
- [x] A `degraded` result matching the expected answer is **not** counted correct.
- [x] An `empty_input` result matching the expected answer **is** counted correct.
- [x] A result with no outcome marker — the naive implementation — is scored on
      its values.
- [x] The summary reports per family and overall, and includes p50 and p95 latency.
- [x] The runner records per-case latency.
- [x] Scoring makes no provider call, and no test reaches the network.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **Is the headline accuracy figure over all 50 cases, or over the ones that produced an answer?** (a) all 50 — a version that fails is punished for failing, which is the comparison's whole point; (b) answered-only — measures classification quality separately from reliability, and is the fairer number if someone asks "how good is the model". **Proposed: report (a) as the headline and (b) beside it, named clearly.** Reporting only (b) would let a version that answered three times look excellent. | **Open — decide at the approval gate** | Human |
| Latency measured around a call includes the retries and the SDK's own backoff, so the hardened version's p95 will be worse than the baseline's by construction. That is a true and uncomfortable result. It must appear rather than be normalised away, and the README should say what it means. | Accepted, must be stated | -- |
| Scoring `unknown` as an answer at all is a judgement: four ambiguous cases declare it correct, so a version that always answered `unknown` would score 8% and look worse than it is — or better, if the reader forgets. The per-family breakdown is what keeps this readable. | Accepted, mitigated by grouping | -- |

## 10. References

- `SPEC-golden-dataset` section 5 (the judging rules) · `SPEC-eval-runner` · `DOMAIN.md` (the five outcomes)

## 11. History

| Date | Change |
|---|---|
| 2026-09-16 | Drafted. The load-bearing rule is that a degraded result is never counted correct: four cases expect `unknown`, so naive scoring would reward a hardened version for failing completely. |
| 2026-09-16 | Approved by the human, including the open decision: both accuracy figures are reported, the one over all cases as the headline. |
| 2026-09-16 | Built. The audit found that the outcome marker does not survive `model_dump()`, so the runner was losing it and the central rule of this spec could not have been applied. The runner now records it alongside latency. |
| 2026-09-16 | A mutation exposed a weak test rather than weak code: "no partial credit" only covered the empty set, where exact and partial matching agree. Two cases added for a strict subset and for an invented extra. |
