"""Claude (Anthropic) runner."""

from __future__ import annotations

import os
import time

from anthropic import Anthropic
from anthropic.types import TextBlock

from src.runners.base import BaseRunner

# Approximate prices in USD per million tokens. Update from
# https://docs.anthropic.com/en/docs/about-claude/models
PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-5": {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "cache_write": 3.75,
    },
    "claude-opus-4": {
        "input": 15.00,
        "output": 75.00,
        "cache_read": 1.50,
        "cache_write": 18.75,
    },
    "claude-haiku-4-5": {
        "input": 1.00,
        "output": 5.00,
        "cache_read": 0.10,
        "cache_write": 1.25,
    },
}


class ClaudeRunner(BaseRunner):
    provider = "anthropic"
    default_model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5")

    def __init__(self, model: str | None = None) -> None:
        super().__init__(model=model)
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY missing — copy .env.example to .env and fill it in."
            )
        self.client = Anthropic(api_key=api_key)

    def _call_model(self, prompt: str, document_text: str) -> tuple[str, dict]:
        full_prompt = prompt.replace("{{DOCUMENT_TEXT}}", document_text)

        start = time.perf_counter()
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": full_prompt}],
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        # Extract text — first TextBlock in the response
        text = ""
        for block in msg.content:
            if isinstance(block, TextBlock):
                text = block.text
                break

        usage = {
            "input_tokens": msg.usage.input_tokens,
            "output_tokens": msg.usage.output_tokens,
            "cache_read_tokens": getattr(msg.usage, "cache_read_input_tokens", 0) or 0,
            "cache_write_tokens": getattr(msg.usage, "cache_creation_input_tokens", 0) or 0,
            "latency_ms": latency_ms,
        }
        return text, usage

    def pricing(self) -> dict[str, float]:
        return PRICING.get(self.model, PRICING["claude-sonnet-4-5"])
