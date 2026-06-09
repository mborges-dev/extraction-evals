#!/usr/bin/env bash
# Convenience wrapper around `uv run python -m src.eval`.
#
# Usage:
#   ./scripts/run.sh                                       # default models + v1
#   ./scripts/run.sh -m claude-sonnet-4-5 gpt-4o-2024-11-20
#   ./scripts/run.sh -m claude-sonnet-4-5 -p v1_baseline v2_structured v3_few_shot
#   ./scripts/run.sh -t invoice                            # only invoices

set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is not installed. Install with:" >&2
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "Warning: .env not found. Copy .env.example to .env and add your API keys." >&2
fi

# Default args if none given
if [[ $# -eq 0 ]]; then
  set -- -m claude-sonnet-4-5 -p v1_baseline
fi

uv run python -m src.eval run "$@"
