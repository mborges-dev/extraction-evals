"""Google Gemini runner."""

from __future__ import annotations

import os
import time

from google import genai
from google.genai import types

from src.runners.base import BaseRunner

# Approximate prices in USD per million tokens (paid tier — free tier has rate
# limits but no per-token cost). Update from
# https://ai.google.dev/gemini-api/docs/pricing
PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-pro": {
        "input": 1.25,
        "output": 10.00,
        "cache_read": 0.31,
    },
    "gemini-2.5-flash": {
        "input": 0.30,
        "output": 2.50,
        "cache_read": 0.075,
    },
    "gemini-2.5-flash-lite": {
        "input": 0.10,
        "output": 0.40,
        "cache_read": 0.025,
    },
}


class GeminiRunner(BaseRunner):
    provider = "google"
    default_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    def __init__(self, model: str | None = None) -> None:
        super().__init__(model=model)
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY missing — copy .env.example to .env and fill it in.")
        self.client = genai.Client(api_key=api_key)

    def _call_model(self, prompt: str, document_text: str) -> tuple[str, dict]:
        full_prompt = prompt.replace("{{DOCUMENT_TEXT}}", document_text)

        # Free-tier Gemini = 10 RPM / 250k TPM. Sequential evals trip this
        # immediately. Retry with exponential backoff on 429 / 503.
        start = time.perf_counter()
        resp = None
        last_err = None
        for attempt in range(4):
            try:
                resp = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        max_output_tokens=4096,
                    ),
                )
                break
            except Exception as e:  # noqa: BLE001
                last_err = e
                msg = str(e)
                if "429" in msg or "503" in msg or "RESOURCE_EXHAUSTED" in msg:
                    # 8, 16, 32, 64 seconds — covers the 60-second RPM window
                    time.sleep(2 ** (attempt + 3))
                    continue
                raise
        if resp is None:
            raise RuntimeError(f"Gemini exhausted retries: {last_err}")
        latency_ms = int((time.perf_counter() - start) * 1000)

        text = resp.text or ""
        meta = resp.usage_metadata
        if meta is None:
            usage = {"input_tokens": 0, "output_tokens": 0, "latency_ms": latency_ms}
        else:
            cached = getattr(meta, "cached_content_token_count", 0) or 0
            prompt_tokens = (meta.prompt_token_count or 0) - cached
            output_tokens = meta.candidates_token_count or 0
            usage = {
                "input_tokens": max(0, prompt_tokens),
                "output_tokens": output_tokens,
                "cache_read_tokens": cached,
                "latency_ms": latency_ms,
            }
        return text, usage

    def pricing(self) -> dict[str, float]:
        return PRICING.get(self.model, PRICING["gemini-2.5-flash"])
