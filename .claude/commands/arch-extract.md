You generate a `<DIR>_ARCHITECTURE.md` for the given directory, **extracted from its real code**. The goal: the document should let someone write code indistinguishable from the original author's.

This does **not** invent an ideal architecture. It *documents the one that exists*.

**If the directory is empty, stop.** This recipe is for existing code, and that restriction is what makes the document binding. What is missing is not the recipe — it is the code.

## Principles (non-negotiable)
1. **Descriptive by default; proposals at the gate.** What is documented is extracted from real code. You **may propose** a better alternative — labelled as a **proposal**, with its reasoning and trade-off — but **never impose it** or slip it into the document without a human decision.
2. **Generic examples** (`{Entity}`, `{Resource}`, `{Component}`), never business terms. The concrete domain lives in `DOMAIN.md`.
3. **Architecture is the "how".** The inventory of domain entities does not belong here.
4. **Where the code contradicts itself, do not choose for the human.** Stop and ask which convention to fix as canonical. Documenting two "official" forms is worse than asking.
5. **Distinguish canonical from legacy or demo.** Mark inherited patterns "do not replicate".
6. **Read, do not skim.** Representative units are read in full.

## Recipe
1. **Detect the stack** from manifests and the shape of the repository: language, framework, test runner, and the **migration mechanism** — a concrete framework, or "none", which activates the `.sql` fallback in `Spec/methodology/MIGRATION.sql.md`.
2. **Map the structure.** Find the recurring unit of work and what repeats N times — what repeats is the pattern worth documenting.
3. **Find the composition root / entry point.** How it starts, what shared instances exist, what runs at import time. "There is none" is a valid and informative answer.
4. **Sample 2–4 representative files and read them completely.**
5. **Extract conventions**: naming, file layout, where logic lives (distil into the responsibility map, section 8.1), return and error handling, configuration, tests.
6. **Fix the canon with the human** wherever the code contradicts itself. Present the evidence (file A versus file B), the observed candidates, and optionally a labelled proposal. Record the **decided canon** and mark the other form "do not replicate". For a systemic inconsistency, group by class with a count and settle it **once**.
7. **Write the document** following `Spec/methodology/ARCHITECTURE.skeleton.md`. Head it with: "Every pattern here is extracted from the real code in `<path>`."
8. **Confirm with the human** and iterate before considering it closed.

## Output
- Write to `Spec/<DIR>_ARCHITECTURE.md`.
- **Never overwrite silently:** if the document exists, stop and show what would change. A hand-curated document is worth more than a fresh pass.
- **Optional by-product:** collect domain entities you encounter as candidates for `DOMAIN.md` — but keep them out of the architecture document.
