# `Spec/` — the orchestrating authority

This directory governs how the rest of the repository is allowed to change. It is
not documentation *about* the project written after the fact; it is what
authorises the work before it happens.

If you are reading this repository to judge the engineering rather than to work on
it, the two files worth your time are [`MASTER_PLAN.md`](MASTER_PLAN.md) — how the
project is run — and [`V2_HARDENED_ARCHITECTURE.md`](V2_HARDENED_ARCHITECTURE.md) —
the binding description of how the code is written, extracted from the code itself.

## Layout

| Path | What it is |
|---|---|
| `MASTER_PLAN.md` | Orchestration: flow, gates, rules, conventions |
| `DOMAIN.md` | What exists in the domain |
| `V2_HARDENED_ARCHITECTURE.md` | How code is written in `v2_hardened/` — **binding** |
| `feature/` | One document per feature: identity, state, acceptance criteria, history |
| `methodology/` | The method itself: the manual and its templates |
| `stories/`, `prototype/` | Optional inputs. Unused here |
| `docs/USAGE.md` | How to operate the cycle day to day |

## The shape of it, in one paragraph

Nothing is implemented without an approved spec. The spec says *what*; the
architecture document says *how*; the agent proposes at the gates and does not
improvise in between. Three moments are human and are not delegated: approving the
spec before code exists, approving the acceptance criteria once it does, and
merging. A fourth applies to this project specifically — **spending budget against
a live provider is always a human action** (`MASTER_PLAN.md` section 7.1).

## About the language

This project is written entirely in English. The method it uses is authored in
Spanish, so everything under `methodology/` is a translation, kept deliberately as
a declared customisation. An update to the method reports its delta rather than
silently reverting these files.
