from io import BytesIO
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader


class DocumentError(ValueError):
    pass


def extract_policy_text(filename: str, payload: bytes) -> str:
    """Extract searchable text from PDF, DOCX, or a UTF-8 text file."""
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".pdf":
            reader = PdfReader(BytesIO(payload), strict=False)
            if reader.is_encrypted:
                raise DocumentError("This PDF is password-protected. Upload an unlocked copy.")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif suffix == ".docx":
            document = Document(BytesIO(payload))
            blocks = []
            for block in document.iter_inner_content():
                if isinstance(block, Paragraph) and block.text.strip():
                    blocks.append(block.text)
                elif isinstance(block, Table):
                    blocks.extend(" | ".join(cell.text for cell in row.cells) for row in block.rows)
            text = "\n".join(blocks)
        elif suffix == ".doc":
            raise DocumentError("Legacy .doc files are not supported. Save the document as .docx and upload it again.")
        else:
            text = payload.decode("utf-8-sig")
            if "\x00" in text:
                raise DocumentError("That file does not look like a text document.")
    except DocumentError:
        raise
    except Exception as e:
        raise DocumentError("Could not read that file. Check that it is a valid PDF, DOCX, or UTF-8 text file.") from e

    text = text.strip()
    if not text:
        raise DocumentError("No selectable text was found. Scanned PDFs need OCR before upload.")
    return text