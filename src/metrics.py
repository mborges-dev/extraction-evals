"""Field-level metrics for comparing extractions against ground truth.

Three metrics, simple by design:
- `exact_match`: 1 if extracted JSON equals ground truth, 0 otherwise (after normalization)
- `field_accuracy`: fraction of top-level fields that match ground truth
- `field_f1`: per-field F1, then averaged (macro)

For nested lists (line_items, experience, etc.), correctness is by index for the
demo; production usage should match items with bipartite assignment.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


def _normalize(v: Any) -> Any:
    """Normalize values so 'EUR' == 'eur', '1.00' == '1.0', None == ''."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip().lower()
    if isinstance(v, list):
        return [_normalize(item) for item in v]
    if isinstance(v, Mapping):
        return {k: _normalize(item) for k, item in v.items()}
    # Decimals, dates, ints — stringify then compare
    return str(v).lower()


def exact_match(extracted: dict, ground_truth: dict) -> float:
    """1.0 if extraction matches ground truth exactly (after normalize)."""
    return 1.0 if _normalize(extracted) == _normalize(ground_truth) else 0.0


def field_accuracy(extracted: dict, ground_truth: dict) -> float:
    """Fraction of top-level fields that match ground truth.

    Nested lists count as one field each (deep equality).
    """
    gt_n = _normalize(ground_truth)
    ex_n = _normalize(extracted)
    if not isinstance(gt_n, dict):
        return 0.0

    total = len(gt_n)
    if total == 0:
        return 1.0
    matched = sum(1 for k, v in gt_n.items() if isinstance(ex_n, dict) and ex_n.get(k) == v)
    return matched / total


@dataclass(frozen=True)
class FieldF1:
    field: str
    precision: float
    recall: float
    f1: float


def per_field_f1(extracted: dict, ground_truth: dict) -> list[FieldF1]:
    """Per-field F1 across all keys present in either side.

    - precision: of the value extracted, what fraction is correct
    - recall: of the value in ground truth, what fraction was extracted

    For scalars (str/number/None), F1 is binary (1.0 or 0.0).
    For lists, F1 is set-based overlap.
    """
    keys = set(extracted.keys()) | set(ground_truth.keys())
    out: list[FieldF1] = []
    for k in sorted(keys):
        ev = _normalize(extracted.get(k))
        gv = _normalize(ground_truth.get(k))
        out.append(_score_field(k, ev, gv))
    return out


def _score_field(field: str, extracted: Any, ground_truth: Any) -> FieldF1:
    # Empty on both sides — perfect match
    if not extracted and not ground_truth:
        return FieldF1(field, 1.0, 1.0, 1.0)

    if isinstance(ground_truth, list) and isinstance(extracted, list):
        gt_set = {str(x) for x in ground_truth}
        ex_set = {str(x) for x in extracted}
        tp = len(gt_set & ex_set)
        precision = tp / len(ex_set) if ex_set else 0.0
        recall = tp / len(gt_set) if gt_set else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return FieldF1(field, precision, recall, f1)

    # Scalars — binary
    match = 1.0 if extracted == ground_truth else 0.0
    return FieldF1(field, match, match, match)


def macro_f1(extracted: dict, ground_truth: dict) -> float:
    """Mean F1 across top-level fields."""
    field_scores = per_field_f1(extracted, ground_truth)
    if not field_scores:
        return 0.0
    return sum(f.f1 for f in field_scores) / len(field_scores)
