from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


class UnsupportedFileType(ValueError):
    pass


def parse_upload(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix in {".txt", ".md", ".markdown"}:
        return data.decode("utf-8", errors="replace").strip()

    if suffix == ".pdf":
        reader = PdfReader(BytesIO(data))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
        return "\n\n".join(page for page in pages if page).strip()

    raise UnsupportedFileType(f"Unsupported file type: {suffix or 'unknown'}")
