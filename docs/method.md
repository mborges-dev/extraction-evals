# Method

How the eval harness actually works.

## The eval matrix

The eval is a Cartesian product: **models × prompts × documents**. Each cell in the grid is one API call, one parsed extraction, one row in the output CSV.

```
   v1_baseline  v2_structured  v3_few_shot  v4_cot
   ───────────  ─────────────  ───────────  ──────
   claude-sonnet  •              •             •         •
   claude-haiku   •              •             •         •
   gpt-4o          •              •             •         •
   gpt-4o-mini    •              •             •         •
   gemini-2.5     •              •             •         •
```

For each cell, every document in `dataset/` is processed. With 7 documents and 5 models × 4 prompts, that's 140 calls per run.

## What the harness records

For each call:

- The model name and prompt version
- The document id and type
- Token usage (input, output, cache read, cache write)
- Latency (wall-clock ms)
- Raw response text (truncated to 200 chars in CSV; full text discarded — too verbose)
- Parsed JSON (or `null` if parsing failed)
- Error message (if the API call failed)

Then it computes three correctness metrics by comparing the parsed JSON against the ground-truth JSON:

1. **Exact match (0 or 1):** entire JSON equal after normalization
2. **Field accuracy (0..1):** fraction of top-level fields that match
3. **Macro F1 (0..1):** mean per-field F1 across all top-level fields

And one cost metric:

4. **Cost USD:** token counts × per-million-token prices (defined per model in `src/runners/<provider>.py`)

## Normalization

Before comparing, both sides are normalized:

- Strings: stripped, lowercased
- Numbers: stringified (so `1.00` == `1.0`)
- `None`: empty string
- Lists: recursively normalized
- Dicts: recursively normalized

This is intentionally lenient. The harness is not testing the model's ability to match casing; it's testing extraction correctness.

**Edge case:** for ground truth I omit empty/null fields (see `dataset/README.md`). The normalizer treats omitted-field == empty-field == 0, so models that include `"due_date": null` and ground truths that omit `due_date` both score as match.

## Parser robustness

The raw response goes through a fallback chain to extract JSON:

1. Try `json.loads(raw_text)` directly
2. Try ```` ```json … ``` ```` fenced block
3. Try any ```` ``` … ``` ```` fenced block
4. Try the first `{...}` substring

If all fail, the call counts as a parse failure (F1 = 0). This matters because some models ignore "return JSON only" instructions and add prose.

## Per-field F1

For lists (e.g. `line_items`, `skills`), F1 is set-based:
- Convert both lists to sets of stringified items
- Precision = |intersection| / |extracted|
- Recall = |intersection| / |ground_truth|
- F1 = 2·P·R / (P+R)

This means line-item *order* doesn't matter, and partial matches are scored. For invoice line items where order may matter operationally, you should use a stricter custom metric (PRs welcome).

For scalars, F1 is binary (1.0 or 0.0).

## What this harness deliberately does NOT do

- **Multi-step extraction** — single-shot only. If you want refine-then-extract loops, fork.
- **Retry on parse failure** — failures count as zeros. Real production code would retry.
- **OCR** — the dataset stores extracted text. PDF/image handling is your problem before the harness sees it.
- **Bipartite matching of line items** — see above.
- **Fine-tuned models** — only public APIs.
- **Streaming** — uses non-streaming endpoints. Latency reflects full-response wait.

These omissions are deliberate. The harness measures the *vanilla* one-call cost and accuracy of each model × prompt combination, which is what you most often need to choose between options. Production stacks add layers on top.

## Reproducibility

Same dataset + same prompts + same models + temperature=0 (default in runners) = same results, modulo provider-side non-determinism (which is non-zero for all providers and worth measuring with a few re-runs).

The harness loads documents in alphabetical order of `<id>.txt` to keep the order stable.

The CSV includes every input parameter so you can reconstruct exactly what was run.
