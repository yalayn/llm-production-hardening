# ARCHITECTURE — the Python codebase

> Every pattern here is extracted from the real code. It describes what exists,
> not what would be ideal. Examples are generic (`{Model}`, `{Field}`); the
> concrete domain lives in `DOMAIN.md`.

| Field | Value |
|---|---|
| **Covers** | All Python in this repository: `v1_naive/`, `v2_hardened/`, `evals/`, `tests/` |
| **Role** | One codebase, one set of conventions, two modules held to different canons |
| **Provenance** | Extracted from the project's own code |
| **Extracted** | 2026-08-20 · rescoped from `V2_HARDENED_ARCHITECTURE.md` |

> **Why one document and not one per folder.** The method's unit is a body of code
> with its own way of being written, not a top-level folder. These modules share a
> language, a virtual environment, a `pyproject.toml`, a test root and every
> convention below. They differ in exactly one declared dimension, and that
> dimension is recorded here as canon rather than split across documents that would
> repeat each other.

---

## 0. The deliberate divergence

Two modules implement the same operation and are held to **different** canons.
That difference is the repository's entire reason to exist, so it is canon — not
drift, not debt, not something to reconcile.

| | `v1_naive` | `v2_hardened` |
|---|---|---|
| Output shape | Described in prose inside the prompt | A Pydantic model with `extra="forbid"` |
| Response handling | `json.loads`, returned unchecked | Validated on arrival, always |
| Provider seam | None — a `client` parameter with a real default | A one-method `Protocol` returning raw text |
| Failure handling | Propagates to the caller | Arrives under its own specs |

**Adding a safety net to `v1_naive` is a defect, not an improvement.** If a future
change makes the two modules converge, the comparison silently stops measuring
anything. Neither module imports the other; that independence is enforced by a
test, not by good intentions.

## 1. Stack

| Concern | Choice |
|---|---|
| Language | Python 3.9 (`requires-python = ">=3.9"`) |
| Validation | Pydantic v2 (`2.13.4`) — `v2_hardened` only |
| LLM provider | Anthropic SDK (`0.125.0`), model `claude-sonnet-5` |
| Tests | pytest (`8.4.2`) |
| Web framework | None. This is a library, not a service |
| Persistence | None |
| Migrations | None — there is no database |

Dependencies are **pinned to exact versions**, not ranges. The project exists to
compare two implementations; a comparison across drifting library versions
measures nothing.

## 2. Structure

```
v1_naive/       the typical implementation        (implemented)
v2_hardened/    the production-hardened one       (vertical implemented)
evals/          the comparison harness            (planned)
data/           the golden dataset -- data, not code
tests/          one test root for all of the above
```

Flat packages. No sub-packages, no layers. Adding a module means asking which
existing module it sits beside, not creating a tier.

Imports are **absolute** (`from v2_hardened.client import LLMClient`), never
relative: a reader can tell where a name comes from without knowing the file's own
location.

## 3. Startup / composition

**There is no entrypoint, no app factory and no shared global state.** Nothing is
constructed at import time; importing any package performs no side effects.

Composition happens **at the call site** — the caller builds a client and passes
it in. Because the dependency is passed rather than reached for, no test needs to
patch a module or set an environment variable to stay offline.

The two modules differ in how the seam is shaped (section 0), not in whether one
exists.

## 4. Core patterns

### 4.1 The contract is a Pydantic model with `extra="forbid"` — `v2_hardened`

`extra="forbid"` is not stylistic: it is what makes `model_json_schema()` emit
`additionalProperties: false`, which is what lets the provider **constrain** the
response rather than merely be asked for it.

Closed sets are `Literal` aliases at module level, not `Enum` classes. `Literal`
inlines as an `enum` array in the JSON Schema; an `Enum` produces `$ref`/`$defs`
indirection that buys nothing and makes a request payload harder to read.

Every field carries `Field(description=...)`. That description travels inside the
schema to the model, so it is prompt surface, not a code comment.

### 4.2 The provider sits behind a one-method `Protocol` — `v2_hardened`

```python
class {Client}(Protocol):
    def complete(self, *, system: str, user: str, json_schema: Dict[str, Any]) -> str: ...
```

Two properties are deliberate and must survive:

- **Keyword-only arguments.** Call sites read as prose; argument order cannot be
  silently wrong.
- **It returns raw text, not a validated object.** This is why the seam is placed
  here at all. A stub can return malformed JSON, a value the schema forbids, or
  raise a provider error, and the validation and recovery logic under test still
  runs for real.

Transport errors are **not** swallowed at this layer.

### 4.3 Validate on arrival, even when the provider was constrained — `v2_hardened`

The real client sends `output_config={"format": {"type": "json_schema", ...}}`,
and the caller validates the result anyway.

Not redundancy. A response can satisfy a schema and still be wrong — an invented
category is well-typed — and a provider can always return something the schema did
not allow. Defence in depth is the pattern; do not remove either half.

### 4.4 No seam of its own — `v1_naive`

The client is a parameter with a real default (`client=None` builds one). No
Protocol, no abstraction. A test has to fake the SDK object's shape rather than a
clean interface, and **that awkwardness is one of the things being measured** —
not a flaw to fix.

### 4.5 Absence is a pattern too — `v2_hardened`

Retries, timeouts, cost budget, caching, deterministic fallback, structured
logging and the feature flag are **deliberately not here yet**; each arrives under
its own spec. Do not add any of them opportunistically while working on something
else.

## 5. Environment configuration

There is no config module and no `.env` loading. The single environment-derived
value is the API credential, resolved by the Anthropic SDK from the environment
when the client is constructed with no arguments.

**No credential is ever read, stored, logged or passed as an argument by this
code.** `.env` is git-ignored.

## 6. Communication / contract

No inter-layer contract file: a single layer with no runtime communication between
parts, so `principles.md` section 4 omits the slot and with it the API
documentation step.

The only external protocol is the Anthropic Messages API. Each module reaches it
through exactly one call site.

## 7. Session / security

No sessions, no authentication, no authorisation — a library with no network
surface of its own. Two standing rules:

- **Credentials never enter the source tree**, in any form, tests included.
- **Ticket text is untrusted input.** It comes from whoever wrote the ticket and
  is handed to a language model. Treating it as data rather than instruction is an
  open design question at the time of writing, not a solved one.

## 8. Implementation rules

- Pin new dependencies to exact versions.
- Type-annotate every public function signature.
- Prefer a module-level constant over a literal buried in a call.
- Never let a bare `next()`/`StopIteration` escape a boundary: when a response
  shape is wrong, raise an error that names what was wrong.
- Every module opens with a docstring saying what it is for, and where a decision
  is non-obvious, why it is that way rather than the alternative.

### 8.1 Responsibility map

| Core responsibility | Canonical location | What it must not do |
|---|---|---|
| Define the output shape | `v2_hardened/schema.py` | Talk to the provider; know a prompt exists |
| Talk to the provider | `v2_hardened/client.py` | Validate; interpret; decide about failures |
| Compose, own the prompt, validate | `v2_hardened/extractor.py` | Build an SDK request; read the environment |
| The naive path, end to end | `v1_naive/extractor.py` | Import anything from `v2_hardened` |
| Compare the two | `evals/` | Define domain shapes; alter either implementation |
| Simulate provider behaviour | test stubs | Reach the network under any condition |

A responsibility landing outside its canonical location is a deviation: reported
at audit time and, if accepted, recorded in 8.2 — never adopted silently.

### 8.2 Debt and accepted exceptions

| Item | Why it is accepted | When it is revisited |
|---|---|---|
| `LLMClient` is a `Protocol` with no static type checker configured | Nothing verifies conformance mechanically; the tests exercising it do. A type checker is tooling this project's scope excludes | If a second real implementation appears |
| Prompt text lives inline in each extractor | One prompt per module, one call site — a prompt module would be indirection with nothing to hold | When a module needs a second prompt |
| Tests live at the repository root | The eval harness imports several modules; one test root keeps one obvious place to look | If the packages become independently installable |

## 9. Running locally

```
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

There is nothing to "run": no server, no CLI. The only executable behaviour is the
test suite.

**Reaching the real provider costs money and is a human action.** No code here may
issue a live request as part of a test, a build step, or an automated check.

## 10. Tests (TDD)

| Aspect | Convention |
|---|---|
| Runner | pytest |
| Location | `tests/`, at the repository root |
| Command | `.venv/bin/python -m pytest` |
| Path setup | `pythonpath = ["."]` in `pyproject.toml` — never `sys.path` edits in code |
| Isolation | Stubs. No network, ever |
| Naming | `test_<behaviour_in_words>` — a sentence, not a method name |

The test written first must fail for the intended reason before the production
code exists. A suite that passes against deliberately broken code is not a suite;
when a test's value is not obvious, break what it covers and confirm it goes red.

Stubs record what they were called with, so a test can assert on the **request**
as well as the response.
