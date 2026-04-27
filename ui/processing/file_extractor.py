# ui/processing/file_extractor.py
# Extracts plain text from uploaded files (PDF, DOCX, TXT, MD).

import io
import logging

logger = logging.getLogger(__name__)


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from an uploaded file.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        filename: Original filename (used to detect format).

    Returns:
        Extracted plain text string.
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"

    if ext in ("txt", "md"):
        return _extract_txt(file_bytes)
    elif ext == "pdf":
        return _extract_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return _extract_docx(file_bytes)
    else:
        # Best-effort: try UTF-8 decode
        try:
            return file_bytes.decode("utf-8", errors="replace")
        except Exception:
            return ""


def _extract_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="replace").strip()


def _extract_pdf(file_bytes: bytes) -> str:
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)
    except ImportError:
        logger.warning("PyPDF2 not installed - cannot extract PDF text")
        return "[PDF extraction requires PyPDF2. Run: pip install PyPDF2]"
    except Exception as e:
        logger.warning("PDF extraction failed: %s", str(e)[:200])
        return ""


def _extract_docx(file_bytes: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except ImportError:
        logger.warning("python-docx not installed - cannot extract DOCX text")
        return "[DOCX extraction requires python-docx. Run: pip install python-docx]"
    except Exception as e:
        logger.warning("DOCX extraction failed: %s", str(e)[:200])
        return ""


def word_count(text: str) -> int:
    return len(text.split())


def auto_detect_mode(text: str) -> str:
    """Suggest a mode based on text length."""
    wc = word_count(text)
    if wc < 300:
        return "pulse"
    elif wc < 800:
        return "narrative"
    else:
        return "scholar"
