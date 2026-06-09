# Results — June 2026 (placeholder)

This is where the first round of benchmark results will land. Until then it's empty.

## Planned scope

- **Models:** claude-sonnet-4-5, claude-haiku-4-5, claude-opus-4, gpt-4o-2024-11-20, gpt-4o-mini-2024-07-18, gpt-5, gemini-2.5-pro
- **Prompts:** v1_baseline, v2_structured, v3_few_shot, v4_cot
- **Dataset:** the 7 synthetic documents shipped with v0.1 + 50 real (anonymized) Portuguese documents (TBD)

## Questions to answer

1. **For Portuguese invoices, what's the highest-F1 cheap model?** (i.e. minimum cost × highest F1)
2. **Does few-shot beat structured-schema-in-prompt for cost-constrained models?**
3. **Where does CoT help and where does it hurt?** (Latency cost vs accuracy gain)
4. **What's the variance across 5 runs of the same call?** (Provider-side non-determinism)
5. **Which model handles the comma-decimal Portuguese number format with no prompt hints?**

## Writeup

When results land, they'll go in:

- `results/charts/<date>-macro-f1.png`
- `results/charts/<date>-cost-vs-f1.png`
- This file, expanded with findings
- A blog post at miguelborges.dev/blog/extraction-evals

Cross-link both ways.
