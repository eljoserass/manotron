from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


DeductionSource = Literal[
    "handwritten_digit",
    "checkmark_assumed",
    "printed",
    "inferred",
    "unknown",
]


class ExtractedLocationDeduction(BaseModel):
    location: str = Field(description="Storage location/bin code.")
    quantity: int = Field(description="Quantity deducted from this location.")
    source: DeductionSource = Field(description="How this deduction was read.")
    confidence: float | None = None


class ExtractedInvoiceLine(BaseModel):
    product_reference_id: str
    quantity_deducted: int
    location_deductions: list[ExtractedLocationDeduction]
    confidence: float | None = None
    notes: str | None = None


class ExtractedInvoice(BaseModel):
    invoice_reference_id: str
    invoice_date: str | None = Field(
        default=None,
        description="Invoice date as YYYY-MM-DD when visible, otherwise null.",
    )
    lines: list[ExtractedInvoiceLine]
    confidence: float | None = None
    notes: str | None = None


class ManotronSettings(BaseModel):
    watch_folder: str | None = None
    db_path: str
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    export_default_folder: str | None = None


class FileScanCandidate(BaseModel):
    path: Path
    sha256_hash: str
    size_bytes: int
    created_at_fs: str
    modified_at_fs: str
    mime_type: str


class ExportOptions(BaseModel):
    output_path: Path | None = None
    date_from: str | None = None
    date_to: str | None = None
