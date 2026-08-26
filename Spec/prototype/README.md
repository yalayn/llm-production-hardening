# `prototype/` — interface prototypes

An **optional** input to the method, and **not applicable to this project**: there
is no user interface here. The folder is kept so that references from the spec
template resolve, and so the convention is documented if the project ever grows one.

## Convention

One folder per sprint: `SPRINT-<YYYY-MM>-<sprintId>/`, named to match its story
file exactly — that pairing is what links a prototype to its stories.

**Where a prototype exists, it is the source of truth for UI and interaction**,
taking precedence over the story, which owns the *what* and the *why*. Where none
exists, the spec's own sections carry that detail.
