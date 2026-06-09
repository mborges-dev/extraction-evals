# Dataset

Documents and their ground-truth extractions.

```
dataset/
├── invoices/
│   ├── inv-001.txt    # the document text
│   ├── inv-001.json   # the expected extraction
│   ├── inv-002.txt
│   └── inv-002.json
├── receipts/
└── resumes/
```

## What's shipped

The initial dataset is **synthetic** — 3 invoices, 2 receipts, 2 resumes with fictional vendor/candidate names. Just enough to exercise the harness end-to-end. The data is realistic in *format* (Portuguese tax conventions, decimal commas, NIF numbers) but the actors are made up.

For meaningful benchmark numbers you'll want **50–200 documents per type** — ideally real ones (anonymized) drawn from a single domain.

## Adding documents

1. Choose a unique short ID (`inv-042`, `rec-007`, `cv-013`).
2. Save the text content as `<id>.txt` (UTF-8). For PDFs, extract text first using `pdftotext` or `pdfplumber` — the harness doesn't do OCR.
3. Save the ground-truth extraction as `<id>.json` matching the schema for that doc type (see `src/schemas.py`).

Run the schema validator before committing:

```bash
uv run python -c "from src.loaders import iter_pairs; list(iter_pairs())"
```

Any schema mismatches will raise a `ValidationError` with the offending field.

## Ground-truth conventions

- **Currency:** ISO 4217 codes (`"EUR"`, `"USD"`, `"GBP"`). Default `EUR` when unstated.
- **VAT / IVA rate:** decimal fraction (`0.23` not `23`).
- **VAT / NIF / NIPC numbers:** digits only, no `"PT"` prefix (`"501234567"` not `"PT501234567"`).
- **Dates:** ISO 8601 (`"2026-03-15"`).
- **Amounts:** dot decimal (`"100.00"` not `"100,00"`).
- **Empty fields:** **omit** from JSON, don't write `null` (avoids false-positive disagreements with models that include vs omit nulls).

## Anonymization

If you use real documents, redact:

- Real personal names (replace with consistent fake names)
- Real phone numbers, email addresses, postal addresses
- Bank account / IBAN numbers
- Real NIF/NIPC of small entities (large companies' NIFs are public so optional)
- Logos and signatures (text-only extraction is unaffected by image removal)

Keep the structural realism — the harness is testing the model's ability to parse *real-looking* documents, so format details matter.
