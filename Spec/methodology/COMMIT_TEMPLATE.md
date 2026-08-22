<!--
COMMIT MESSAGE CONVENTION.
Fixed structure for every agent commit on a feature branch. This file is a
reference, not something instantiated per commit: /build follows it when
composing each `git commit`.
-->

# Commit message convention

## Regular commit (any step of the cycle)

```
<type>(SPEC-<featureId>): <imperative summary, 72 characters or fewer, no full stop>

<optional body: what changes and why -- not how>

Spec: Spec/feature/SPEC-<featureId>.md
```

## Closing commit (the one that leaves the state at `In review`)

Adds the covered criteria on top of the block above:

```
Accepted criteria:
- <criterion 1, copied from the spec, section 8>
- <criterion 2>
```

## Rules

- **Closed set of types:** `feat` (new capability), `fix` (correction), `test`
  (the red step of TDD), `refactor`, `docs` (changes under `Spec/` or `docs/`),
  `chore` (configuration, housekeeping).
- **Scope** is `SPEC-<featureId>` — the spec id, greppable in `git log`.
- The `Spec:` trailer is **mandatory** on every commit of a feature branch.
- The `Accepted criteria` block belongs **exclusively to the closing commit**;
  intermediate commits do not carry it.
- This is an **invariant** convention of the method: not configurable per
  project, with no automatic enforcement (no `commit-msg` hook).
