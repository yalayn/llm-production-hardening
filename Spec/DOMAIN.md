# DOMAIN — llm-production-hardening

> The catalogue of what this project's domain contains. It answers *what exists*,
> never *how it is built* — that lives in each `*_ARCHITECTURE.md`.
>
> This document mirrors **implemented reality** and is updated at closing, not
> proposed ahead of the code.

## 1. Scope and responsibility

Support ticket triage. One free-text ticket goes in; validated structured data
comes out. There is no persistence, no user, no session and no authorisation —
the domain is a single transformation and the vocabulary that describes it.

## 2. Domain entities

| Entity | Where it lives | Role |
|---|---|---|
| `TicketExtraction` | `v2_hardened/schema.py` | The output contract: the validated result of triaging one ticket. Fields: `category`, `urgency`, `entities`, `suggested_action` |
| `Category` | `v2_hardened/schema.py` | Closed set: `billing`, `technical`, `account`, `feature_request`, `other`, `unknown` |
| `Urgency` | `v2_hardened/schema.py` | Closed set: `low`, `medium`, `high`, `critical`, `unknown` |

**Ticket text** is domain input but not a modelled entity: it is an unstructured
string supplied by the caller. It is also **untrusted** — see
`ARCHITECTURE.md` section 7.

### The distinction between `other` and `unknown`

Not redundancy, and the reason both exist is worth keeping written down:

- `other` — the ticket is clear, and it fits none of the listed categories.
- `unknown` — the ticket does not say enough to decide.

Without the second, a genuinely ambiguous ticket forces an invented answer, and
the ambiguous cases in the golden dataset would have no correct answer available
to any implementation.

## 3. Exposed operations

| Operation | Where it lives | Role |
|---|---|---|
| `extract_ticket(text, client)` | `v2_hardened/extractor.py` | Composes the prompt, calls the provider, validates the result |

## 4. Presence in other directories

> **This section is the single owner of implementation status.** `principles.md`
> section 4.1 makes this document the mirror of implemented reality, updated at
> closing. No other document repeats it — one that did would be wrong within the
> hour, as three of them were.

| Directory | Status |
|---|---|
| `v2_hardened` | Implemented — owns the domain definitions |
| `v1_naive` | **Implemented** (2026-08-20). Deliberately does **not** import these definitions: it describes the target shape in prose inside its prompt, which is a large part of what is being measured |
| `evals` | **Implemented** (2026-09-08), run harness only. Compares both implementations against the golden dataset; consumes the domain, does not define it. Scoring and the comparative table are still to come |

## 5. Growth considerations

- The category set is closed on purpose. Adding a value changes the golden
  dataset's expected answers, so it is a spec-level decision.
- There is no versioning of the output shape. If one is ever needed, it belongs
  in this document before it belongs in the code.
