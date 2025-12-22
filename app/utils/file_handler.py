# file_handler.py
import docx
from io import BytesIO
import pytesseract
from pdf2image import convert_from_bytes
import pdfplumber

MIN_TEXT_LEN = 20  # Lowered threshold

def ocr_pdf(file_bytes: bytes) -> str:
    try:
        images = convert_from_bytes(file_bytes)
    except Exception:
        return ""

    text = ""
    for img in images:
        try:
            text += pytesseract.image_to_string(img) + "\n"
        except Exception:
            continue

    return text.strip()


def read_file_content(uploaded_file, force_ocr: bool = False) -> str:
    """
    Extract text from uploaded file.

    - Primary extraction first
    - OCR fallback only if primary fails OR force_ocr=True
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

    text = ""

    # DOCX
    if filename.endswith(".docx"):
        try:
            doc = docx.Document(BytesIO(raw_bytes))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            text = ""

    # TXT
    elif filename.endswith(".txt"):
        try:
            text = raw_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

    # PDF
    elif filename.endswith(".pdf"):
        # HARD GUARD
        if not raw_bytes.startswith(b"%PDF"):
            return ""

        # 1️⃣ pdfplumber primary
        try:
            with pdfplumber.open(BytesIO(raw_bytes)) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception:
            text = ""

        # 2️⃣ Fallback OCR if not enough text or force_ocr
        if force_ocr or len(text.strip()) < MIN_TEXT_LEN:
            text = ocr_pdf(raw_bytes)

    # Return if enough text
    return text.strip() if len(text.strip()) >= MIN_TEXT_LEN else ""
