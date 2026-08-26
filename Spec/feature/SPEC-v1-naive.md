# Spec — SPEC-v1-naive · The naive extraction implementation

| Field | Value |
|---|---|
| **SPEC** | `SPEC-v1-naive` |
| **featureId** | `v1-naive` |
| **State** | 📝 `Draft` |
| **Author** | Yordin Da Rocha |
| **Date** | 2026-08-20 |
| **Depends on** | -- |
| **Implementation directories** | `v1_naive` (new) |
| **Integration base** | -- |
| **Spends budget** | `no` — every test runs against a stub |

---

## 1. Problem and goal

This repository's product is a **comparison**. A comparison needs a baseline, and
the baseline has to be one a competent engineer recognises as their own work.

If a reader can say *"nobody writes it like that"*, every number in the results
table becomes worthless — the hardened version would only be beating a straw man.
So the goal here is narrow and unusual: write the version **without** the safety
net, and write it **well**.

## 2. Scope

**Includes**
- `v1_naive/extractor.py` — the whole implementation, one module.
- A prompt that describes the desired JSON shape **in prose**.
- A direct call to the provider and `json.loads()` on the response text.
- Tests that pin the behaviour, including how it fails.

**Excludes (out of scope)**
- Schema validation, retries, timeout, budget, cache, fallback, structured
  logging, feature flag. Their absence **is** the feature.
- Any import from `v2_hardened`. The two implementations must be independent or
  the comparison measures nothing.
- Making it fail on purpose. Every weakness must be one a real developer would
  plausibly ship, never one inserted to lose.

## 3. Domain and data model

Targets the same conceptual output as `DOMAIN.md` — `category`, `urgency`,
`entities`, `suggested_action` — but **does not import `TicketExtraction`**.

That is the point of the exercise. `v1_naive` describes the shape in prose inside
its prompt and returns whatever `json.loads()` produces: a plain `dict`, unchecked.
Two implementations aiming at one shape, one of which can prove it hit it.

**Schema change:** no changes.

## 4. API contract

**N/A for this project.** Single layer, no runtime communication between parts —
`principles.md` section 4 omits the contract slot.

## 5. `v1_naive`

One module, one public function. No package structure, no seam, no abstraction:

```
v1_naive/
  __init__.py
  extractor.py
```

**The prompt carries the schema in prose.** A JSON example embedded in the system
prompt, the way you write it when you want to be done in ten minutes.

**The client is a parameter with a real default.**

```python
def extract_ticket(ticket_text, client=None):
    client = client or anthropic.Anthropic()
```

This deserves its one line of justification, because it is the most contestable
decision in the spec. A hurried developer does **not** build a Protocol — but they
very often do write exactly this idiom, because it is the shortest path to
something testable. It keeps `v1` honest (no abstraction of its own, no shared
seam with `v2`) while letting the eval harness drive it offline.

The awkwardness that follows — a test has to fake the SDK object's shape rather
than a clean one-method interface — is **not a flaw in the spec**. It is one of
the things the comparison exists to show.

**The response is parsed with `json.loads()` and returned as-is.** No validation,
no repair, no catch. If the model wraps the JSON in prose, the exception
propagates to the caller. That is the behaviour being measured.

## 6. Second implementation directory

**N/A — outside the declared scope.** This spec touches one directory.

## 7. Behaviour walkthrough

1. The caller passes ticket text to `extract_ticket`.
2. A system prompt describing the target JSON is combined with the ticket.
3. One request goes to the provider. No timeout is set beyond the SDK default; no
   retry policy is configured beyond the SDK default.
4. The response's text block is passed to `json.loads()`.
5. The resulting `dict` is returned, unexamined.

**Failure modes, all deliberately unhandled:** the model wraps JSON in prose
(`JSONDecodeError`); returns valid JSON with a category that does not exist (no
error at all — the caller receives it); omits a field (the caller gets a `KeyError`
later, far from here); the provider errors or times out (the exception propagates).

## 8. Acceptance criteria

- [ ] Given a stub returning well-formed JSON, when `extract_ticket` is called,
      then a `dict` carrying the four expected keys is returned.
- [ ] Given a stub returning JSON wrapped in prose, then `json.JSONDecodeError`
      propagates out of `extract_ticket` — pinned by a test, because that failure
      is a documented result of this version, not an accident.
- [ ] Given a stub returning valid JSON with a category outside the known set,
      then the value is returned unchanged and no error is raised.
- [ ] `v1_naive` imports nothing from `v2_hardened` — verified by a test, not by
      inspection.
- [ ] `extract_ticket` is callable with a single argument, using a real client by
      default.
- [ ] No test in this feature reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| **Does `v1` use the provider's native structured output?** The API offers `output_config.format`, and it is on the first page of the documentation — so a competent developer in a hurry might well reach for it. If `v1` uses it, it stops being naive in the one dimension that matters most and the comparison narrows. If it does not, a reader may object that the baseline was weakened on purpose. **Proposed: `v1` asks for JSON in the prompt and parses with `json.loads()`** — that is what dominates the real code in the wild — **and the README states this choice and its reasoning explicitly** rather than leaving it to be discovered. | **Open — decide at the approval gate** | Human |
| How do we verify "well written" at all? It is the one acceptance criterion that cannot be made binary. Proposed check: read it against the question *"would a good developer sign this on a Friday afternoon?"* and treat a "no" as blocking. | Open | Human |
| `v1_naive` has no `*_ARCHITECTURE.md`, and cannot have one before its code exists. `/build` will therefore construct without a standing canon for this directory. The method names only one exception to that rule (the catalogue bootstrap spec) and this is not it. **This is a real gap in the instrument**: it does not describe how a brownfield project adds a genuinely new directory. Proposed handling: section 5 above carries the design intent, and `/arch-extract` runs on `v1_naive` at closing so its document is born descriptive as always. | Open — gap recorded, workaround proposed | Human |
| A future contributor or agent may "improve" `v1` by adding validation, breaking the comparison silently. Mitigation: the architecture document extracted at closing records the omissions **as deliberate canon**. | Accepted, mitigated | -- |

## 10. References

- Domain: `DOMAIN.md`
- Architectures: `V2_HARDENED_ARCHITECTURE.md` (for contrast only; it does not
  bind this directory), `V1_NAIVE_ARCHITECTURE.md` (to be extracted at closing)
- Method: `methodology/principles.md`
- Orchestration: `MASTER_PLAN.md`

## 11. History

| Date | Change |
|---|---|
| 2026-08-20 | Spec drafted. Three decisions left open for the approval gate: whether `v1` may use native structured output, how "well written" is verified, and how a new directory acquires an architecture document. |
