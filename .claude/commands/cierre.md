You run the **Closing Sequence** for a feature that is implemented and **approved by the human**. You do not build or redesign: you close.

> The filename stays `cierre` on purpose. The command is identical across this
> author's other projects, and one renamed command is a worse inconsistency than
> one untranslated filename. The content is English like everything else.

## Entry gate (verify before touching anything)
- The spec must be **`In review`** in its own header. If it is `Ready` or `In progress`, stop — `/build` has not finished. If it is `Draft`, that is `/spec`.
- You must be on the feature branch `feat/SPEC-<featureId>`. **Never** close from `main`.
- **Requires explicit human approval** of the acceptance criteria. The human invokes `/cierre`; do not infer approval from the conversation.
- **No API documentation gate**: this project has no contract, so the step does not apply.

## Sequence (in order)
1. **Final commit `In review` → `Implemented`.** Update the state in the spec document with its date, and commit it following `Spec/methodology/COMMIT_TEMPLATE.md` (type `docs`, `Spec:` trailer).
2. **Push** the branch.
3. **Resolve the integration base.** Precedence: `--base <branch>` passed to `/cierre` → the spec's `Integration base` field → `version_management.integration_base` (`main`). If the resolved branch does not exist, say so and offer to create it **with confirmation** — never open a pull request against an invalid target.
4. **Build the pull request body, always.** Fill `Spec/methodology/PR_TEMPLATE.md` with real data: the spec, the changes, the criteria from section 8, the state of the tests, and the confirmation that no test reached the network. This happens **before and independently of** how the request is opened.
   - `version_management.pull_request.author` is **`human`** in this project → **hand off**: give the human the comparison path (`main...feat/SPEC-<featureId>`) **and the filled body**, ready to paste. **Never the URL alone.**
   - **No remote is configured yet.** Say so plainly: the branch cannot be pushed and the pull request cannot be opened until one exists. Do not present the hand-off as if it were complete.
5. **Opportunistic cleanup** is disabled (`cleanup_local_after_merge: false`). Skip it.

## Rules and stop
- Single repository, so a single pull request. The final commit lives in the same repository and travels inside it.
- **Merging and deleting the branch — local or remote — are always human.** You do not merge and you do not delete this feature's branch.
- You finish by **reporting** the hand-off and waiting for the human merge.
