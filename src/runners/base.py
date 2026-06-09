"""Base interface every provider runner implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RunResult:
    """The output of running one prompt × one document on one model."""

    model: str
    prompt_version: str
    doc_id: str
    doc_type: str

    # Raw outputs
    raw_response: str
    parsed_json: dict | None  # None if parsing failed

    # Resource usage
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    latency_ms: int = 0

    # Errors
    error: str | None = None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.cache_read_tokens + self.cache_write_tokens


class BaseRunner(ABC):
    """Abstract base class for provider runners.

    Subclasses must:
    - Set `provider` and `default_model`.
    - Implement `_call_model(...)` to do the actual API call.
    - Implement `pricing(...)` for cost-estimation.
    """

    provider: str = "base"
    default_model: str = "unknown"

    def __init__(self, model: str | None = None) -> None:
        self.model = model or self.default_model

    @abstractmethod
    def _call_model(self, prompt: str, document_text: str) -> tuple[str, dict]:
        """Send the prompt + document to the model.

        Returns:
            (raw_response_text, usage_dict)
            usage_dict must contain at least: input_tokens, output_tokens
            and optionally cache_read_tokens, cache_write_tokens.
        """
        ...

    @abstractmethod
    def pricing(self) -> dict[str, float]:
        """Per-million-token USD prices for this model.

        Returns a dict with keys: input, output, cache_read, cache_write
        (cache keys are optional; default 0).
        """
        ...

    def estimated_cost_usd(self, usage: dict) -> float:
        """Apply pricing to a usage dict."""
        p = self.pricing()
        per_million = (
            usage.get("input_tokens", 0) * p.get("input", 0)
            + usage.get("output_tokens", 0) * p.get("output", 0)
            + usage.get("cache_read_tokens", 0) * p.get("cache_read", 0)
            + usage.get("cache_write_tokens", 0) * p.get("cache_write", 0)
        )
        return per_million / 1_000_000
