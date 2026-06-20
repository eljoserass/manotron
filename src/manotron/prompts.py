LOCATION_KEYWORD = "location"
PRODUCT_REFERENCE_KEYWORD = "product reference"
INVOICE_REFERENCE_KEYWORD = "invoice reference"
QUANTITY_KEYWORD = "quantity"

EXTRACTION_PROMPT = f"""
Extract invoice/order deduction data from the provided invoice scan.

Terms may vary. Treat "{LOCATION_KEYWORD}" as the storage/bin/place code,
"{PRODUCT_REFERENCE_KEYWORD}" as the product code, "{INVOICE_REFERENCE_KEYWORD}"
as the invoice id, and "{QUANTITY_KEYWORD}" as the total product quantity.

Return one line per product. Each line must include every location that appears
to contribute stock for that product.

Rules:
- If handwritten digits appear beside locations, use those digits as the
  quantity deducted from each location.
- If there is a checkmark beside one location and no handwritten digit, assume
  the full product quantity is deducted from that checked location.
- Prefer extracting likely rows over omitting uncertain rows.
- Use source="handwritten_digit" for handwritten quantities.
- Use source="checkmark_assumed" when a checkmark implies the full quantity.
- Use source="printed" for quantities printed on the document.
- Use source="inferred" for reasonable deductions inferred from the layout.
- Use source="unknown" when the source is unclear.
- Put short uncertainty notes in notes instead of adding extra fields.
""".strip()

