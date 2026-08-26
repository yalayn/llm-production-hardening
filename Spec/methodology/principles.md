# Method principles (invariant)

> The **theory** of the methodology, independent of any project or stack. The
> `MASTER_PLAN` generated in each project is the *operative instance* of these
> principles. This document is never tokenised: it is the manual.
>
> **Translation note.** The method is authored in Spanish and vendorised as such.
> This copy is an English translation, kept as a declared customisation so that
> this public repository reads in one language. `/methodology-update` detects
> hand-edited machinery and reports instead of overwriting, so an update will
> surface its delta rather than silently reverting this file.

## 1. Three directory roles

Every project is seen as **implementation directories** (the code: backend,
frontend, services...) governed by a **`Spec/`** directory that is the
**orchestrating authority**.

- Implementation directories are artefacts: they are not modified without a spec
  backing the change.
- `Spec/` holds the architectural truth, the **contract** between layers, and the
  state of every feature.

## 2. The spec is the only way in

No development starts without an **approved spec**. Where the idea **came from**
(a conversation, a prototype, a user story) is **agnostic** to development: those
origins are interchangeable and sit *outside* the flow; their only output is to
feed the spec. Material origins are loaded into input folders (`prototype/`,
`stories/`), each with its own convention; when writing, the spec **ingests** them
if they exist (they are optional).

## 3. One document, one responsibility

Each document **answers a single question** and **changes for a single reason**.
Information is not duplicated across documents: if a fact needs to live in two
places, one of them is redundant. If a change modifies no document, it is not a
real change.

Typical hierarchy, widest scope first: master plan → spec template → feature spec
(identity, state and history in a single document) → contract → architectures →
domain → prototypes/stories.

## 4. The contract governs communication

The **contract** (e.g. `openapi.yaml`) is the source of truth for communication
between layers. It is **derived from the spec** — not maintained by hand, not
synchronised by tooling. Layers are implemented **against it**.

> **Applies with two or more communicating layers.** In projects with a single
> layer or artefact — no runtime communication between parts — the contract slot
> is omitted. **This project is that case.**

> **API documentation is a VIEW of the contract.** Human-readable API
> documentation is a renderer of the contract, not a parallel source. It applies
> only where a contract exists.

### 4.1 The data model governs persistence

The analogue of the contract, for **persistence**: the **schema** is a source of
truth derived from the spec.

- **Invariant:**
  1. A **schema change is decided in the spec** (section 3), never improvised in `/build`.
  2. The **migration is a derived artefact** (code) living in the implementation
     directory, **not** in `Spec/`.
  3. The migration is **applied under a human gate**: the agent produces and
     pushes it, but **never runs it against a real database** — the same
     irreversible, outward-facing boundary as integrating by pull request.
  4. Every migration is **reversible in schema** (a paired `down`); the reverse
     covers **structure**, it does not resurrect **data**.
  5. `DOMAIN.md` reflects **implemented reality** and is updated at **closing** —
     a mirror of the code, not a proposal.
  6. **Reuse before creating, against the FRESH base.** The `/build` audit
     synchronises `DOMAIN.md` (and the contract, where one exists) against the
     base before judging what already exists.
- **Adaptable:** the **mechanism** — the project's migration framework if it has
  one, or the versioned `.sql` fallback the method defines if it does not.

### 4.2 Architecture governs construction

The analogue for "how code is written": each directory's `*_ARCHITECTURE.md` is a
**binding** source of truth, not a style guide.

- **Invariant:**
  1. `*_ARCHITECTURE.md` is the **binding** authority for how each directory is
     built. In case of doubt about structure, conventions or design decisions, it
     **prevails** over external patterns and over inconsistent legacy code. Both
     modes **read** it; it is **written** only through the defined channels:
     initial bootstrap (`arch-extract`), the consultative update at `/build`
     closing, and the architectural audit that precedes implementation.
  2. **Spec Mode consults it, never writes it.**
  3. The post-bootstrap update cycle is **consultative and iterative**: at
     `/build` closing, if the code introduced a decision not reflected in the
     standing canon and not anticipated by the audit, the agent **proposes** it;
     the human **decides** before the document changes. It is never rewritten
     silently.
  4. The "debt / exceptions" register of each `*_ARCHITECTURE.md` remains the
     channel for deviations **accepted as exceptions** (which do not become
     canon).
  5. **Architectural warnings at audit time** (before writing code, not at
     closing). For each task in the spec, the agent audits it against the
     standing `*_ARCHITECTURE.md` and raises one of two warnings:
     - **Blocking** — the standing architecture does **not support** the task.
       The plan **pauses**, but this is not a binary vote: the agent presents its
       proposal with alternatives and trade-offs, and agent and human **iterate
       to agreement**. With agreement, the document is updated and work
       continues. Without it, the spec cannot be executed as written: adjust
       scope via `/spec`, or leave it paused.
     - **Suggestion** — a route exists within the standing canon, but the agent
       proposes a better one. Approved, the document is updated. Rejected, the
       agent **continues with the standing canon** without blocking.
     - In no case does the agent improvise a solution outside the standing canon
       without passing through this audit.
  6. **Provenance: the document is always extracted from code.** An
     `*_ARCHITECTURE.md` is binding **because it describes something that
     exists**. Where that code came from admits two provenances — `extracted`
     (the project's own code) or `scaffolded` (a catalogue entry planted by
     `/build`) — but in both the document is written by **reading**, never by
     designing in the abstract. A directory with no code **has no**
     `*_ARCHITECTURE.md`: that absence is legible information, and it is
     preferable to a skeleton of TODOs that reads as canon without being it.

## 5. Feature flow

```
origin (agnostic) → SPEC → CONTRACT (derived) → AUDIT → IMPLEMENTATION → VERIFICATION → CLOSING
```

With **human control points**: approve the spec, approve the criteria, and
**integrate by pull request** (merge and delete the branch). Creating branches is
**no longer** a human gate: the agent does it.

## 6. Two working modes

The flow runs in two complementary modes, each with **its own file boundary and
stopping condition** so they cannot bleed into each other:

- **Spec Mode** — builds the *what*. Works on an **authoring branch** (free name;
  one session may cover several specs), writes only inside `Spec/`, and pushes
  there. Ends leaving the spec in `Draft`; **it does not implement**.
- **Build Mode** — builds the *how*. Starts from an approved spec; **creates the
  feature's shared branch** (`feat/<spec-id>`) in every repository involved,
  **including `Spec/`**. Implements against the contract with TDD, commits and
  pushes. Ends at `In review`; **it does not open a pull request, does not merge,
  does not delete branches**.

**Fluid transition, visible boundary.** Moving between `/spec` and `/build` is
**fluid and context-driven**, and the agent **announces it**. The boundary stays
**visible without being awkward**: the agent always **names the active mode** and
**never erases the boundary silently** — it does not implement disguised as spec
work, nor redesign the spec disguised as build work. The **real gates** are
**approving the spec** (`Draft → Ready`) and **integration by pull request**;
**switching modes is not a gate**. Parallelism happens **between different
specs**, never within the same feature.

### 6.1 PO Mode — upstream of the flow, optional

The flow still runs in **two** modes; nothing above changes. **PO Mode** (`/po`)
is **not a third step**: it operates the **origins** zone that section 2 already
declares to be *outside* development.

| Mode | Answers | Delivers | Part of the flow? |
|---|---|---|---|
| **PO** (`/po`) | the *for whom* and the *why* | stories in `Spec/stories/` | **No** — upstream origin |
| **Spec** (`/spec`) | the *what* | a spec in `Draft` | Yes |
| **Build** (`/build` + `/cierre`) | the *how* | a feature `In review` → `Implemented` | Yes |

- **Optional by construction.** If `/po` is never invoked, the method operates
  identically.
- **Explicit entry only — the deliberate exception to the fluid transition.** PO
  Mode is **not entered by context**. That is a decision, not an oversight: a
  mode declared *outside* the flow that the agent could activate on its own would,
  with use, become a **de facto step**. Explicit invocation is what makes
  "optional" true in **behaviour** and not only in documentation.
- **Its own boundary, narrower than Spec Mode's:** it writes **only in
  `Spec/stories/`**; it does not create specs. On reaching that boundary it
  **stops and points** to `/spec`.
- **It adds no gates.**

## 7. Spec states

`Draft` → `Ready` → `In progress` → `In review` → `Implemented` (plus `Paused`,
outside the cycle). The step `Draft → Ready` is **authorised by the human**.

## 8. Branches: the agent creates, the human integrates

The agent **creates** feature branches, **commits** and **pushes** to them. The
irreversible, outward-facing boundary — **merging into the base** — is **always
human** and is not delegated.

- **Agent (always):** create the branch, commit and push to the feature branch;
  never to `main`/`master`.
- **Stable branch identity from `/spec`.** The branch name
  (`feat/<project-prefix>-<featureId>`) derives from the `featureId` assigned when
  writing — there is no number to reconcile and no race between parallel authors.
- **Human (always):** **merge** into the base and delete the **remote** branch.
- **Configurable per project** (`version_management`, chosen at init): who
  **opens the pull request**, **which integration branch** it targets, and who
  **deletes merged local branches**. **Merging is never configurable.**
- **The pull request target need not be `main`.** What is **invariant** is that
  **a human merges**; which branch the request targets is adaptable.
- **Multi-repo: one pull request per repository, merged together.** The method
  **warns** about cross-repository atomicity; it does not enforce it.
- **The pull request body accompanies EVERY pull request.** Closing always builds
  the body with real data, **before and independently of** how the request is
  opened. Opening is **host-agnostic**: where the agent can, it opens with that
  body; otherwise it **hands off** the comparison URL **and the filled body**.
  **Never the URL alone.**
- **git (and a remote) are prerequisites of this layer.** A directory **without
  git** falls outside the versioning layer: its changes are **written in place**
  but are not branched or reviewed, and the method **says so** — it never
  excludes it silently.

### 8.1 Commit message convention

The commit message **format** is an **invariant** of the method (unlike pull
request authorship or branch cleanup): every commit on a feature branch follows
the convention vendorised in `Spec/methodology/COMMIT_TEMPLATE.md` —
`<type>(<prefix>-<featureId>): <summary>` with a mandatory `Spec:` trailer and a
closed set of types (`feat`/`fix`/`test`/`refactor`/`docs`/`chore`). The **closing
commit** of the cycle adds an `Accepted criteria` block listing the verified
criteria from the spec's section 8. **There is no automatic enforcement** (no
`commit-msg` hook).

**Authoring vs. the feature cycle.** Spec authoring (`/spec`) may cover several
specs and uses a **freely named authoring branch**. The **shared name** derived
from the `featureId` is reserved for the **build/closing cycle** branch — the one
that updates the spec's state in its own document — which `/build` creates in
every repository involved, **including `Spec/`**. One collaborator per branch.

## 9. Global rules

1. **Consistency over creativity**: new code is indistinguishable from each
   repository's **decided canon**, not from legacy by inertia. Creativity is
   bounded: the agent **proposes at the gate**, it does not invent during
   implementation.
2. **Bounded scope**: nothing the spec did not ask for.
3. **TDD**: the test before the production code; no feature closes red.
4. **No secrets** in `Spec/` (credentials, internal hosts, tokens).
5. **Traceability**: every spec references its origin and its contract endpoints.
6. **Integration only by pull request**: nothing enters `main`/`master` by direct
   commit; everything passes through a pull request whose merge is a human
   responsibility.
7. **Responsibility map (descriptive)**: each layer's architecture declares where
   each responsibility lives, extracted from real code. New code respects it;
   `/build` **warns** (consultatively) on deviations and records them as debt or
   exceptions.

## 10. Invariant vs. adaptable

The method — this document, the flow, the modes, the states, the document
hierarchy — is **invariant**. The **architectures** (stack-dependent), the
**domain** and the **contract** adapt per project.
