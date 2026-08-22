<!--
NEUTRAL ARCHITECTURE SKELETON -- stack-agnostic.
/arch-extract generates one <DIR>_ARCHITECTURE.md per implementation directory,
filling these sections with what was EXTRACTED FROM THAT DIRECTORY'S REAL CODE.

Rules when filling it in:
- What is documented is extracted from real code. The agent may **propose**
  improvements at the consultative gate, but only the canon **decided with the
  human** enters the document. Mark the origin of a rule when it matters:
  `real code`, or `adopted improvement` (not yet propagated to the code).
- GENERIC examples (`{Entity}`, `{Resource}`, `{Component}`), never business terms.
- This document decides ARCHITECTURE (the "how"); the domain lives in DOMAIN.md.
- Sections that do not apply to a stack are omitted; a stack may require others.
-->

# <DIR>_ARCHITECTURE — <<directory role>> (<<stack>>)

| | |
|---|---|
| **Provenance** | <<`extracted from the project's own code` · `extracted from a catalogue scaffold` — where the code that was read came from. The document is descriptive either way; the field exists so a reader knows how settled the canon is>> |

> Architecture and development conventions for this directory. Every pattern here
> is extracted from the real code. An agent or developer should produce code
> indistinguishable from the original author's. Examples use **generic
> placeholders**; the business appears only where it supports a technical decision.

## 1. Stack

<<Table: concern → technology → note. Extracted from dependency manifests and code.>>

## 2. Folder / module structure

<<The canonical layout of a unit of work here, with the role of each part.>>

## 3. Startup / composition

<<How it initialises: entry point, registration, shared instances, startup side
effects. The directory's composition root. "There is none" is a valid and
informative answer.>>

## 4. Core patterns

<<The recurring, solid units of the code -- the most important thing to extract.
One subsection per pattern, with a generic example and the observed conventions:
naming, signatures, responsibilities.>>

## 5. Environment configuration

<<How configuration is selected and declared; where constants live. No secrets.>>

## 6. Communication / contract

<<How this directory talks to anything outside itself. If there is no contract
file, say what the external protocol is and where its single call site lives.>>

## 7. Session / security

<<Authentication, authorisation, and the standing rules new code must respect.>>

## 8. Implementation rules

<<The concrete rules a newcomer would otherwise get wrong.>>

### 8.1 Responsibility map

| Core responsibility | Canonical location | What it must not do |
|---|---|---|
| <<...>> | <<...>> | <<...>> |

<<A responsibility landing outside its canonical location is a deviation: reported
at audit time and, if accepted, recorded in 8.2 -- never adopted silently.>>

### 8.2 Debt and accepted exceptions

| Item | Why it is accepted | When it is revisited |
|---|---|---|
| <<...>> | <<...>> | <<...>> |

## 9. Running locally

<<Setup and run commands, exactly as they work.>>

## 10. Tests (TDD)

<<Runner, location, command, isolation strategy, naming. The test comes before the
production code; nothing closes red.>>
