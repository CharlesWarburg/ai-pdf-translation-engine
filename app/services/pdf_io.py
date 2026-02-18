import logging
import os
from dataclasses import dataclass
from io import BytesIO
from typing import List, Optional

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ..utils.errors import PermanentUpstreamError, UserInputError

logger = logging.getLogger(__name__)

# Unicode-capable font for PDF output; registered once per process.
_UNICODE_FONT_REGISTERED: Optional[str] = None

FONT_NAME = "DejaVuSans"
FONT_SIZE = 12


@dataclass
class Page:
    """Single PDF page with extracted text."""

    page_number: int
    text: str


@dataclass
class Document:
    """Parsed PDF document used by the translation pipeline."""

    pages: List[Page]
    total_pages: int


def extract_text_from_pdf(pdf_bytes: bytes) -> Document:
    """Extract plain text from a PDF payload."""

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        pages = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            text = " ".join(text.split())
            pages.append(Page(page_number=i, text=text))

        if not pages:
            raise UserInputError("The PDF contains no extractable text.")

        return Document(pages=pages, total_pages=len(pages))

    except PdfReadError as exc:
        # Clearly invalid / malformed PDF (e.g. renamed .txt) → treat as user input error.
        raise UserInputError("The uploaded file could not be read as a PDF.") from exc
    except Exception as exc:
        # Any other failure is treated as an internal error; details are logged upstream.
        raise PermanentUpstreamError("Unexpected error extracting PDF text.") from exc


def _get_dejavu_font_path() -> Optional[str]:
    """Return path to DejaVuSans.ttf if available (bundled or system). Used for full Unicode embedding."""
    # Bundled: app/fonts/DejaVuSans.ttf (relative to this file: app/services/pdf_io.py)
    this_dir = os.path.dirname(os.path.abspath(__file__))
    bundled = os.path.join(this_dir, "..", "fonts", "DejaVuSans.ttf")
    if os.path.isfile(bundled):
        return os.path.normpath(bundled)
    # Linux/Docker: package fonts-dejavu-core
    # macOS: Homebrew cask font-dejavu installs to ~/Library/Fonts
    system_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        os.path.expanduser("~/Library/Fonts/DejaVuSans.ttf"),
    ]
    for p in system_paths:
        if os.path.isfile(p):
            return p
    return None


def _ensure_unicode_font():
    """Register DejaVu Sans for Unicode embedding if available; otherwise canvas keeps default."""
    global _UNICODE_FONT_REGISTERED
    if _UNICODE_FONT_REGISTERED is not None:
        return
    path = _get_dejavu_font_path()
    if path is None:
        logger.warning(
            "unicode_font_not_found DejaVuSans.ttf not found; PDF may show missing glyphs for non-ASCII. "
            "Add app/fonts/DejaVuSans.ttf or install fonts-dejavu-core (Linux)."
        )
        _UNICODE_FONT_REGISTERED = ""
        return
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        pdfmetrics.registerFont(TTFont(FONT_NAME, path))
        _UNICODE_FONT_REGISTERED = FONT_NAME
        logger.info("unicode_font_ready path=%s", path)
    except Exception as e:
        logger.warning("unicode_font_register_failed path=%s error=%s", path, e)
        _UNICODE_FONT_REGISTERED = ""


def create_pdf_from_text(text: str, original_pages: int = 1) -> bytes:
    """Render plain text into a basic PDF document. Uses DejaVu Sans when available for full Unicode support."""

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    _ensure_unicode_font()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    if _UNICODE_FONT_REGISTERED:
        c.setFont(FONT_NAME, FONT_SIZE)

    width, height = A4
    margin = 50
    line_height = 14
    y = height - margin

    # Width-based wrapping: use rendered width so variable-width fonts (e.g. DejaVu) don't overflow
    font_for_measure = FONT_NAME if _UNICODE_FONT_REGISTERED else "Helvetica"
    max_text_width = width - 2 * margin

    def line_width(s: str) -> float:
        return c.stringWidth(s, font_for_measure, FONT_SIZE)

    paragraphs = text.split("\n\n")

    for para in paragraphs:
        words = para.split()
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word]) if current_line else word
            if current_line and line_width(test_line) > max_text_width:
                if y < margin + line_height:
                    c.showPage()
                    y = height - margin
                if _UNICODE_FONT_REGISTERED:
                    c.setFont(FONT_NAME, FONT_SIZE)

                c.drawString(margin, y, " ".join(current_line))
                y -= line_height
                current_line = [word]
            else:
                current_line.append(word)

        if current_line:
            if y < margin + line_height:
                c.showPage()
                y = height - margin
            if _UNICODE_FONT_REGISTERED:
                c.setFont(FONT_NAME, FONT_SIZE)
            c.drawString(margin, y, " ".join(current_line))
            y -= line_height

        y -= line_height // 2

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
