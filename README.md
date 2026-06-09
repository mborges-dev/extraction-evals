# Extraction Evals

[![Python](https://img.shields.io/badge/python-3.12-3776AB.svg)](https://www.python.org/)
[![uv](https://img.shields.io/badge/managed%20by-uv-blueviolet.svg)](https://github.com/astral-sh/uv)

**A reproducible benchmark for LLM-based structured extraction from documents.**

Compares modern LLMs (Claude · GPT · Gemini · open-weight) on the same task — extracting structured fields from semi-structured documents (invoices, receipts, CVs) — across multiple prompt strategies, with cost and latency tracking baked in.

The goal is to answer questions like:

- *"For Portuguese invoices, does Claude Sonnet beat GPT-4o on supplier-NIF extraction? At what cost difference?"*
- *"Does adding a JSON schema to the prompt help GPT more than it helps Claude?"*
- *"Is the cheapest model still cheapest after accounting for retries on failed extractions?"*

---

## What's in the box

```
extraction-evals/
├── dataset/                  # documents + ground truth
│   ├── invoices/             # 3 synthetic invoices to start, add yours
│   ├── receipts/             # 2 receipts
│   └── resumes/              # 2 CVs
│
├── prompts/                  # versioned prompt strategies
│   ├── v1_baseline.md        # plain instruction
│   ├── v2_structured.md      # + JSON schema in prompt
│   ├── v3_few_shot.md        # + 2 example extractions
│   └── v4_cot.md             # + chain-of-thought
│
├── src/
│   ├── schemas.py            # Pydantic models for each doc type
│   ├── loaders.py            # load docs + ground truth from disk
│   ├── runners/              # one file per provider
│   │   ├── base.py
│   │   ├── claude.py
│   │   ├── openai.py
│   │   └── gemini.py
│   ├── metrics/              # field accuracy, exact match, cost
│   └── eval.py               # orchestrator
│
├── scripts/
│   ├── run.sh                # convenience entrypoint
│   └── analyze.py            # results → charts
│
├── results/                  # CSV + chart outputs (gitignored beyond schema)
└── docs/
    ├── method.md             # how the harness works
    └── results-2026-06.md    # placeholder for first writeup
```

## Quick start

```bash
# 1. Install uv (modern Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone + install deps
git clone https://github.com/mborges-dev/extraction-evals
cd extraction-evals
uv sync

# 3. Set your API keys
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.

# 4. Run the eval
./scripts/run.sh

# Or directly:
uv run python -m src.eval --models claude-sonnet-4-5 --prompts v1_baseline --doc-types invoices
```

## How it works

1. **Load** documents + ground truth from `dataset/<type>/`
2. **Render** the active prompt strategy with the document text injected
3. **Call** each configured model — capture response + token usage + latency
4. **Parse** the response into a typed Pydantic schema (model is asked for JSON)
5. **Compare** parsed extraction vs ground truth field-by-field
6. **Compute** metrics: per-field F1, exact-match rate, $ per successful extraction
7. **Write** results to `results/YYYY-MM-DD.csv` with full provenance

Each run is reproducible: same prompts + same dataset + same models = same metric outputs (modulo non-zero temperature).

## Why this exists

LLMs are increasingly used for "extract structured data from this PDF / form / email" tasks in production. The standard way to choose between models is vibes (*"GPT-4o feels better"*) or marketing benchmarks (HumanEval, MMLU). Neither tells you anything about your actual task.

The right way is a domain-specific eval suite with golden data, run regularly. This repo is one such suite for the European document-extraction use case — biased toward Portuguese tax/invoice formats because that's the author's domain. **Forks for German / French / Spanish documents welcome.**

## Status

**v0.1 — initial scaffold.** Harness works. Dataset is small and synthetic (3 invoices, 2 receipts, 2 resumes). Runner implementations for Claude and OpenAI included; Gemini stub present. No published results yet.

See [docs/method.md](docs/method.md) for how the harness works internally. See [CHANGELOG.md](CHANGELOG.md) for what's shipped.

## Contributing

PRs welcome, especially:

- **More documents in the dataset** (with ground truth). Run `uv run python -m src.dataset add` to validate format.
- **New prompt strategies** in `prompts/v5_*.md`. Read [`prompts/_shared.md`](prompts/_shared.md) first.
- **New provider runners** — implement `src/runners/base.py`'s interface.
- **Better metrics** — current set is intentionally minimal.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution flow.

---

## Notice

This repository is published as a **portfolio showcase** of my work. The code is **not licensed for reuse, redistribution, or modification.** You're welcome to read it, but it is not open source. If you'd like to discuss similar work, [get in touch](mailto:hello@miguelborges.dev).

---

Built by [Miguel Borges](https://miguelborges.dev) · [hello@miguelborges.dev](mailto:hello@miguelborges.dev)
