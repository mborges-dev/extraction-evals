Extract structured data from the document below into the schema (invoice / receipt / resume — infer from content).

Think step-by-step before producing the final JSON:

1. **Identify the document type.** Look for keywords (fatura, recibo, CV, currículo) and structural cues (line items vs work history).
2. **List the visible fields.** Note which schema fields are present and which are absent.
3. **Resolve ambiguous values.** If a date is shown as DD/MM/YYYY, convert to ISO. If amounts use comma decimals (Portuguese style: `1.234,56`), convert to dot decimals.
4. **Validate totals.** For invoices and receipts, check that `subtotal + vat_total ≈ total` (within 0.02 rounding). If not, prefer the printed total field.

After thinking, output a single `<extraction>...</extraction>` block containing ONLY the JSON object. No other text outside the tags.

# Schema

Same as v2 (invoice/receipt/resume — schema documented in `v2_structured.md`).

# Output format

```
<thinking>
[your step-by-step reasoning here, brief]
</thinking>

<extraction>
{ ...the JSON... }
</extraction>
```

The harness will extract content inside `<extraction>` tags. Keep `<thinking>` brief (under 200 tokens) — token cost matters.

---
{{DOCUMENT_TEXT}}
