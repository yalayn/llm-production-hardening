# `stories/` — user stories

An **optional** input to the method. Stories describe the *for whom* and the
*why*; a spec describes the *what*. Nothing here is required for the flow to
operate, and this project has not used it: the requirements arrived as a written
brief instead.

## Convention

One file per sprint: `SPRINT-<YYYY-MM>-<sprintId>.md`, where `<YYYY-MM>` is the
starting month and `<sprintId>` is a lowercase kebab-case slug. No sequential
number — a number computed in parallel collides silently, whereas a repeated slug
collides as a file, which is immediately visible.

Specs cite stories by id: `stories/SPRINT-2026-08-hardening.md#HU-001`.

The template is `Spec/methodology/STORIES.template.md`. Authoring assistance is
`/po`, which is entered explicitly and never by context.
