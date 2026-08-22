# v2_hardened — Architecture

> Every pattern in this document is extracted from the real code in `v2_hardened/`.
> It describes what exists, not what would be ideal. Examples are generic
> (`{Model}`, `{Field}`); the concrete domain lives in `DOMAIN.md`.

| Field | Value |
|---|---|
| **Directory** | `v2_hardened/` |
| **Role** | The production-hardened implementation of the extraction feature |
| **Provenance** | Extracted from the project's own code |
| **Extracted** | 2026-08-20 |

---

## 1. Stack

| Concern | Choice |
|---|---|
| Language | Python 3.9 (`requires-python = ">=3.9"`) |
| Validation | Pydantic v2 (`2.13.4`) |
| LLM provider | Anthropic SDK (`0.125.0`), model `claude-sonnet-5` |
| Tests | pytest (`8.4.2`) |
| Web framework | None. This is a library, not a service |
| Persistence | None |
| Migrations | None — there is no database, so no migration mechanism applies |
| Containers | None |

Dependencies are **pinned to exact versions**, not ranges. The whole project
exists to compare two implementations; a comparison across drifting library
versions measures nothing.

## 2. Module structure

Flat package. Three modules, each with one responsibility, no sub-packages:

```
v2_hardened/
  __init__.py     empty -- the package exposes nothing implicitly
  schema.py       the output contract
  client.py       the seam with the LLM provider
  extractor.py    the operation that composes the two
tests/            at repository root, not inside the package
```

Dependency direction is one-way and shallow: `extractor` imports `schema` and
`client`; neither imports `extractor`. Adding a module means asking which of
these three it sits beside, not creating a layer.

Imports are absolute (`from v2_hardened.client import LLMClient`), never
relative. A reader can tell where a name comes from without knowing the file's
own location.

## 3. Startup / composition

**There is no entrypoint, no app factory and no shared global state.** Nothing
is constructed at import time, and importing the package performs no side
effects.

Composition happens **at the call site**: the caller builds a client and passes
it in.

```python
client = AnthropicClient()
result = extract_ticket(text, client)
```

This is the single most load-bearing decision in the directory. Because the
dependency is passed rather than reached for, no test needs to patch a module,
monkeypatch an import, or set an environment variable to stay offline.

## 4. Core patterns

### 4.1 The contract is a Pydantic model with `extra="forbid"`

`{Model}` subclasses `BaseModel` and sets `model_config = ConfigDict(extra="forbid")`.
That is not stylistic: it is what makes `model_json_schema()` emit
`additionalProperties: false`, which is what lets the provider **constrain** the
response instead of merely being asked for it.

Closed sets are `Literal` aliases declared at module level, not `Enum` classes.
`Literal` inlines as an `enum` array in the JSON Schema; an `Enum` produces
`$ref`/`$defs` indirection that buys nothing and makes a request payload harder
to read.

Every field carries `Field(description=...)`. The description travels inside the
schema to the model, so it is prompt surface, not a code comment.

### 4.2 The provider sits behind a one-method `Protocol` returning raw text

```python
class {Client}(Protocol):
    def complete(self, *, system: str, user: str, json_schema: Dict[str, Any]) -> str: ...
```

Two properties are deliberate and must be preserved:

- **Keyword-only arguments.** Call sites read as prose and argument order can
  never be silently wrong.
- **It returns raw text, not a validated object.** This is the reason the seam
  is placed here at all. A stub can return malformed JSON, a value the schema
  forbids, or raise a provider error, and the validation and recovery logic
  under test still runs for real. A seam placed above the operation would return
  a finished object and skip the exact behaviour this project exists to measure.

Transport errors are **not** swallowed at this layer. The Protocol's contract is
that it raises whatever the provider raises; deciding what to do about it
belongs to the caller.

### 4.3 Validate on arrival, even when the provider was constrained

The real client sends the schema as a response-format constraint:

```python
output_config={"format": {"type": "json_schema", "schema": json_schema}}
```

and the caller validates the result anyway, with
`{Model}.model_validate_json(raw)`.

This is not redundancy. A response can satisfy a schema and still be wrong --
an invented category is well-typed -- and a provider can always return something
the schema did not allow. Defence in depth is the pattern; do not remove either
half.

### 4.4 Absence is a pattern too

The following are **deliberately not here yet**, each arriving under its own
spec: retries, timeouts, cost budget, caching, deterministic fallback,
structured logging, feature flag. Do not add any of them opportunistically while
working on something else. Their absence is the baseline being measured.

## 5. Environment configuration

There is no config module and no `.env` loading. The single environment-derived
value is the API credential, resolved by the Anthropic SDK itself from the
environment when `anthropic.Anthropic()` is constructed with no arguments.

**No credential is ever read, stored, logged or passed as an argument by this
code.** `.env` is git-ignored. A future need for configuration should be weighed
against how much of this directory's simplicity it costs.

## 6. Communication / contract

No inter-layer contract file. This project has a single layer with no runtime
communication between parts, so `principles.md` section 4 omits the contract
slot, and with it the API documentation step.

The only external protocol is the Anthropic Messages API, reached through
exactly one call site: `{Client}.complete`. Anything the API surface changes
should be a change to that one method.

## 7. Session / security

No sessions, no authentication, no authorization — this is a library with no
network surface of its own.

Two standing rules that any new code must respect:

- **Credentials never enter the source tree**, in any form, including tests and
  fixtures.
- **Ticket text is untrusted input.** It comes from whoever wrote the ticket and
  is passed to a language model. Treating it as data rather than instruction is
  an open design question at the time of writing, not a solved one.

## 8. Implementation rules

- Pin new dependencies to exact versions.
- Type-annotate every public function signature.
- Prefer a module-level constant over a literal buried in a call.
- Never raise a bare `next()`/`StopIteration` at a boundary: when a response
  shape is not what was expected, raise an error that names what was wrong.
- Every module opens with a docstring that says what it is for, and where a
  decision is non-obvious, why it is that way rather than the alternative.

### 8.1 Responsibility map

| Core responsibility | Canonical location | What it must not do |
|---|---|---|
| Define the output shape | `schema.py` | Talk to the provider; know a prompt exists |
| Talk to the provider | `client.py` | Validate; interpret; decide about failures |
| Compose the operation, own the prompt, validate | `extractor.py` | Build an SDK request; read the environment |
| Simulate provider behaviour | test stubs | Reach the network under any condition |

A responsibility landing outside its canonical location is a deviation. It is
reported at audit time and, if accepted, recorded in 8.2 — never adopted
silently.

### 8.2 Debt and accepted exceptions

| Item | Why it is accepted | When it is revisited |
|---|---|---|
| `LLMClient` is a `Protocol` with no static type checker configured | Nothing verifies that an implementation satisfies it; conformance is checked by the tests exercising it, not by a tool. Adding a type checker is tooling this project's scope excludes | If a second real implementation appears |
| Prompt text lives inline in `extractor.py` | One prompt, one call site — a prompt module would be indirection with nothing to hold | When a second prompt exists |
| Tests live at the repository root, not beside the package | The eval harness will import several implementations; a single test root keeps one obvious place to look | If the directories become independently installable |

## 9. Running locally

```
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

There is nothing to "run": no server, no CLI. The only executable behaviour is
the test suite.

**Reaching the real provider costs money and is a human action.** No code in
this repository may issue a live request as part of a test, a build step, or an
automated check.

## 10. Tests (TDD)

| Aspect | Convention |
|---|---|
| Runner | pytest |
| Location | `tests/`, at the repository root |
| Command | `.venv/bin/python -m pytest` |
| Path setup | `pythonpath = ["."]` in `pyproject.toml` — never `sys.path` edits in code |
| Isolation | A stub implementing the client Protocol. No network, ever |
| Naming | `test_<behaviour_in_words>` — a sentence, not a method name |

The test written first must fail for the intended reason before the production
code exists. A suite that passes against deliberately broken code is not a
suite; when a test's value is not obvious, break the thing it covers and confirm
it goes red.

Stubs record what they were called with, so a test can assert on the **request**
as well as the response — that is how "the provider was asked to constrain its
output" is verified at all.
