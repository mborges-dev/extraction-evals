Extract structured data from the document below.

Return a single JSON object with the relevant fields. Use snake_case keys. Numbers as numbers (not strings). Dates in ISO 8601 format (YYYY-MM-DD). If a field is not present in the document, omit it from the JSON.

Return ONLY the JSON object. No prose, no markdown fences, no comments.

---
{{DOCUMENT_TEXT}}
