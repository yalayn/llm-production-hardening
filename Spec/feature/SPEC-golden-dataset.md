# Spec — SPEC-golden-dataset · The 50-case golden dataset

| Field | Value |
|---|---|
| **SPEC** | `SPEC-golden-dataset` |
| **featureId** | `golden-dataset` |
| **State** | ✅ `Implemented` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-09-01 |
| **Depends on** | `SPEC-v1-naive` |
| **Implementation directories** | `Python codebase` — adds `data/`, and a test |
| **Integration base** | -- |
| **Spends budget** | `no` — writing the dataset spends nothing; running against it is a later spec |

---

## 1. Problem and goal

The twenty edge cases are the heart of the repository: they are what `v1` fails
and `v2` does not. Without them the comparison has thirty rows of two
implementations agreeing with each other.

They are written **now**, with `v1` done and `v2` not started, so the cases are
specified against the *problem* rather than against a solution that already knows
how to pass them.

## 2. Scope

**Includes** — `data/golden.jsonl` (50 records), the long-ticket fixture it
references, and a test suite that validates the dataset's own integrity.

**Excludes** — the eval harness, any scoring code, and running anything against a
provider. Those are later specs.

## 3. Domain and data model

Expected answers use the closed sets already declared in `DOMAIN.md`. The dataset
introduces no new domain concepts; it is evidence about the existing one.

**Schema change:** no changes.

## 4. API contract

N/A — see `ARCHITECTURE.md` section 6.

## 5. Record shape

One JSON object per line:

```json
{
  "id": "billing-duplicate-charge",
  "family": "normal",
  "ticket": "You charged me twice for invoice INV-4471.",
  "expected": { "category": "billing", "urgency": "high", "entities": ["INV-4471"] },
  "notes": "why this is the right answer, for a human reviewing the dataset"
}
```

Four decisions, each with its reason:

- **`suggested_action` is recorded by the runner but never scored.** It is free
  text; exact matching is meaningless and an LLM judge would add cost, latency and
  a dependency for the least decisive of the four fields.
- **`category` and `urgency` are matched exactly; `entities` as a
  case-insensitive set.** Order of entities carries no meaning.
- **The 10,000-word ticket lives in its own file**, referenced by `ticket_file`
  instead of `ticket`. Inline it would be roughly 60 KB on one line and would make
  the dataset unreviewable — and a dataset nobody can read is not evidence.
- **The duplicate case carries `duplicate_of`** naming the record it copies, and
  its ticket text must be byte-identical. That identity is what the cache is
  measured against, so a test enforces it rather than trusting a copy-paste.

## 6. Second implementation directory

N/A — one directory.

## 7. How a record is consumed

1. The runner reads a line, taking `ticket` or loading `ticket_file`.
2. It calls one implementation with that text.
3. It compares the result against `expected`, field by field, under the rules in
   section 5.
4. `family` groups the results, so the output table can show where each
   implementation actually breaks rather than one aggregate score.

## 8. Acceptance criteria

- [x] `data/golden.jsonl` holds exactly 50 records: 30 with `family: normal`, 20
      edge cases.
- [x] All nine edge families are present: empty, two-word, non-target language,
      10,000-word, genuinely ambiguous, prompt injection, non-existent category,
      control characters and pasted HTML, exact duplicate.
- [x] Every record parses, carries every required field, and holds exactly one of
      `ticket` or `ticket_file` — verified by a test.
- [x] Every `expected.category` and `expected.urgency` is a member of the closed
      sets in `DOMAIN.md` — verified by a test, so a typo cannot silently create an
      unpassable case.
- [x] The duplicate record's ticket is byte-identical to the record it names in
      `duplicate_of` — verified by a test.
- [x] The long-ticket fixture is at least 10,000 words — verified by a test.
- [x] No record and no test references `v1_naive` or `v2_hardened`; the dataset
      describes the problem, not either answer — verified by a test.
- [x] No test reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **Who owns the ground truth?** The agent can draft 50 tickets and 50 expected answers, but if the agent also decides what is correct, the dataset measures agreement with the agent — not correctness. That is a circularity the repository cannot afford, since the results table is its whole product. **Proposed: the agent drafts; the human reviews all 50 and adjudicates the ambiguous ones case by case at the approval gate.** Roughly 15 minutes of reading. | **Open — decide at the approval gate** | Human |
| The genuinely ambiguous cases need a defensible answer, not just `unknown`. `unknown` is correct when the ticket *does not say enough*; a ticket that is merely hard is not ambiguous. The `notes` field on each such record must survive the question "why is this one unknowable?" | Open | Human |
| The 10,000-word case costs more input tokens than the other 49 combined (roughly 13,000 against 6,000). In absolute terms that is a few cents per run. Proposed: keep it — context-length behaviour is a real production failure and it is the only case that exercises it. | Proposed, confirm | Human |
| Thirty "normal" cases risk being thirty variations of the same easy ticket. Mitigation: they spread across all five real categories and all four urgencies, and no two share a category-urgency pair without differing in structure. | Accepted, mitigated | -- |

## 10. References

- `DOMAIN.md` (closed sets) · `ARCHITECTURE.md` · `MASTER_PLAN.md`

## 11. History

| Date | Change |
|---|---|
| 2026-09-01 | Drafted. The load-bearing open question is who owns the ground truth: if the agent both writes the cases and decides the right answers, the results table measures agreement with the agent. |
| 2026-09-03 | Approved by the human in conversation, including the split of ground truth: the agent drafts, the human adjudicates at the criteria gate. Build started. |
| 2026-09-03 | Criteria approved by the human, including the twenty edge-case answers. Closed as `Implemented`. |
| 2026-09-04 | **Dates corrected.** Same defect as in `SPEC-v1-naive`: rows read 2026-08-20 against real dates of 2026-09-01 and 2026-09-03. |
