# Spec — SPEC-feature-flag · Element 7

| Field | Value |
|---|---|
| **SPEC** | `SPEC-feature-flag` |
| **featureId** | `feature-flag` |
| **State** | 🔨 `In progress` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-09-13 |
| **Depends on** | `SPEC-hardening-resilience` |
| **Implementation directories** | `Python codebase` |
| **Integration base** | -- |
| **Spends budget** | `no` |

---

## 1. Problem and goal

The last of the seven. When an LLM feature misbehaves in production — wrong
answers, a price change, an incident upstream — the question is how fast it can
be stopped. If the answer is "ship a release", it is not a kill switch.

## 2. Scope

**Includes** — an environment variable, read on every call, that makes the
hardened version stop consulting the provider and return its deterministic result
instead.

**Excludes** — configuration of anything else. A flag system, percentages,
per-tenant rules: all out of scope, and all the shape of a second project. One
switch, off or on.

## 3. Domain and data model

The outcome marker gains a **fifth** value: `disabled`.

It is not the same as `degraded`, and collapsing them would be the expensive
mistake. `degraded` means the provider could not be made to answer; `disabled`
means nobody asked it to. During an incident, telling those apart in the logs is
the difference between "our switch is working" and "we are still broken".

**Schema change:** no changes. The marker stays private and never reaches the
schema sent to the provider.

## 4. API contract

N/A — see `ARCHITECTURE.md` section 6.

## 5. Implementation

**Read on every call, never at import.** A value captured at import time needs a
restart to take effect, and a kill switch that needs a restart is a deployment
with extra steps. The cost of reading an environment variable per call is
negligible next to a network round trip, and it is what makes the promise true.

**On by default.** The variable's absence means normal operation. A kill switch
exists to stop something in an emergency; forgetting to set it must not be what
takes the feature down.

**Disabled returns the deterministic result** — the same full schema with
`unknown` in both closed fields that the fallback already produces — marked
`disabled`. There is no second shape and no new placeholder: the existing one is
reused, so a caller that already handles a degraded answer handles this one.

**A disabled call is still logged**, with its outcome and zero cost. Silence
would leave an operator unable to confirm from the logs that the switch took
effect, which is the first thing they will want to know.

## 6. Second implementation directory

N/A — one directory.

## 7. Behaviour walkthrough

1. The variable is read.
2. If it says off, the deterministic result is returned marked `disabled`, with
   no call, no cost, and one log record.
3. Otherwise the extraction proceeds exactly as before.
4. Setting the variable between two calls changes the second one's behaviour
   without restarting anything.

## 8. Acceptance criteria

- [ ] With the flag off, no call is made and the result is marked `disabled`.
- [ ] With the flag absent, the extraction proceeds normally — the default is on.
- [ ] Changing the variable between two calls changes the second one's behaviour,
      with no reimport and no restart.
- [ ] A disabled result carries `unknown` in both closed fields and is
      distinguishable from a degraded one.
- [ ] A disabled call writes one log record, with zero cost.
- [ ] The naive version is unchanged: it has no switch, which is the point.
- [ ] No test reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **Does the cache still serve while the flag is off?** (a) no — the flag means "do not use the model's answers right now", and a cached answer is a model answer; one rule, easy to reason about at 3 a.m. (b) yes — those answers are already paid for, and serving them keeps quality up while the provider is the problem. (b) is defensible when the incident is upstream, and wrong when the incident is the answers themselves. **Proposed: (a).** | **Open — decide at the approval gate** | Human |
| Reading the environment on every call makes behaviour depend on ambient state, which is normally a smell. Here it is the requirement: the alternative fails the one thing the element exists for. | Accepted, deliberate | -- |
| A truthy-string check is a classic source of surprise — `"false"`, `"0"` and `"no"` are all truthy in Python. The parsing must be explicit and tested, or the switch fails silently in the direction of staying on. | Accepted, must be tested | -- |

## 10. References

- `DOMAIN.md` (the outcome marker) · `SPEC-hardening-resilience` (the deterministic result) · `ARCHITECTURE.md` section 5

## 11. History

| Date | Change |
|---|---|
| 2026-09-13 | Drafted. `disabled` is a fifth value on the existing marker rather than a reuse of `degraded`: during an incident, "our switch worked" and "we are still broken" must not look the same in the logs. |
| 2026-09-16 | Approved by the human, including the open decision: the cache does not serve while the flag is off. |
