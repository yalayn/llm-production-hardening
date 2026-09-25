# Spec — SPEC-readme-comparison · The README this repository exists to deliver

| Field | Value |
|---|---|
| **SPEC** | `SPEC-readme-comparison` |
| **featureId** | `readme-comparison` |
| **State** | 📝 `Draft` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-09-24 |
| **Depends on** | `SPEC-readme-failures`, `SPEC-eval-fidelity`, `SPEC-eval-scoring` |
| **Implementation directories** | `Python codebase` — `README.md` and `tests/` |
| **Integration base** | -- |
| **Spends budget** | `no`. Every figure comes from run files already committed. No provider call is needed to write or to verify this |

---

## 1. Problem and goal

The repository is read by someone deciding whether the author can be trusted with
a broken AI feature. Everything it needs to earn that now exists — four measured
runs, a 50-case dataset, three implementations and a diagnostic — and the README
still opens with the word **Incomplete** and carries one section out of the six it
needs.

The measurement also changed what the README can claim. The project was built to
show that hardening an LLM feature makes it work. What it measured is narrower and
more useful:

- **Without a schema there is no product.** `v1_naive` failed 46 of 50 cases, and
  most of them on prose wrapped around the JSON.
- **The accuracy was bought by the prompt, not by the hardening.** Describing four
  schema fields moved entity extraction by 16 cases, none lost. The diagnostic
  proves it: it is `v1_structured`'s code path with the hardened version's schema
  and system prompt, and nothing else.
- **The seven elements produced no measurable accuracy gain.** Every case
  `v2_hardened` wins over the diagnostic is one of the two empty tickets. That is
  one element — guarding input before paying — and the other six show nothing,
  because the provider never failed in roughly 200 calls.

A README that credits resilience for the entity gain would be making a claim its
own data refutes, and the first reader to open both files would find it.

**Goal:** a README whose every figure is recomputed from a committed run by a
test, which says plainly what was measured, what was not, and which of the three
findings a reader should act on.

## 2. Scope

**Includes**
- `README.md`, complete: the comparative table in the first 20 lines, the existing
  failure section, the attribution section, what the eval does not measure, the
  seven elements with one line of reasoning each, how to reproduce, and a closing
  contact paragraph.
- `tests/test_readme_figures.py` extended: every new figure recomputed from the
  run files, so a stale number cannot be published.

**Excludes**
- Any change to an implementation, to the harness, to scoring or to the dataset.
  If writing this reveals a defect in one of those, it is a finding for a spec of
  its own — see section 9.
- New runs. Nothing here needs the provider.
- A `CONTRIBUTING`, a licence, badges or CI. Out of the project's declared scope.

## 3. Domain and data model

No change. **Schema change:** no changes.

## 4. API contract

N/A — see `ARCHITECTURE.md` section 6.

## 5. Implementation

### 5.1 The first twenty lines

One sentence saying what the repository is, then the table: **three columns —
`v1_naive`, `v1_structured`, `v2_hardened`** — with uncontrolled failures,
accuracy on the three scored fields, cost per 1,000 requests and latency
p50/p95.

**Three columns, not four.** Those are the three things a reader could build. The
diagnostic is an instrument, and a fourth column invites a hurried reader to take
a control for a recommendation. It gets its own section instead, where the point
is attribution rather than choice.

Immediately under the table, one line saying what it proves and what it does not:
that the accuracy came from the schema and the prompt, and that the resilience
elements are not what these numbers measure. **Above the fold, not deferred.** The
reader this repository is written for is looking for the catch; finding it stated
by the author is what makes the rest credible. The risk — that the first screen
reads as the repository undermining itself — is real and is answered by wording,
not by moving the line further down.

### 5.2 The attribution section

Three steps, each with the number that isolates it:

| Step | What changes | Measured effect |
|---|---|---|
| `v1_naive` → `v1_structured` | the schema | 46 → 2 uncontrolled failures |
| `v1_structured` → diagnostic | the prompt surface | entities +16, −0 |
| diagnostic → `v2_hardened` | the seven elements | the two empty tickets, nothing else |

**The noise floor is stated before any of it.** Two runs of `v2_hardened` on
identical code and prompts disagree on 1 category, 3 urgency and 2 entity
verdicts, so a gap of three cases or fewer is indistinguishable from variance.
Without that figure the reader cannot tell which differences in the table are
real, and neither could the author.

The third row is shown case by case, because "nothing else" is a strong claim: the
two cases outside the empty family that `v2_hardened` wins are each offset by one
it loses.

### 5.3 What the eval does not measure

The six elements that showed nothing did not fail — they were never exercised.
The provider did not time out, did not rate-limit and did not return a malformed
reply in roughly 200 calls; the dataset has one duplicate ticket, so the cache
could hit once; the flag was never switched off.

This section says so in those terms, and says what each element is for in
production. It must not convert absence of evidence into evidence, in either
direction: the elements are not claimed to be worthless, and they are not claimed
to be worth something this eval demonstrated.

### 5.4 The seven elements, one line each

The original requirement: every design decision defensible in one line to a
client. Each element gets its line, and where a reasonable alternative was
rejected, the line says which and why — retry covering validation failures only,
the cache key covering prompt and model and schema rather than the ticket alone,
failures never cached, `disabled` never reusing `degraded`.

### 5.5 Reproduction

The install command, the test command, and the runner invocation for each
implementation with its budget flag. It states that every figure above can be
recomputed from the committed runs **without spending anything**, and what the
four runs cost when they were made.

### 5.6 The figures are guarded

`tests/test_readme_figures.py` grows one test per new figure, each reading the
run files and asserting the README contains the number it computes. The existing
tests already do this for the failure section. A figure that appears in prose
without a test behind it is a figure that will go stale silently.

## 6. Second implementation directory

N/A — one directory.

## 7. Behaviour walkthrough

1. A reader opens the repository and sees, within the first screen, the table and
   the sentence qualifying it.
2. Wanting the catch, they read the attribution section and find the noise floor
   and the case-by-case third row.
3. Doubting the numbers, they clone, run `pytest`, and the figure tests recompute
   every one of them from the committed runs without a provider call.
4. Deciding what to do in their own codebase, they get three separable
   recommendations rather than one bundle.

## 8. Acceptance criteria

- [ ] The comparative table is complete and begins within the first 20 lines.
- [ ] The word `Incomplete` is gone, and no section is left as a placeholder.
- [ ] The table has three columns; the diagnostic appears in its own section.
- [ ] The sentence stating what the table does and does not prove sits directly
      under it, above the fold.
- [ ] The noise floor is stated as a measured figure before any comparison is
      argued from.
- [ ] The third attribution row is shown case by case, including the two cases
      `v2_hardened` loses.
- [ ] Every numeric figure in the README is recomputed from a committed run file
      by a test, and the suite fails if any figure is edited by hand.
- [ ] The seven elements each carry one line of reasoning.
- [ ] A reader can reproduce every figure without spending anything, and the
      README says so and says what the runs cost.
- [ ] The README closes with a contact paragraph.
- [ ] No test reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **The first screen may read as the repository refuting itself.** Decided at the approval gate: the qualifying line stays above the fold, because the reader is looking for the catch and finding it stated by the author is what buys the rest. Mitigated by wording, not by placement. | Decided by the human, 2026-09-24 | -- |
| **The six unexercised elements are the weakest part of the deliverable.** They are argued from production experience, not from this eval. The README must label that boundary explicitly. An eval that injected provider failures would measure them and is the obvious next project — named, not silently skipped. | Accepted, declared in 5.3 | -- |
| Figures freeze a model's behaviour on a date. Sonnet 5 will change. Mitigation: the README dates every run and names the model, and the noise floor tells a future reader how much movement is meaningless. | Accepted, mitigated | -- |
| Writing the README may surface a defect in scoring or in the dataset. If it does, it becomes its own spec rather than a quiet fix here: this spec changes prose and tests only. | Declared | -- |
| `v1_structured` answered both prompt-injection cases correctly, and `v1_naive` got two of its three passes there. Already recorded as an honest admission; it stays in the README rather than being dropped for being inconvenient. | Decided | -- |

## 10. References

- `SPEC-readme-failures` (the section this one completes) · `SPEC-eval-fidelity` sections 5 and 9 (the attribution and what it would cost to be wrong) · `MASTER_PLAN.md` section 7.1 (the spending gate) · `ARCHITECTURE.md` section 0

## 11. History

| Date | Change |
|---|---|
| 2026-09-24 | Drafted after the four runs were scored. The measurement changed the deliverable's thesis: the accuracy belongs to the prompt, and the seven elements' only measurable contribution is the empty-input guard. Two forks decided at the gate — three columns with the diagnostic in its own section, and the qualifying sentence above the fold. |
