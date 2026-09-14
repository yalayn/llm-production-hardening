# llm-production-hardening

> **Incomplete.** This repository is being built in the open, one piece at a time.
> What exists today is the naive implementation, a 50-case golden dataset, a run
> harness, and the section below. The hardened implementation, the comparative
> table and the rest of this README are still to come.

## What breaks in v1 and why

`v1-naive` is the ordinary way to do this: one prompt asking for JSON, and
`json.loads` on the reply. No schema validation, no retry, no timeout, no budget,
no cache, no fallback, no structured logging, no kill switch. It is written the
way a competent engineer writes it on a Friday afternoon, and it is not
exaggerated for effect.

It was run twice against 50 support tickets, using `claude-sonnet-5`, on
2026-09-08 and 2026-09-13. Both runs are reproducible from this repository.

---

### 1. The model was polite, and the feature went down

**Ticket**

> You charged me twice for invoice INV-4471 this morning. Please fix it.

**What the model actually returned**

<pre>
```json
{
  "category": "billing",
  "urgency": "high",
  "entities": ["INV-4471"],
  "suggested_action": "Verify the duplicate charge on INV-4471 and process a refund."
}
```
</pre>

**What the code did with it**

```
File "v1_naive/extractor.py", line 40, in extract_ticket
    return json.loads(block.text)
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

The answer is correct. Every field is right. The integration still fell over,
because three backticks arrived before the first brace.

**45 of 48** replies came wrapped in a code fence. Not 48 of 48 — and that is the
part worth sitting with. Test this by hand once, land on one of the three that
came back bare, and you ship something that fails most of your traffic.

Overall: **47 of 50** cases produced no usable result.

---

### 2. The code read the wrong part of the response

This one is not a weakness of the naive approach. It is what happens to correct
code when a provider starts replying differently, and it is reported separately
because none of the hardening below repairs it.

The first run used the pattern that every tutorial and SDK example used for
years:

```python
response.content[0].text
```

On a model that reasons by default, index 0 is a thinking block, not the answer.

```
AttributeError: 'ThinkingBlock' object has no attribute 'text'
```

Where the block existed but carried no text, `json.loads("")` raised the same
decode error as above — which is how this masqueraded as a parsing problem until
the raw replies were recorded.

**43 of 50** cases died there, and **45 of 50** failed overall in that run. Again
it was intermittent: the model does not always reason, so five cases passed.

Nobody edited this code for it to break. The model changed underneath it.

---

### 3. Empty input never reached the model

Two tickets in the dataset are empty or whitespace. Both were rejected before
inference:

```
anthropic.BadRequestError: Error code: 400 - messages.0: user messages must
have non-empty content
```

**This one is not a v1 problem.** The hardened version has it too, at the time of
writing. Validating input before paying for a call is a production practice that
neither implementation has yet, and pretending otherwise would be dishonest about
where the line actually falls.

---

### What these runs cannot tell you

**Accuracy is not measurable from them.** With 47 of 50 failing to parse, almost
nothing reached the point of being compared against the expected answer. The
comparison of *correctness* needs the hardened version to exist. What these runs
measure is something narrower and, for a production system, more immediate: how
often the integration produced nothing at all.

**The naive version got the prompt injections right.** Two of its three passes
were injection attempts — including one embedding a complete, well-formed JSON
answer designed to be copied. It ignored the instruction and classified the real
complaint correctly, both times. The model resisted on its own, with no help from
the code around it. That is a point against the argument this repository is
making, and it belongs here rather than in a footnote.

**None of this is permanent.** These are observations about one model on two
dates, not laws. If the provider stops wrapping replies in fences tomorrow, the
first failure disappears — and the reason to validate what arrives does not.
