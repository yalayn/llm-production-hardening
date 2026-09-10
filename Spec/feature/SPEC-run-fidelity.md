# Spec — SPEC-run-fidelity · Make the run measure what it claims to

| Field | Value |
|---|---|
| **SPEC** | `SPEC-run-fidelity` |
| **featureId** | `run-fidelity` |
| **State** | 👀 `In review` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-09-09 |
| **Depends on** | `SPEC-v1-naive`, `SPEC-eval-runner` |
| **Implementation directories** | `Python codebase` |
| **Integration base** | -- |
| **Spends budget** | `no` to build. Re-running the baseline afterwards costs about 0.13 USD and is a human act |

---

## 1. Problem and goal

The first real run failed 45 of 50 cases, and **not for any reason the seven
hardening elements address**.

Forty-three died in the same line: `v1_naive` reads `response.content[0].text`,
and Sonnet 5 reasons by default, so index 0 is usually a thinking block whose text
is empty. Two more were empty tickets the API rejects with a 400 before the model
sees them.

Two consequences, and both have to be fixed before the baseline means anything:

- **The comparison loses its causality.** A table showing v1 at ten percent and v2
  at a hundred would be measuring response-block selection, while the text argues
  it measures hardening. No element of the seven — cache, budget, timeout,
  fallback, logging, flag — repairs a thinking block.
- **The instrument cannot show its evidence.** `SPEC-eval-runner` section 5
  required each record to carry *the raw text returned*. It was never built, and
  no criterion checked for it, so the run cannot say what the model actually
  replied.

## 2. Scope

**Includes**
- `v1_naive` selects the block of type `text` rather than the first block.
- The runner records the raw response text for every call, successful or not.

**Excludes**
- Any other hardening in `v1_naive`. Reading the correct field is correct SDK
  use, not a safety net — see section 5.
- Guarding empty input. It is a real finding and it affects **both**
  implementations; it belongs to a decision of its own, in section 9.
- The README section about the thinking block. That is the final phase.

## 3. Domain and data model

No change. The run-result record gains one field, `raw`, defined in
`SPEC-eval-runner` section 5 and unimplemented until now.

**Schema change:** no changes.

## 4. API contract

N/A — see `ARCHITECTURE.md` section 6.

## 5. Implementation

**`v1_naive` picks the text block.** The same three lines `v2_hardened` already
uses. This does **not** make `v1` less naive, and `ARCHITECTURE.md` section 0 is
not violated: the naive-versus-hardened axis is validation, retries, timeout,
budget, cache, fallback, logging and the flag. Which field of the response you
read is not on that axis — it is the difference between using the SDK correctly
and using it incorrectly, like spelling the endpoint right.

The distinction that settles it: after this change `v1` still parses blindly,
still validates nothing, still lets an invented category through. Nothing it
lacked before, it gains.

**The runner records the raw text.** The usage recorder already intercepts every
response, so the text is captured where the usage already is, and attached to the
case record. It is recorded for failures too — that is precisely when it matters,
and its absence is what made the first run unreadable.

## 6. Second implementation directory

N/A — one directory.

## 7. Behaviour walkthrough

1. A response arrives carrying a thinking block followed by a text block.
2. `v1_naive` walks the blocks, takes the one of type `text`, and passes it to
   `json.loads` unexamined, exactly as before.
3. The recorder stores that same raw text against the call.
4. The runner writes it into the case record whether the call succeeded or not.

## 8. Acceptance criteria

- [x] Given a response whose first block is a thinking block, `v1_naive` returns
      the parsed result rather than raising.
- [x] Given a response with no text block at all, `v1_naive` raises — it does not
      invent a result.
- [x] `v1_naive` still returns an invented category unchanged and still raises on
      prose-wrapped JSON: the previous behaviour is intact — verified by the tests
      already written for it.
- [x] Every run record carries the raw response text, for failed calls as well as
      successful ones.
- [x] A record for a failing case shows what the model actually returned, not only
      the traceback.
- [x] No test reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **Empty input is rejected by the provider with a 400, in both versions.** Two dataset cases hit it. Guarding it before spending a call is a genuine production practice and is **not** among the seven elements. **Proposed: it becomes an element of `v2` only — validate input before paying for a call — and `v1` keeps failing on it, which is a legitimate difference rather than a rigged one.** | **Open — decide at the approval gate** | Human |
| Does correcting the block selection weaken the baseline? Argued in section 5 that it does not, and the third criterion exists to prove it: if `v1` stops letting an invented category through, the change went too far. | Proposed, guarded by a criterion | -- |
| The thinking-block failure is now evidence rather than a defect in flight. Its traces live in the first run's output, which is git-ignored. **If that file is lost, the finding is lost with it.** Mitigation: the final phase quotes the trace into the README, and the summary it commits carries the date and model. | Accepted, mitigated | -- |

## 10. References

- `ARCHITECTURE.md` section 0 (the deliberate divergence) · `SPEC-eval-runner` section 5 · `MASTER_PLAN.md` section 7.1

## 11. History

| Date | Change |
|---|---|
| 2026-09-09 | Drafted after the first real baseline run: 45 of 50 cases failed, 43 of them on response-block selection and 2 on empty input rejected by the provider. Neither cause is anything the seven hardening elements address. |
| 2026-09-09 | Approved by the human in conversation. Build started. The open decision in section 9 concerns a future `v2` element and does not block this one. |
| 2026-09-09 | Built. Both directions verified by mutation: reverting to index 0 turns the new test red, and adding validation to `v1` turns the old one red. The change is bounded on both sides. |
