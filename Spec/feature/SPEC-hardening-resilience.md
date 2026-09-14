# Spec — SPEC-hardening-resilience · Elements 4 to 6

| Field | Value |
|---|---|
| **SPEC** | `SPEC-hardening-resilience` |
| **featureId** | `hardening-resilience` |
| **State** | ✅ `Implemented` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-09-13 |
| **Depends on** | `SPEC-hardening-core` |
| **Implementation directories** | `Python codebase` |
| **Integration base** | -- |
| **Spends budget** | `no` |

---

## 1. Problem and goal

`SPEC-hardening-core` deliberately stops at an exception: attempts exhausted, or
the ceiling reached, and the caller gets a raise. That is not a production
answer.

This spec makes the hardened version survive: it stops paying for work it has
already done, it degrades instead of failing, and it says what happened on every
call.

## 2. Scope

**Includes** — element 4 (cache keyed on the input), element 5 (deterministic
fallback), element 6 (structured logging per call).

**Excludes** — the feature flag, which is the next spec. Persistence of any kind:
the cache lives in memory for the life of the process, because a database is out
of scope for this project and an in-memory cache demonstrates the idea without
one.

## 3. Domain and data model

`DOMAIN.md` already records that an extraction carries **whether the provider was
consulted**. This spec **widens that same distinction** rather than adding a
parallel one: the result now says which of four ways it was reached — answered,
served from cache, degraded, or skipped as empty input.

**Schema change:** no changes. The distinction stays a private attribute and
never reaches the schema sent to the provider.

## 4. API contract

N/A — see `ARCHITECTURE.md` section 6.

## 5. Implementation

### Element 4 · Cache keyed on the input

**The key covers everything that can change the answer** — the ticket text, the
system prompt, the model and the schema — not the ticket text alone. Keyed on the
text alone, editing the prompt would keep serving answers produced by the old
one, and nothing would say so. That failure is silent and survives a deploy,
which makes it worse than the cost it saves.

**Failures are not cached.** Caching one turns a transient provider problem into
a permanent wrong answer for that input, for the life of the process.

The golden dataset already contains the case that proves it works:
`edge-duplicate-of-billing` is byte-identical to `billing-duplicate-charge`, so a
complete run must make **49 calls, not 50**.

### Element 5 · Deterministic fallback

Catches what `hardening-core` raises and returns something usable, marked as
degraded, so the caller is never handed an exception from the language model.

**It must not hide a defect.** A provider failure degrades; a programming error —
a `TypeError`, a missing attribute, a broken import — is **not** caught and
propagates. A fallback wide enough to swallow bugs converts every future mistake
into a silent `unknown`, and the bug is never found. This is the single most
dangerous line in the spec, and the criteria pin it.

### Element 6 · Structured logging per call

One record per extraction: tokens, cost, latency, attempts made, and how it ended
— answered, degraded, served from cache, or skipped as empty. Machine-readable,
because the point is to be able to answer *"what did this cost us last week"*
without reading prose.

**It never logs the ticket text**, and it never logs credentials. A support
ticket is customer writing and belongs in the support system, not in the
application logs of an extraction service.

## 6. Second implementation directory

N/A — one directory.

## 7. Behaviour walkthrough

1. The key is computed from the input and everything else that shapes the answer.
2. A hit returns the stored result immediately, marked as served from cache, with
   no call and no cost.
3. A miss runs the `hardening-core` path: guard, call, validate, retry, ceiling.
4. Success stores the result under the key and returns it.
5. A provider failure returns the degraded result instead of raising. A
   programming error propagates untouched.
6. Either way, one log record is written describing what happened.

## 8. Acceptance criteria

- [x] The same input twice produces one call and two identical results; the second
      is marked as served from cache.
- [x] Changing the system prompt changes the key: the same ticket calls again
      rather than serving the previous answer.
- [x] A failed extraction is not cached: the next identical input calls again.
- [x] When the provider never yields a valid reply, a degraded result is returned
      rather than an exception, and it is marked degraded.
- [x] A programming error raised inside the extraction **propagates** and is not
      turned into a degraded result.
- [x] Every extraction writes exactly one log record carrying tokens, cost,
      latency, attempts and outcome.
- [x] No log record contains the ticket text or any credential — verified by a
      test that feeds a recognisable string and asserts its absence.
- [x] The naive version is unchanged.
- [x] No test reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **What does the degraded result contain?** (a) the full schema with `unknown` in both closed fields — the caller's code needs no special case, and `unknown` already means "not enough to decide", which is true; (b) a smaller, distinct object — impossible to mistake for a real answer, but every caller must now handle two shapes. **Proposed: (a), with the marker as the thing that distinguishes it.** | **Open — decide at the approval gate** | Human |
| **Does the log carry the ticket text?** Omitting it is the right production default and what section 5 requires. But a repository teaching people to debug LLM integrations might reasonably show how to log a redacted or hashed form, since "log nothing" makes a bad day much harder. **Proposed: log a hash of the input — enough to correlate two records, useless for reading the customer's words.** | **Open — decide at the approval gate** | Human |
| An in-memory cache means the duplicate case only demonstrates a hit **within one run**. That is honest for the comparison and worth stating in the results, rather than implying a cache that survives a restart. | Accepted, must be stated | -- |
| The fallback boundary is judgement, not a rule the code can enforce: "provider failure" and "programming error" are distinguished by exception type, and a new failure mode could land on the wrong side. Mitigation: the default is to **propagate**, so an unclassified failure is loud rather than silent. | Accepted, mitigated | -- |

## 10. References

- `SPEC-hardening-core` (what raises) · `DOMAIN.md` (the unconsulted distinction) · `data/golden.jsonl` (`edge-duplicate-of-billing`) · `ARCHITECTURE.md` section 4

## 11. History

| Date | Change |
|---|---|
| 2026-09-13 | Drafted. The cache key covers the prompt and model, not just the ticket, because a key that ignores them serves stale answers silently after an edit. The fallback is explicitly barred from catching programming errors. |
| 2026-09-13 | Approved by the human, including both open decisions: the degraded result carries the full schema with `unknown`, and the log carries a hash of the input rather than its text. |
| 2026-09-13 | Built. Section 3 said "three ways" against four in section 5; corrected to four. The marker was widened rather than duplicated, as recorded when the previous spec closed. |
| 2026-09-13 | Criteria approved by the human. Closed as `Implemented`. |
