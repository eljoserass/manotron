from __future__ import annotations

from pathlib import Path

from openai import OpenAI

from manotron.files import IMAGE_EXTENSIONS, data_url, mime_type_for
from manotron.prompts import EXTRACTION_PROMPT
from manotron.schemas import ExtractedInvoice, ManotronSettings


def validate_api_key(api_key: str) -> None:
    client = OpenAI(api_key=api_key)
    # Authentication-only check. Extraction uses the configured model separately.
    client.models.list()


class OpenAIInvoiceExtractor:
    def __init__(self, settings: ManotronSettings) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("Missing OpenAI API key. Run `manotron init` first.")
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)

    def extract(self, path: Path) -> ExtractedInvoice:
        mime_type = mime_type_for(path)
        file_payload = _file_payload(path, mime_type)
        response = self.client.responses.parse(
            model=self.settings.openai_model,
            input=[
                {"role": "developer", "content": EXTRACTION_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Extract the invoice deduction rows from this file.",
                        },
                        file_payload,
                    ],
                },
            ],
            text_format=ExtractedInvoice,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("OpenAI returned no parsed invoice data.")
        return parsed


def _file_payload(path: Path, mime_type: str) -> dict[str, str]:
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        return {
            "type": "input_image",
            "image_url": data_url(path, mime_type),
        }
    return {
        "type": "input_file",
        "filename": path.name,
        "file_data": data_url(path, mime_type),
    }

