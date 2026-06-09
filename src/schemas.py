"""Pydantic models for each document type.

The model is asked to return JSON conforming to one of these schemas.
Ground-truth files in `dataset/<type>/*.json` must also match the schema.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

DocumentType = Literal["invoice", "receipt", "resume"]


class LineItem(BaseModel):
    """One line on an invoice or receipt.

    Only `description` and `total` are required — simplified Portuguese
    receipts often omit quantity and unit_price, showing only totals.
    """

    description: str
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    total: Decimal
    vat_rate: Decimal | None = Field(
        default=None,
        description="VAT (IVA) rate as a fraction, e.g. 0.23 for 23%",
    )


class InvoiceExtraction(BaseModel):
    """Structured extraction from an invoice or fatura."""

    document_number: str | None = Field(
        default=None, description="Invoice number as printed"
    )
    document_date: date | None = None
    due_date: date | None = None
    supplier_name: str
    supplier_vat: str | None = Field(
        default=None,
        description="Supplier VAT / NIF / NIPC number (digits only)",
    )
    customer_name: str | None = None
    customer_vat: str | None = None
    currency: str = Field(default="EUR", description="ISO 4217 code")
    subtotal: Decimal
    vat_total: Decimal
    total: Decimal
    line_items: list[LineItem] = Field(default_factory=list)


class ReceiptExtraction(BaseModel):
    """Structured extraction from a receipt or recibo."""

    merchant_name: str
    merchant_vat: str | None = None
    receipt_date: date | None = None
    currency: str = Field(default="EUR")
    subtotal: Decimal | None = None
    vat_total: Decimal | None = None
    total: Decimal
    payment_method: Literal["cash", "card", "mbway", "transfer", "other"] | None = None
    line_items: list[LineItem] = Field(default_factory=list)


class Experience(BaseModel):
    """One role on a resume."""

    company: str
    title: str
    start_date: date | None = None
    end_date: date | None = Field(
        default=None, description="None if still current"
    )
    location: str | None = None
    description: str | None = None


class Education(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ResumeExtraction(BaseModel):
    """Structured extraction from a CV / resume."""

    candidate_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = Field(
        default=None, description="Current role / one-line professional summary"
    )
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


SCHEMA_BY_TYPE: dict[DocumentType, type[BaseModel]] = {
    "invoice": InvoiceExtraction,
    "receipt": ReceiptExtraction,
    "resume": ResumeExtraction,
}
