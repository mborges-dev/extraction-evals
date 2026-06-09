Extract structured data from the document below into the schema described.

Return ONLY a JSON object. Use snake_case keys. Numbers as numbers. Dates in ISO 8601 (YYYY-MM-DD). Omit fields you cannot infer with high confidence.

# Schema

Same as the schema in v2 (invoice/receipt/resume detected from content).

# Example 1 — invoice

Document:
```
FATURA Nº 2026/A/0042
Data: 15/03/2026   Vencimento: 30/03/2026
Acme Comércio, Lda.     NIF: 501234567
Cliente: Beta SA        NIF: 502345678
Produto X    2 un. × 50,00€  = 100,00€  (IVA 23%)
Subtotal: 100,00€   IVA: 23,00€   Total: 123,00€
```

Extraction:
```json
{
  "document_number": "2026/A/0042",
  "document_date": "2026-03-15",
  "due_date": "2026-03-30",
  "supplier_name": "Acme Comércio, Lda.",
  "supplier_vat": "501234567",
  "customer_name": "Beta SA",
  "customer_vat": "502345678",
  "currency": "EUR",
  "subtotal": 100.00,
  "vat_total": 23.00,
  "total": 123.00,
  "line_items": [
    {"description": "Produto X", "quantity": 2, "unit_price": 50.00, "total": 100.00, "vat_rate": 0.23}
  ]
}
```

# Example 2 — resume

Document:
```
Joana Pereira
Senior Backend Engineer · Lisbon, Portugal
joana@example.com · 912 345 678

Experience
- TechCo (2022–present): Built payment pipeline in Go
- StartupX (2020–2022): Led API team

Education
- MSc Computer Science, IST, 2020

Skills: Go, Python, PostgreSQL, Kubernetes
```

Extraction:
```json
{
  "candidate_name": "Joana Pereira",
  "headline": "Senior Backend Engineer",
  "location": "Lisbon, Portugal",
  "email": "joana@example.com",
  "phone": "912 345 678",
  "experience": [
    {"company": "TechCo", "title": "Senior Backend Engineer", "start_date": "2022-01-01", "end_date": null, "description": "Built payment pipeline in Go"},
    {"company": "StartupX", "title": "API Team Lead", "start_date": "2020-01-01", "end_date": "2022-01-01", "description": "Led API team"}
  ],
  "education": [
    {"institution": "IST", "degree": "MSc", "field_of_study": "Computer Science", "end_date": "2020-01-01"}
  ],
  "skills": ["Go", "Python", "PostgreSQL", "Kubernetes"]
}
```

Now extract the following document. Return ONLY the JSON.

---
{{DOCUMENT_TEXT}}
