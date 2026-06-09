"""Load documents and ground truth from disk.

Each document lives as a pair under `dataset/<type>/`:
- `<id>.txt`   the document text (or markdown rendering)
- `<id>.json`  the ground-truth extraction (matches schema for that type)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from pydantic import BaseModel

from src.schemas import SCHEMA_BY_TYPE, DocumentType

DATASET_ROOT = Path(__file__).resolve().parent.parent / "dataset"

# Folder names are plural; schema enum values are singular.
FOLDER_BY_TYPE: dict[DocumentType, str] = {
    "invoice": "invoices",
    "receipt": "receipts",
    "resume": "resumes",
}


@dataclass(frozen=True)
class DocumentPair:
    """A document and its ground-truth extraction."""

    doc_id: str
    doc_type: DocumentType
    text: str
    ground_truth: BaseModel

    @property
    def path(self) -> Path:
        return DATASET_ROOT / FOLDER_BY_TYPE[self.doc_type] / f"{self.doc_id}.txt"


def load_pair(doc_type: DocumentType, doc_id: str) -> DocumentPair:
    """Load one document + its ground truth. Raises FileNotFoundError if missing."""
    type_dir = DATASET_ROOT / FOLDER_BY_TYPE[doc_type]
    text_path = type_dir / f"{doc_id}.txt"
    gt_path = type_dir / f"{doc_id}.json"

    text = text_path.read_text(encoding="utf-8")
    gt_raw = json.loads(gt_path.read_text(encoding="utf-8"))
    schema = SCHEMA_BY_TYPE[doc_type]
    ground_truth = schema.model_validate(gt_raw)

    return DocumentPair(
        doc_id=doc_id,
        doc_type=doc_type,
        text=text,
        ground_truth=ground_truth,
    )


def iter_pairs(doc_type: DocumentType | None = None) -> Iterator[DocumentPair]:
    """Iterate over all document pairs, optionally filtered by type.

    Yields pairs in deterministic alphabetical order so eval runs are reproducible.
    """
    types: list[DocumentType] = (
        [doc_type] if doc_type else ["invoice", "receipt", "resume"]
    )
    for t in types:
        type_dir = DATASET_ROOT / FOLDER_BY_TYPE[t]
        if not type_dir.exists():
            continue
        for txt_file in sorted(type_dir.glob("*.txt")):
            doc_id = txt_file.stem
            try:
                yield load_pair(t, doc_id)
            except FileNotFoundError:
                # Missing ground truth — skip but warn
                print(f"  ⚠️  {t}/{doc_id}: no ground-truth JSON, skipping")
