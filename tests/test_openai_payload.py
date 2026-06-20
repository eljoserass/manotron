from pathlib import Path

from manotron.openai_client import _file_payload


def test_file_payload_routes_images_and_pdfs(tmp_path: Path) -> None:
    image = tmp_path / "invoice.jpg"
    pdf = tmp_path / "invoice.pdf"
    image.write_bytes(b"image-bytes")
    pdf.write_bytes(b"pdf-bytes")

    image_payload = _file_payload(image, "image/jpeg")
    pdf_payload = _file_payload(pdf, "application/pdf")

    assert image_payload["type"] == "input_image"
    assert image_payload["image_url"].startswith("data:image/jpeg;base64,")
    assert pdf_payload["type"] == "input_file"
    assert pdf_payload["filename"] == "invoice.pdf"
    assert pdf_payload["file_data"].startswith("data:application/pdf;base64,")

