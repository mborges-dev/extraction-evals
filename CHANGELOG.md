# Changelog

All notable changes to Extraction Evals documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] — 2026-06-09

Initial scaffold. The harness is end-to-end runnable with a small synthetic dataset.

### Added

- **Pydantic schemas** for three document types (invoice, receipt, resume), with Portuguese tax-format defaults
- **Loader** that pairs `<id>.txt` documents with `<id>.json` ground truth, validates against the schema
- **Runners** for Claude (Anthropic) and OpenAI (GPT). Gemini and Together stubs ready to add.
- **Metrics** — exact match, field accuracy, macro F1, cost estimate (USD)
- **Eval orchestrator** with Typer CLI: `uv run python -m src.eval run --models … --prompts … --doc-types …`
- **Convenience runner** at `scripts/run.sh`
- **Analyzer** (`scripts/analyze.py`) — produces F1 bar chart, cost-vs-F1 scatter, and markdown summary from a results CSV
- **Four prompt strategies**: `v1_baseline`, `v2_structured` (schema in prompt), `v3_few_shot`, `v4_cot` (chain-of-thought)
- **Synthetic dataset** — 3 invoices (PT EUR, GB GBP reverse-charge, PT simplified), 2 receipts (supermarket card payment, café cash), 2 resumes (engineer, designer)
- **Documentation**
  - `README.md` — overview + quick start
  - `docs/method.md` — how the harness works internally
  - `docs/results-2026-06.md` — placeholder for first benchmark run
  - `CONTRIBUTING.md` — how to add docs, prompts, or runners

### Known limitations

- Only Claude and OpenAI runners shipped — Gemini / Together stubs pending
- Synthetic dataset only — real-document benchmark numbers pending
- No retry logic on parse failures (deliberate — see `docs/method.md`)
- No bipartite matching for line items (sets-based F1 only)
- Single-shot extraction only (multi-step extraction belongs in a separate harness)

## [Unreleased]

### Planned for v0.2

- Real-document dataset (50 PT documents per type, anonymized)
- First published benchmark with results CSV + charts + blog writeup
- Gemini runner
- Llama runner via Together AI
- Optional bipartite matching for line items
- Temperature variance test mode (run the same cell N times to measure provider-side non-determinism)

[0.1.0]: https://github.com/mborges-dev/extraction-evals/releases/tag/v0.1.0
[Unreleased]: https://github.com/mborges-dev/extraction-evals/compare/v0.1.0...HEAD
