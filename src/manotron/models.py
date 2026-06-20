from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SourceFile(Base):
    __tablename__ = "source_files"
    __table_args__ = (UniqueConstraint("sha256_hash", name="uq_source_files_sha256_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(Text)
    filename: Mapped[str] = mapped_column(String(512))
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    created_at_fs: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    modified_at_fs: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    invoices: Mapped[list[Invoice]] = relationship(back_populates="source_file")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_file_id: Mapped[int] = mapped_column(ForeignKey("source_files.id"))
    invoice_reference_id: Mapped[str] = mapped_column(String(255), index=True)
    invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    model_name: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_llm_json: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_file: Mapped[SourceFile] = relationship(back_populates="invoices")
    lines: Mapped[list[InvoiceLine]] = relationship(back_populates="invoice")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    product_reference_id: Mapped[str] = mapped_column(String(255), index=True)
    product_locations: Mapped[str] = mapped_column(Text)
    quantity_deducted: Mapped[int] = mapped_column(Integer)
    locations_quantity: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    invoice: Mapped[Invoice] = relationship(back_populates="lines")
    location_deductions: Mapped[list[LineLocationDeduction]] = relationship(
        back_populates="invoice_line",
        cascade="all, delete-orphan",
    )


class LineLocationDeduction(Base):
    __tablename__ = "line_location_deductions"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_line_id: Mapped[int] = mapped_column(ForeignKey("invoice_lines.id"))
    location: Mapped[str] = mapped_column(String(255), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(64))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    invoice_line: Mapped[InvoiceLine] = relationship(back_populates="location_deductions")


class ScanRun(Base):
    __tablename__ = "scan_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    folder: Mapped[str] = mapped_column(Text)
    files_seen: Mapped[int] = mapped_column(Integer, default=0)
    files_processed: Mapped[int] = mapped_column(Integer, default=0)
    files_failed: Mapped[int] = mapped_column(Integer, default=0)
    files_skipped: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="running")

