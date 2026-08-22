<!--
SPEC TEMPLATE -- copy to Spec/feature/SPEC-<featureId>.md and fill in.
Delete the HTML comments and the notes between <<>> when done.
Rules live in MASTER_PLAN.md. Nothing is implemented until the spec is `Ready`.

Section numbers are STABLE. Other documents cite "section 8" (acceptance
criteria), "section 9" (risks) and "section 11" (history) by number, so a
section that does not apply is marked N/A rather than removed and renumbered.
-->

# Spec — SPEC-<featureId> <<Readable feature name>>

| Field | Value |
|---|---|
| **SPEC** | `SPEC-<featureId>` <<the spec's identity. Stable from the moment `/spec` assigns it; two identical featureIds collide as files, which is immediately visible>> |
| **featureId** | `<feature-id>` <<kebab-case, unique>> |
| **State** | 📝 `Draft` <<Draft · Ready · In progress · In review · Implemented · Paused — the single source of truth for state>> |
| **Author** | <<name>> |
| **Date** | <<YYYY-MM-DD — gives chronological order alongside `git log`, since the name carries no number>> |
| **Depends on** | <<previous SPEC-<featureId>, or "--">> |
| **Implementation directories** | `<names, from implementation_dirs in methodology.config.yaml>` <<which directories this spec touches. Governs which of sections 5-7 are completed and where `/build` creates a branch. "--" for a process-only spec that touches just `Spec/`>> |
| **Integration base** | `<branch>` <<optional override of `version_management.integration_base`. "--" uses the default>> |
| **Spends budget** | `yes` / `no` <<project-specific. `yes` means closing this spec requires a live provider run, which is a human action with a reported cost>> |

---

## 1. Problem and goal

<<What need this solves and for whom. Two to four sentences. No solution yet.>>

## 2. Scope

**Includes**
- <<item>>

**Excludes (out of scope)**
- <<item>>

## 3. Domain and data model

<<Entities involved. Reference what already exists in `DOMAIN.md` rather than
redefining it: reuse before creating.>>

| Entity | Key fields | Notes |
|---|---|---|
| `<entity>` | `<fields>` | <<new / existing / extends...>> |

**Schema change:** `no changes`.

> This project has no database — persistence is out of scope. If that ever
> changes, the schema change is decided **here**, and `/build` produces the
> migration with its paired `down` without applying it: applying it is a human
> gate (`methodology/principles.md` section 4.1).

## 4. API contract

**N/A for this project.** There is a single layer with no runtime communication
between parts, so `principles.md` section 4 omits the contract slot, and with it
the API documentation step. The section is kept so that section numbers stay
stable across documents.

The only external protocol is the provider API, and it is reached through exactly
one call site — see `V2_HARDENED_ARCHITECTURE.md` section 6.

## 5. <<Implementation directory A — e.g. v2_hardened>>

<<What is created or modified here. Read this directory's `*_ARCHITECTURE.md` to
design against the reality of the code. The spec does not modify that document --
that happens, if at all, during the `/build` audit or at closing.>>

## 6. <<Implementation directory B — e.g. evals>>

<<As above. If the directory is not in the header's list, write
`N/A -- outside the declared scope` rather than leaving the placeholder.>>

## 7. Behaviour walkthrough

<<This project has no user interface. Describe the developer-facing path instead:
what is called, with what, what comes back, and what happens on each failure mode
the feature is responsible for.>>

1. <<...>>

## 8. Acceptance criteria

<<Verifiable and binary. These are the basis of the Verification phase and of the
closing commit. Each one must be able to fail; if you cannot picture the case
where it does not hold, it is a wish, not a criterion.>>

- [ ] <<Given ... when ... then ...>>
- [ ] No test in this feature reaches the network or spends budget.

## 9. Risks and open decisions

| Topic | Decision / pending | Owner |
|---|---|---|
| <<...>> | <<...>> | <<...>> |

## 10. References

- Domain: `DOMAIN.md`
- Architectures: <<list of `*_ARCHITECTURE.md`>>
- Method: `methodology/principles.md`

## 11. History

<!-- Substantive turns only: course corrections, scope changes, discarded paths.
State transitions (Draft->Ready, Ready->In progress, ...) are NOT recorded here --
they are already commits, scoped to this spec and carrying a `Spec:` trailer, and
`git log` is their register. Without that cut, this section degenerates into a
shadow of the git log. -->

| Date | Change |
|---|---|
| <<YYYY-MM-DD>> | <<what changed course and why — not the state transition>> |
