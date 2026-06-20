from __future__ import annotations

from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from sqlalchemy import select

from manotron.config import load_settings
from manotron.db import init_db, session_scope
from manotron.models import Invoice, InvoiceLine, SourceFile
from manotron.schemas import ExportOptions, ManotronSettings

EXPORT_COLUMNS = [
    "invoice_reference_id",
    "invoice_date",
    "product_reference_id",
    "product_locations",
    "quantity_deducted",
    "locations_quantity",
    "source_file_path",
    "extracted_at",
    "model_name",
    "line_confidence",
    "invoice_confidence",
    "line_notes",
    "invoice_notes",
]


def export_configured(options: ExportOptions) -> Path:
    settings = load_settings()
    return export_to_excel(settings, options)


def export_to_excel(settings: ManotronSettings, options: ExportOptions) -> Path:
    init_db(settings.db_path)
    output_path = _resolve_output_path(settings, options)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "invoice_lines"
    worksheet.append(EXPORT_COLUMNS)

    with session_scope(settings.db_path) as session:
        statement = (
            select(InvoiceLine, Invoice, SourceFile)
            .join(Invoice, InvoiceLine.invoice_id == Invoice.id)
            .join(SourceFile, Invoice.source_file_id == SourceFile.id)
            .order_by(Invoice.invoice_date, Invoice.invoice_reference_id, InvoiceLine.id)
        )
        for line, invoice, source_file in session.execute(statement).all():
            if not _within_date_range(invoice, options):
                continue
            worksheet.append(
                [
                    invoice.invoice_reference_id,
                    invoice.invoice_date.isoformat() if invoice.invoice_date else "",
                    line.product_reference_id,
                    line.product_locations,
                    line.quantity_deducted,
                    line.locations_quantity,
                    source_file.path,
                    invoice.extracted_at.isoformat(),
                    invoice.model_name,
                    line.confidence,
                    invoice.confidence,
                    line.notes,
                    invoice.notes,
                ]
            )

    workbook.save(output_path)
    return output_path


def _resolve_output_path(settings: ManotronSettings, options: ExportOptions) -> Path:
    if options.output_path:
        return options.output_path.expanduser().resolve()
    folder = Path(settings.export_default_folder).expanduser() if settings.export_default_folder else Path.cwd()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return (folder / f"manotron_export_{stamp}.xlsx").resolve()


def _within_date_range(invoice: Invoice, options: ExportOptions) -> bool:
    if invoice.invoice_date is None:
        return True
    if options.date_from and invoice.invoice_date.isoformat() < options.date_from:
        return False
    if options.date_to and invoice.invoice_date.isoformat() > options.date_to:
        return False
    return True

