# file_handler.py
import docx
from io import BytesIO
import pytesseract
from pdf2image import convert_from_bytes
import pdfplumber

MIN_TEXT_LEN = 50

def ocr_pdf(file_bytes: bytes) -> str:
    try:
        images = convert_from_bytes(file_bytes)
    except Exception:
        # 🔇 absolutely silent
        return ""

    text = ""
    for img in images:
        try:
            text += pytesseract.image_to_string(img) + "\n"
        except Exception:
            continue

    return text.strip()


def read_file_content(uploaded_file) -> str:
    """
    NEVER throws
    NEVER crashes
    Returns "" if unreadable
    """

    if uploaded_file is None:
        return ""

    filename = (
        getattr(uploaded_file, "filename", None)
        or getattr(uploaded_file, "name", "")
    ).lower()

    try:
        if hasattr(uploaded_file, "file"):
            raw_bytes = uploaded_file.file.read()
            uploaded_file.file.seek(0)
        else:
            raw_bytes = uploaded_file.getvalue()
    except Exception:
        return ""

    # ---------- DOCX ----------
    if filename.endswith(".docx"):
        try:
            doc = docx.Document(BytesIO(raw_bytes))
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            return ""

    # ---------- TXT ----------
    if filename.endswith(".txt"):
        try:
            return raw_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    # ---------- PDF ----------
    if filename.endswith(".pdf"):
        text = ""

        # 🚫 HARD GUARD: non-PDF container (FORM / binary junk)
        if not raw_bytes.startswith(b"%PDF"):
            return ""

        # 1️⃣ pdfplumber ONLY (skip PyPDF completely)
        try:
            with pdfplumber.open(BytesIO(raw_bytes)) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception:
            pass

        if len(text.strip()) >= MIN_TEXT_LEN:
            return text.strip()

        # 2️⃣ OCR fallback (best effort)
        text = ocr_pdf(raw_bytes)

        if len(text.strip()) >= MIN_TEXT_LEN:
            return text.strip()

        return ""

    return ""
