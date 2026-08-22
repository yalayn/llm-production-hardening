# Operating the cycle

## The three commands

| Command | Answers | Leaves |
|---|---|---|
| `/spec` | the *what* | a spec at `Draft` |
| `/build` | the *how* | the feature at `In review`, branch pushed, no pull request |
| `/cierre` | closing | the closing commit and the pull request hand-off |

`/arch-extract` regenerates a directory's architecture document from its code.
`/po` writes user stories and is optional — this project has not used it.

## A full pass

**1 · Write the spec.**

```
/spec <what the feature should do>
```

Produces `Spec/feature/SPEC-<featureId>.md` at `Draft` on an authoring branch.
Read it. It is the cheapest moment in the cycle to disagree — no code exists yet,
so there is no sunk cost pulling the decision.

**2 · Approve it.** Change `State` to `Ready` in the spec's own header. This is a
human action; the agent will not do it.

**3 · Build.**

```
/build SPEC-<featureId>
```

Creates `feat/SPEC-<featureId>`, records `In progress`, audits the work against
the standing architecture, then implements test-first. It stops at `In review`
with the branch pushed and **no pull request open**.

If the audit raises a blocking warning, it pauses and presents a proposal. That is
a conversation to have, not a yes/no button.

**4 · Approve the criteria.** Read the diff against the spec's section 8.

**5 · Close.**

```
/cierre SPEC-<featureId>
```

Writes the closing commit with its `Accepted criteria` block and hands you the
comparison URL plus a filled-in pull request body.

**6 · Merge.** Yours, always.

## Running the tests

```bash
cd /Users/yordindarocha/Proyectos/llm-production-hardening && .venv/bin/python -m pytest -v
```

No test reaches the network. If one ever does, that is a defect regardless of
whether it passes.

## Spending budget

Nothing in this repository issues a live provider request automatically. When a
feature needs real numbers, the run is prepared for you and **you launch it**,
with its estimated cost stated first. Set the credential in your own shell:

```bash
export ANTHROPIC_API_KEY="your-key"
```

It is never written into the repository, and `.env` is git-ignored.

## Where things live when you get lost

- What state is everything in? — `grep -H "State" Spec/feature/*.md`
- Why is the code shaped like this? — `Spec/V2_HARDENED_ARCHITECTURE.md`
- Why was that decided? — section 9 and section 11 of the relevant spec
- What are the rules? — `Spec/MASTER_PLAN.md`, and the theory in
  `Spec/methodology/principles.md`
