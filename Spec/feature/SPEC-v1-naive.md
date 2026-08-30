# Spec — SPEC-v1-naive · The naive extraction implementation

| Field | Value |
|---|---|
| **SPEC** | `SPEC-v1-naive` |
| **featureId** | `v1-naive` |
| **State** | 📝 `Draft` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-08-20 |
| **Depends on** | -- |
| **Implementation directories** | `Python codebase` — adds `v1_naive/` |
| **Integration base** | -- |
| **Spends budget** | `no` — every test runs against a stub |

---

## 1. Problem and goal

This repository's product is a **comparison**, and a comparison needs a baseline
that a competent engineer recognises as their own work. If a reader can say
*"nobody writes it like that"*, every number in the results table is worthless.

So the goal is narrow and unusual: write the version **without** the safety net,
and write it **well**.

## 2. Scope

**Includes** — `v1_naive/extractor.py`: one module, one public function, a prompt
that carries the JSON shape in prose, a direct provider call, `json.loads()`, and
tests that pin the behaviour including how it fails.

**Excludes** — schema validation, retries, timeout, budget, cache, fallback,
structured logging, feature flag: their absence *is* the feature. Any import from
`v2_hardened`. And making it fail on purpose: every weakness must be one a real
developer would plausibly ship.

## 3. Domain and data model

Targets the same shape as `DOMAIN.md` but **does not import `TicketExtraction`**.
It describes the shape in prose in its prompt and returns whatever `json.loads()`
produces — a plain `dict`, unchecked. Two implementations aiming at one shape, one
of which can prove it hit it.

**Schema change:** no changes.

## 4. API contract

N/A — see `ARCHITECTURE.md` section 6.

## 5. Implementation

Governed by `ARCHITECTURE.md`; section 0 records this module's canon and section
4.4 its seam. Three decisions, each with its reason:

- **The prompt carries the schema in prose.** A JSON example in the system prompt,
  the way you write it when you want to be done in ten minutes.
- **The client is a parameter with a real default** (`client=None` builds one).
  A hurried developer does not build a Protocol, but very often writes exactly this
  idiom — it is the shortest path to something testable. It keeps `v1` honest while
  letting the eval harness drive it offline. That a test must then fake the SDK
  object's shape rather than a clean interface is **part of what is being
  measured**, not a flaw to fix.
- **`json.loads()`, returned as-is.** No validation, no repair, no catch.

## 6. Second implementation directory

N/A — one directory.

## 7. Behaviour walkthrough

1. Caller passes ticket text to `extract_ticket`.
2. A system prompt describing the target JSON is combined with the ticket.
3. One request. No timeout or retry policy beyond the SDK defaults.
4. The response text goes to `json.loads()`.
5. The `dict` is returned, unexamined.

**Failure modes, all deliberately unhandled** — and the reason this module exists:

| The model... | What happens |
|---|---|
| wraps JSON in prose | `JSONDecodeError` propagates |
| returns a category that does not exist | no error at all; the caller receives it |
| omits a field | `KeyError` later, far from here |
| errors or times out | the exception propagates |

## 8. Acceptance criteria

- [ ] Given a stub returning well-formed JSON, a `dict` with the four expected
      keys is returned.
- [ ] Given a stub returning JSON wrapped in prose, `json.JSONDecodeError`
      propagates — pinned by a test, because that failure is a documented result of
      this version, not an accident.
- [ ] Given valid JSON with a category outside the known set, the value is
      returned unchanged and nothing is raised.
- [ ] `v1_naive` imports nothing from `v2_hardened` — verified by a test, not by
      inspection.
- [ ] `extract_ticket` is callable with a single argument, using a real client by
      default.
- [ ] No test reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **Does `v1` use the provider's native structured output?** `output_config.format` is on the first page of the documentation, so a competent developer in a hurry might well reach for it. If `v1` uses it, it stops being naive in the dimension that matters most. If it does not, a reader may object that the baseline was weakened deliberately. **Proposed: prompt-based JSON and `json.loads()` — what dominates real code in the wild — with the README stating the choice and its reasoning outright** rather than leaving it to be discovered. | **Open — decide at the approval gate** | Human |
| How is "well written" verified? The one criterion that resists being binary. Proposed check: *"would a good developer sign this on a Friday afternoon?"*, with a "no" treated as blocking. | Open | Human |
| A future change may "improve" `v1` and silently end the comparison. Mitigated: `ARCHITECTURE.md` section 0 records the divergence as canon, and the no-import rule is enforced by a test. | Accepted, mitigated | -- |

## 10. References

- `ARCHITECTURE.md` (binding) · `DOMAIN.md` · `MASTER_PLAN.md`
- Method: `methodology/principles.md`

## 11. History

| Date | Change |
|---|---|
| 2026-08-20 | Drafted. Two decisions left open for the approval gate: whether `v1` may use native structured output, and how "well written" is verified. |
| 2026-08-20 | Rewritten shorter under the new `MASTER_PLAN` rule 9 (proportion). A third open decision — how a new directory acquires an architecture document — was dropped: rescoping to a single `ARCHITECTURE.md` removed the gap instead of working around it. |
