<!--
SQL MIGRATION FALLBACK -- the shape the method defines when a project has no
migration framework of its own.
-->

# SQL migration fallback

**Inert in this project.** There is no database: persistence is out of scope, and
`methodology.config.yaml` declares no migration mechanism. This file exists so
that the references to it from `/build` and from the spec template resolve to
something real rather than to nothing.

If persistence is ever introduced, it arrives through its own spec, whose section
3 decides the schema change, and the shape below applies.

## Shape

One file per migration, named `<UTC timestamp>_<snake_case description>.sql`,
holding a paired `up` and `down`:

```sql
-- migrate:up
<<forward statements>>

-- migrate:down
<<statements that undo the structure above, in reverse order>>
```

## Rules

- **Every migration is reversible in schema.** The `down` restores the
  **structure**; it does not resurrect **data**. A `down` that cannot restore the
  structure means the `up` was too large and should be split.
- **The agent produces and pushes the migration. It never runs it against a real
  database.** That is a human gate, the same irreversible outward-facing boundary
  as merging.
- **A ledger table records what has been applied.** It must not be named
  `migrations` if any framework in the workspace already claims that name.
- **Backfilling a new non-nullable column over existing rows** takes one of two
  routes, decided in the spec, never improvised: **A** — add and update together,
  for small tables; **B** — expand, backfill, then contract, for large tables or
  batched work.
- **No secrets**: no credentials, no internal hostnames, in any migration.
