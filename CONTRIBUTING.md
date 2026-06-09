# Contributing

Thanks for considering a contribution. Three forms of contribution are explicitly welcome:

## 1. More documents in the dataset

This is the highest-leverage way to help. Add anonymized real documents (invoices, receipts, CVs) — see [`dataset/README.md`](dataset/README.md) for the format and anonymization rules.

**Pull request format:**
- One document type per PR (don't mix invoices and CVs)
- Include both `<id>.txt` (text) and `<id>.json` (ground truth)
- Run `uv run python -c "from src.loaders import iter_pairs; list(iter_pairs())"` before pushing — it'll catch schema mismatches
- In the PR description, say what domain the docs come from and confirm they're anonymized

## 2. New prompt strategies

Prompt versions live in `prompts/v<N>_<name>.md`. Add a new one in the same numeric series.

Read [`prompts/_shared.md`](prompts/_shared.md) first — it explains the output contract every prompt must honor.

**Don't:**
- Hard-code one document type into a prompt — the same prompt must handle invoices, receipts, and CVs
- Multi-step prompts that need parse-then-retry — this harness is single-shot by design (see [`docs/method.md`](docs/method.md))

## 3. New provider runners

To add e.g. Mistral, Cohere, or a self-hosted model:

1. Create `src/runners/<provider>.py`
2. Subclass `BaseRunner` (see `src/runners/base.py`)
3. Implement `_call_model(self, prompt, document_text) → (text, usage)` and `pricing(self) → dict`
4. Add a per-million-token pricing table at the top of the file with a comment linking to the provider's pricing page
5. Register the runner in `src/eval.py`'s `_runner_for(...)` dispatcher

Open a PR — happy to review pricing tables against the source.

---

## Development setup

```bash
git clone https://github.com/mborges-dev/extraction-evals
cd extraction-evals

# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

uv sync                              # install runtime + dev deps
cp .env.example .env                 # then fill in API keys you have

# Linting and types
uv run ruff check src tests
uv run ruff format --check src tests
uv run pyright src

# Smoke test the harness without making API calls
uv run python -c "from src.loaders import iter_pairs; print(len(list(iter_pairs())))"
```

## What I'll likely not accept

- New top-level dependencies (the runtime is intentionally minimal: anthropic + openai + pydantic + pandas + matplotlib + typer + rich + dotenv)
- Provider-specific quirks leaking outside `src/runners/<provider>.py`
- Metrics that are radically different in spirit from F1 / exact-match (those belong in a separate library)
- Dataset documents that aren't anonymized

## Reporting bugs

Open an issue with:

- What command you ran
- What you expected
- What actually happened (error output, partial CSV, etc.)
- Your Python version (`python --version`) and uv version (`uv --version`)

## Code of conduct

Be useful. Be honest. Be brief.
