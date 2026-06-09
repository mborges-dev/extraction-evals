Extract structured data from the document below into the schema described.

Return ONLY a JSON object. Use snake_case keys. Numbers as numbers. Dates in ISO 8601 (YYYY-MM-DD). Omit fields you cannot infer with high confidence.

# Schema

If the document is an invoice/fatura:
```json
{
  "document_number": "string",
  "document_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD or null",
  "supplier_name": "string",
  "supplier_vat": "digits only (NIF/NIPC)",
  "customer_name": "string or null",
  "customer_vat": "digits only or null",
  "currency": "ISO 4217 (default EUR)",
  "subtotal": number,
  "vat_total": number,
  "total": number,
  "line_items": [
    {
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "total": number,
      "vat_rate": number  // fraction, e.g. 0.23 for 23%
    }
  ]
}
```

If receipt: same shape but `merchant_name`/`merchant_vat` instead of supplier, no due_date, optional `payment_method` in {cash, card, mbway, transfer, other}.

If resume/CV:
```json
{
  "candidate_name": "string",
  "email": "string or null",
  "phone": "string or null",
  "location": "string or null",
  "headline": "string or null",
  "experience": [{"company", "title", "start_date", "end_date", "location", "description"}],
  "education": [{"institution", "degree", "field_of_study", "start_date", "end_date"}],
  "skills": ["string"],
  "languages": ["string"]
}
```

Return ONLY the JSON. No prose, no markdown fences.

---
{{DOCUMENT_TEXT}}
