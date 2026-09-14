# Spec — SPEC-hardening-core · Elements 1 to 3

| Field | Value |
|---|---|
| **SPEC** | `SPEC-hardening-core` |
| **featureId** | `hardening-core` |
| **State** | 👀 `In review` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-09-13 |
| **Depends on** | `SPEC-run-fidelity` |
| **Implementation directories** | `Python codebase` |
| **Integration base** | -- |
| **Spends budget** | `no` to build. Comparing it against the baseline later costs about 0.17 USD and is a human act |

---

## 1. Problem and goal

The baseline produced no usable result in 47 of 50 cases. This is the first of
three specs that make the hardened version worth comparing it against.

Three elements: validated structured output, retry on validation failure, and a
timeout with a cost ceiling per request.

## 2. Scope

**Includes**
- **Element 1** already exists from the bootstrap vertical — the schema is sent
  and the reply validated. This spec **formalises** it: the criteria pin the
  behaviour, and the reasoning about what it bounds is written down.
- **Element 2** — retry when the reply fails validation, with a maximum.
- **Element 3** — an explicit timeout, and a cost ceiling for one extraction
  including its retries.
- The empty-input guard, which belongs to element 3.

**Excludes** — cache, fallback, structured logging, feature flag. The next two
specs. Where an element here needs one of those to be complete, it stops at its
own boundary and says so rather than reaching forward.

## 3. Domain and data model

No change. `TicketExtraction` is unchanged; the empty-input guard returns an
instance of it using values the closed sets already allow.

**Schema change:** no changes.

## 4. API contract

N/A — see `ARCHITECTURE.md` section 6.

## 5. Implementation

### Element 1 · Validated structured output

Already built. What this spec adds is the record of **what it actually buys**,
because it is more than "the JSON parses":

- The reply is constrained at the provider, so the code is not guessing at a
  format. The baseline's defining failure — a code fence — cannot occur.
- **It bounds a prompt injection.** With the category set closed at the schema,
  the most an injected instruction can achieve is a *wrong but valid* category.
  It cannot make the model emit the system prompt, arbitrary text, or a shape the
  caller did not ask for. The blast radius is structural, not behavioural.
- Validation still runs on arrival, because a reply can satisfy a schema and
  still be wrong, and because a provider can always return something unexpected.

### Element 2 · Retry on validation failure

**Only validation failures are retried here.** Transport failures — 429, 5xx,
connection errors — are already retried with backoff by the SDK, and
reimplementing that would be duplicating a mechanism that already exists and is
better tested than anything added here would be.

That distinction decides the shape: a validation failure is not congestion. The
provider answered promptly and answered badly, so waiting changes nothing about
the next attempt's chance of success. What the delay would buy is unclear, and
what the maximum buys is obvious — a bound on cost and latency.

### Element 3 · Timeout and cost ceiling

An explicit timeout, short enough to be a decision rather than the SDK's
ten-minute default.

A cost ceiling for **one extraction including its retries**: the run harness
already bounds a whole run, and this bounds a single request so that one
pathological ticket cannot consume the run's allowance on its own.

**The empty-input guard belongs here.** Two dataset cases are empty or
whitespace, and the provider rejects them with a 400 before inference. Guarding
them:

- spends nothing on a call that cannot succeed, which is what a cost ceiling is
  for;
- returns `unknown` for both fields, which is what the golden dataset declares to
  be the **correct** answer — so it is not a special case, it is the right result
  reached without paying.

The baseline keeps failing on these, and that is a legitimate difference rather
than a rigged one: not validating input is exactly what the naive version is.

## 6. Second implementation directory

N/A — one directory.

## 7. Behaviour walkthrough

1. Input arrives. If it is empty or whitespace, the result is `unknown` for both
   fields, marked as not having consulted the model, and nothing is spent.
2. Otherwise one call goes out, carrying the schema, under an explicit timeout.
3. The reply is validated. On success it is returned.
4. On a validation failure, the attempt is repeated up to the maximum.
5. Before each retry, the cost so far is checked against the ceiling; reaching it
   stops the attempts.
6. Exhausting the attempts or the ceiling raises. **Turning that into a usable
   degraded answer is element 5**, in the next spec, and this one deliberately
   stops short of it.

## 8. Acceptance criteria

- [x] Given a reply that fails validation and then a valid one, the valid result
      is returned and exactly two calls were made.
- [x] Given replies that never validate, the attempts stop at the maximum and the
      number of calls equals it.
- [x] Transport errors are **not** retried by this code — verified by a stub that
      raises one and counts a single call.
- [x] Given accumulated cost at the ceiling, no further attempt is made.
- [x] An explicit timeout is passed to the provider — verified by inspecting what
      the stub received, not by waiting.
- [x] Given empty or whitespace input, `unknown`/`unknown` is returned, **no call
      is made**, and the result is marked as not having consulted the model.
- [x] The naive version is unchanged by this spec — verified by the tests it
      already has.
- [x] No test reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **How does the retry behave between attempts?** (a) immediate, since a validation failure is not congestion; (b) exponential with jitter, familiar but arguably cargo-culted here; (c) immediate **with feedback** — tell the model what failed validation. (c) is the most effective and the most complex, and it makes each retry cost more than the first. **Proposed: (a), with the reasoning written down.** | **Open — decide at the approval gate** | Human |
| **Where does the cost ceiling cut?** (a) count real usage after each attempt and stop before the next — exact, overshoots by at most one call; (b) estimate before calling and refuse — no overshoot, but the estimate can be wrong, and mine was wrong by a factor of two until a real call corrected it. **Proposed: (a), the same choice the run harness made and for the same reason.** | **Open — decide at the approval gate** | Human |
| **The injection benefit is not measurable with this dataset.** The baseline answered both injection cases correctly on its own, so a comparison will show no difference and the claim in element 1 will rest on reasoning rather than data. The final phase must say that plainly instead of implying a win. | Accepted, must be stated | -- |
| A guard that returns a result without calling the model is one step from a guard that returns results the model should have produced. Boundary: it applies only where the provider itself would refuse the input. | Accepted, bounded | -- |

## 10. References

- `ARCHITECTURE.md` sections 0 and 4 · `data/golden.jsonl` (empty cases) · `SPEC-eval-runner` (the run-level ceiling) · `MASTER_PLAN.md` section 7.1

## 11. History

| Date | Change |
|---|---|
| 2026-09-13 | Drafted. Two findings from the baseline runs are folded into existing elements rather than becoming an eighth: the closed schema bounds prompt injection (element 1), and empty input is guarded before paying for a call (element 3). |
| 2026-09-13 | Approved by the human, including both open decisions: immediate retry, and a ceiling that counts real usage. |
| 2026-09-13 | Audit raised a blocking warning and it was resolved by agreement: the canon had the client returning raw text, which cannot carry the cost the ceiling needs. The return is extended to carry text and cost, and `ARCHITECTURE.md` is updated in this build. |
| 2026-09-13 | Built. A first mutation check on the transport-error guarantee proved nothing: the call sits outside the retry `try`, so changing what the `except` catches is a no-op there. The real mutation — moving the call inside — does turn it red, and `ARCHITECTURE.md` now records the placement as the reason the guarantee holds. |
