"""OpenAI (GPT) runner."""

from __future__ import annotations

import os
import time

from openai import OpenAI

from src.runners.base import BaseRunner

# Approximate prices in USD per million tokens. Update from
# https://openai.com/api/pricing/
PRICING: dict[str, dict[str, float]] = {
    "gpt-4o-2024-11-20": {
        "input": 2.50,
        "output": 10.00,
        "cache_read": 1.25,
    },
    "gpt-4o-mini-2024-07-18": {
        "input": 0.15,
        "output": 0.60,
        "cache_read": 0.075,
    },
    "gpt-5": {
        "input": 5.00,
        "output": 20.00,
        "cache_read": 2.50,
    },
}


class OpenAIRunner(BaseRunner):
    provider = "openai"
    default_model = os.environ.get("OPENAI_MODEL", "gpt-4o-2024-11-20")

    def __init__(self, model: str | None = None) -> None:
        super().__init__(model=model)
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY missing — copy .env.example to .env and fill it in."
            )
        self.client = OpenAI(api_key=api_key)

    def _call_model(self, prompt: str, document_text: str) -> tuple[str, dict]:
        full_prompt = prompt.replace("{{DOCUMENT_TEXT}}", document_text)

        start = time.perf_counter()
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": full_prompt}],
            response_format={"type": "json_object"},
            max_tokens=4096,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        text = resp.choices[0].message.content or ""
        u = resp.usage
        if u is None:
            usage = {"input_tokens": 0, "output_tokens": 0, "latency_ms": latency_ms}
        else:
            cached = (
                getattr(u, "prompt_tokens_details", None) and
                getattr(u.prompt_tokens_details, "cached_tokens", 0)
            ) or 0
            usage = {
                "input_tokens": u.prompt_tokens - cached,
                "output_tokens": u.completion_tokens,
                "cache_read_tokens": cached,
                "latency_ms": latency_ms,
            }
        return text, usage

    def pricing(self) -> dict[str, float]:
        return PRICING.get(self.model, PRICING["gpt-4o-2024-11-20"])
