from __future__ import annotations

import base64
import hashlib
import mimetypes
from datetime import datetime, timezone
from pathlib import Path

from manotron.schemas import FileScanCandidate

IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".webp"}
FILE_EXTENSIONS = {
    ".csv",
    ".doc",
    ".docx",
    ".html",
    ".json",
    ".md",
    ".odt",
    ".pdf",
    ".ppt",
    ".pptx",
    ".rtf",
    ".tsv",
    ".txt",
    ".xls",
    ".xlsx",
    ".xml",
}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | FILE_EXTENSIONS


def is_supported_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def iter_supported_files(folder: Path) -> list[Path]:
    return sorted(path for path in folder.expanduser().resolve().rglob("*") if is_supported_file(path))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mime_type_for(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type:
        return mime_type
    if path.suffix.lower() == ".pdf":
        return "application/pdf"
    return "application/octet-stream"


def file_candidate(path: Path) -> FileScanCandidate:
    stat = path.stat()
    return FileScanCandidate(
        path=path.expanduser().resolve(),
        sha256_hash=sha256_file(path),
        size_bytes=stat.st_size,
        created_at_fs=datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(),
        modified_at_fs=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        mime_type=mime_type_for(path),
    )


def data_url(path: Path, mime_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

