# Spec — SPEC-v1-structured · The third variant

| Field | Value |
|---|---|
| **SPEC** | `SPEC-v1-structured` |
| **featureId** | `v1-structured` |
| **State** | ✅ `Implemented` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-09-16 |
| **Depends on** | `SPEC-v1-naive`, `SPEC-eval-scoring` |
| **Implementation directories** | `Python codebase` — adds `v1_structured/` |
| **Integration base** | -- |
| **Spends budget** | `no` to build. The comparative run afterwards costs about 0.49 USD and is a human act |

---

## 1. Problem and goal

A reader who knows the current API will ask, in the first thirty seconds:
*"the provider constrains output natively — isn't that enough?"*

It is the strongest objection this repository faces, and answering it in prose
would be an assertion against an assertion. This variant answers it with a
column of numbers: the naive version **with** native structured output and
nothing else.

The baseline runs already show what makes it necessary. In the second run, **45
of 48 replies arrived wrapped in a code fence** and `json.loads` failed on the
first character. Structured output fixes precisely that — and nothing else. This
variant measures where "nothing else" ends.

## 2. Scope

**Includes** — `v1_structured/extractor.py`: the naive implementation with one
call changed, sending a response-format constraint.

**Excludes** — every one of the seven elements. No schema validation on arrival,
no retry, no timeout, no budget, no cache, no fallback, no structured logging, no
switch. If it gains any of them it stops being the third column and becomes a
worse copy of the second.

Also excluded: importing anything from `v1_naive` or `v2_hardened`.

## 3. Domain and data model

Targets the same shape as `DOMAIN.md`. It declares **its own** JSON schema as a
literal, rather than importing the Pydantic model from `v2_hardened`.

That is deliberate and it is the same reasoning the golden dataset uses. Three
independent statements of the same vocabulary that agree are evidence; one shared
constant hides the day they stop agreeing. And a developer reaching for structured
output for the first time writes the schema by hand from the documentation — which
is what this variant is portraying.

**Schema change:** no changes.

## 4. API contract

N/A — see `ARCHITECTURE.md` section 6.

## 5. Implementation

One module, one public function, the same shape as `v1_naive`: a client parameter
with a real default, one call, `json.loads` on the way out.

**The single difference** is the response-format constraint on the request. The
reply is still parsed blindly and returned as a plain `dict`. Nothing checks that
the category is one the schema allowed — the provider was asked to constrain it,
and this variant takes that on trust, which is exactly the position being tested.

**The duplication of `v1_naive` is deliberate.** Sharing code between the two
would mean a change to one silently changing the other, and the comparison rests
on them being independently frozen. Forty lines copied is cheaper than a
comparison that quietly stops comparing.

## 6. Second implementation directory

N/A — one directory.

## 7. Behaviour walkthrough

1. The caller passes ticket text.
2. A system prompt and a response-format constraint go out together.
3. The reply's text block is passed to `json.loads`.
4. The resulting `dict` is returned, unexamined.

**Failure modes that remain, and are the point:** a category outside the allowed
set if the provider yields one; a missing field surfacing as a `KeyError` far
away; a provider error or timeout propagating; empty input rejected with a 400
before inference. None of these is what structured output addresses.

## 8. Acceptance criteria

- [x] Given a stub returning well-formed JSON, a `dict` with the four expected
      keys is returned.
- [x] The request carries a response-format constraint — verified by inspecting
      what the stub received.
- [x] Given a reply whose category is outside the declared set, the value is
      returned unchanged: nothing validates on arrival.
- [x] Given a transport error, it propagates: there is no retry and no fallback.
- [x] `v1_structured` imports nothing from `v1_naive` or `v2_hardened` — verified
      by a test, not by inspection.
- [x] The runner can run it by name, alongside the other two.
- [x] Neither existing implementation is changed by this spec.
- [x] No test reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **Three independent copies of the category vocabulary now exist** — the dataset, the hardened schema, and this one. Each is a separate statement of what its author believed, and disagreement between them is a finding the eval surfaces rather than a bug a shared constant would hide. It also reads like duplication to someone skimming, and this project has spent real effort removing exactly that. **Proposed: keep them independent, and have `ARCHITECTURE.md` say why in one place so a future reader does not "fix" it.** | **Open — decide at the approval gate** | Human |
| This variant may score close to the hardened one, since the fence failure is the dominant one in the baseline. That would be an uncomfortable result and a true one: it would mean most of the measured gap comes from element 1, and the other six earn their place on grounds the dataset cannot show — reliability under provider failure, cost control, and being able to turn it off. The README must say that rather than let the table imply otherwise. | Accepted, must be stated | -- |
| A third column makes the headline table harder to read, which is why it stays out of it: the table compares naive against hardened, and this variant appears in its own section answering the question it exists for. | Decided in `SPEC-readme-failures` | -- |

## 10. References

- `ARCHITECTURE.md` section 0 (the deliberate divergence) · `SPEC-v1-naive` · `evals/runner.py` (the implementation registry)

## 11. History

| Date | Change |
|---|---|
| 2026-09-16 | Drafted. Exists to answer the strongest objection the repository faces with a column of numbers rather than a paragraph. |
| 2026-09-16 | Approved by the human, including the open decision: the three vocabularies stay independent, with `ARCHITECTURE.md` explaining why in one place. Build started. |
| 2026-09-16 | Built. The independence guard was grepping raw text, so it fired on a docstring explaining why the duplication is deliberate — a mention is not an import. Both guards now read the AST; the naive version's had the same latent weakness and was fixed with it. |
| 2026-09-16 | Reviewing the diff moved the import-guard helper into `tests/helpers.py`: it had been sitting below the tests that used it, with another test module importing it from there. |
| 2026-09-16 | Criteria approved by the human. Closed as `Implemented`. Merged before this closing commit, so the state transition arrives as a follow-up — the second time in this project. |
