# MASTER PLAN — llm-production-hardening

> The operative instance of the method for this project. The invariant theory
> lives in `methodology/principles.md`; this document says how it applies here.

| Field | Value |
|---|---|
| **Project** | `llm-production-hardening` |
| **Method version** | `3.1.0` |
| **Identity prefix** | `SPEC` |
| **Topology** | Single repository — code and `Spec/` versioned together |
| **Integration base** | `main` |
| **Onboarded** | 2026-08-20, brownfield |

## 1. Purpose

A public engineering reference: the same LLM feature — structured extraction from
a free-text support ticket — implemented twice, naively and hardened for
production, and compared with **measured numbers**.

The comparison is the product. Anything that makes the numbers less trustworthy —
an unfair setup, an estimated figure presented as measured, a naive version
written badly on purpose — defeats the point.

## 2. Directory philosophy

| Directory | Role | State |
|---|---|---|
| `Spec/` | Orchestrating authority: architecture, domain, feature state | Active |
| `v2_hardened/` | The production-hardened implementation | Implemented (vertical only) |
| `v1_naive/` | The typical implementation, written well and without a safety net | Planned |
| `evals/` | The comparison harness and its output table | Planned |
| `data/` | The golden dataset. Data, not an implementation directory | Planned |
| `tests/` | Test root for every implementation directory | Active |

Implementation directories are artefacts: they are not modified without a spec
backing the change. `v1_naive` and `evals` are **not yet declared** in
`methodology.config.yaml` — a directory with no code gets no architecture
document, and declaring one early would create a binding document with nothing
behind it. They join the config when their first spec creates them.

## 3. Document hierarchy

```
MASTER_PLAN.md            this file -- orchestration
  methodology/            the frozen method: manual and templates
  DOMAIN.md               what exists in the domain
  <DIR>_ARCHITECTURE.md   how code is written in each directory (binding)
  feature/SPEC-<id>.md    one document per feature: identity, state, history
```

**No contract file.** A single layer with no runtime communication between parts,
so `principles.md` section 4 omits the contract slot, and with it the API
documentation step.

### 3.1 Finding specs without an index

There is no central index. A spec's own header is the single source of truth for
its state, so:

```
grep -l "In review" Spec/feature/*.md
```

The `Date` field plus `git log` give chronological order, since names carry no
sequential number.

## 4. Orchestration flow

```
SPEC → approval → AUDIT → IMPLEMENTATION (TDD) → VERIFICATION → CLOSING → merge
```

- `/spec` writes the *what* and stops at `Draft`.
- The human approves: `Draft → Ready`. **Gate.**
- `/build` creates the feature branch, audits against the standing architecture,
  implements test-first, and stops at `In review`. It does not open a pull request.
- The human approves the acceptance criteria. **Gate.**
- `/cierre` writes the closing commit, pushes, and hands off the pull request body.
- The human merges. **Gate.**

## 5. Branches and integration

- Branch name: `feat/SPEC-<featureId>`, derived from the featureId at authoring time.
- The agent creates branches, commits and pushes. It never commits to `main`.
- **Pull requests are opened by the human** (`version_management.pull_request.author: human`).
  `/cierre` hands over the comparison URL together with the filled-in body.
- **Merging is human, always.** The method does not make that configurable.
- No remote is configured yet. Until one exists, `/cierre` can prepare a pull
  request but nothing can be pushed — the last gate stays incomplete.

## 6. Spec states

`Draft` → `Ready` → `In progress` → `In review` → `Implemented`, plus `Paused`
outside the cycle. Only the header of each spec records this.

## 7. Global development rules

1. **Consistency over creativity.** New code is indistinguishable from the decided
   canon of its directory.
2. **Bounded scope.** Nothing the spec did not ask for. This project's brief lists
   explicit exclusions — no interface, no authentication, no database, no
   deployment, no multi-provider abstraction, no container, no CI. If something on
   that list seems necessary, it is raised and discussed, never added quietly.
3. **TDD.** The test before the production code; nothing closes red. A test that
   does not go red when the behaviour it covers is broken is not a test.
4. **No secrets** anywhere in the repository, including tests and fixtures.
5. **Integration only by pull request.**
6. **Every design decision is explained in one line** — enough for the author to
   defend it in a technical conversation. Where more than one option is
   reasonable, the alternatives and their trade-offs are presented and the human
   chooses.
7. **Simple over clever.** A reader should follow any module in five minutes.
8. **English throughout** — code, comments, names and documentation, this
   directory included.

**Testing requirement.** Every affected implementation directory must declare its
test framework and its test folder; without that, Verification is **blocked** for
that directory and its feature cannot leave `In progress`. Current state:
`v2_hardened` satisfies it (pytest, `tests/`, green).

### 7.1 Spending gate — project-specific

**The agent never issues a live provider request.** Not in a test, not in a build
step, not to check something quickly.

This is the same boundary that `principles.md` section 4.1 draws around applying a
migration to a real database: irreversible, outward-facing, and therefore human.
Here it is also budgeted — the whole experiment runs on a fixed allowance, and an
agent debugging in a loop is exactly how such an allowance disappears.

- Tests run against a stub implementing the client Protocol. Deterministic, free.
- Every real run is launched by the human, with its estimated cost reported first.
- A spec whose closing needs a live run declares `Spends budget: yes` in its header.

## 8. Naming conventions

- **featureId** — a readable kebab-case slug, unique. It is the spec's canonical
  identity: no sequential number to reconcile between parallel authors. Two
  identical featureIds collide as files, which is visible immediately.
- **`SPEC-<featureId>`** — the full identity. Stable from authoring, immutable
  afterwards.
- **Branch** — `feat/SPEC-<featureId>`.

## 9. Starting a feature

### 9.1 Writing the spec — `/spec`
1. Read `DOMAIN.md` and the relevant `*_ARCHITECTURE.md`.
2. Copy `methodology/SPEC_TEMPLATE.md` to `feature/SPEC-<featureId>.md`.
3. Fill it in, leave it at `Draft`, commit to an authoring branch.
4. **Stop.** The human approves the move to `Ready`.

### 9.2 Building — `/build` then `/cierre`
1. `/build` creates `feat/SPEC-<featureId>`, records `In progress`, audits, then
   implements test-first.
2. Suite green, state `In review`, branch pushed, **no pull request**.
3. **Stop.** The human approves the criteria.
4. `/cierre` writes the closing commit with its `Accepted criteria` block and
   hands off the pull request.
5. **Stop.** The human merges.
