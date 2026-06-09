# Shared prompt scaffolding

Every prompt version starts from the same skeleton and adds a *technique* on top. This file documents what each prompt is allowed to assume.

## Placeholders

- `{{DOCUMENT_TEXT}}` — replaced by the raw document text at call time.
- (no other placeholders — eval harness keeps it simple)

## Output contract

Every prompt must instruct the model to return **JSON only**. No prose, no markdown fences, no comments. The harness has fallback parsers (fenced blocks, first `{...}` substring) for robustness, but a well-behaved response is direct JSON.

## Document types

The same prompt is used for all three document types (invoice, receipt, resume). The model is expected to infer the type from the content and return whatever fields apply. The schema is **not** specified in the prompt for v1; it is included from v2 onwards as a deliberate variable.

## What we're measuring

- Whether the model returns valid JSON
- Whether the structured fields match ground truth
- Token efficiency (cost per document)
- Latency

That's it. Prompts that do clever things (multi-step extraction, retry on parse failure, etc.) belong in a separate harness — this one tests *single-shot extraction*.
