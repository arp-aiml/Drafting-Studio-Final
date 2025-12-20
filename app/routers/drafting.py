#drafting.py
from fastapi import APIRouter, Response, HTTPException, UploadFile, File
from pydantic import BaseModel
import os
import tempfile
import asyncio
from fastapi.encoders import jsonable_encoder

from app.models.schemas import DraftRequest, RefineRequest, ExportRequest, EmailRequest
from app.services.ai_engine import generate_legal_draft, refine_text, suggest_case_laws_ai
from app.services.export_engine import export_to_word, export_to_pdf
from app.services.validator import validate_draft
from app.services.email_engine import send_draft_email
from app.services.document_intelligence import analyze_legal_document
from app.utils.file_handler import read_file_content
from app.utils.chunk_and_index import build_index_from_file, load_faiss_index
from app.utils.retrieval import retrieve_top_k_chunks
from app.services.scraper import scrape_legal_context

router = APIRouter(prefix="/draft", tags=["Drafting Studio"])


class CaseLawRequest(BaseModel):
    content: str


# =========================
# DOCUMENT ANALYSIS (UPLOAD → EMBED → ANALYSE)
# =========================
@router.post("/analyze-document")
async def analyze_document(file: UploadFile = File(...)):
    import asyncio

    document_text = read_file_content(file)
    clean_text = document_text.replace("\x00", "").strip()

    if len(clean_text) < 50:
        raise HTTPException(
            status_code=400,
            detail="This PDF cannot be read programmatically."
        )

    suffix = os.path.splitext(file.filename)[1] or ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(clean_text.encode("utf-8"))
        temp_path = tmp.name

    try:
        doc_hash = build_index_from_file(temp_path)
        if not doc_hash:
            raise HTTPException(
                status_code=400,
                detail="No readable text to index. Analysis aborted."
            )
    finally:
        os.unlink(temp_path)

    # Pass doc_hash to LLM analysis
    analysis_model = await analyze_legal_document(clean_text, doc_hash=doc_hash)
    analysis = jsonable_encoder(analysis_model)

    # Safe enrichment
    try:
        scraped = await asyncio.to_thread(
            scrape_legal_context,
            clean_text[:150],
            "generic"
        )
        if isinstance(scraped, list):
            analysis.setdefault("relevant_judicial_precedents", [])
            analysis["relevant_judicial_precedents"].extend(scraped)
    except Exception:
        pass

    return analysis



# =========================
# MANUAL EMBEDDING ENDPOINT
# =========================
@router.post("/embed-document")
async def embed_document(file: UploadFile = File(...)):
    text = read_file_content(file)
    clean_text = text.replace("\x00", "").strip()

    if len(clean_text) < 50:
        raise HTTPException(400, "No readable text found in document")

    doc_hash = build_index_from_file(
        file_path=tempfile.NamedTemporaryFile(delete=False).name
    )

    return {"status": "embedded", "doc_hash": doc_hash}
