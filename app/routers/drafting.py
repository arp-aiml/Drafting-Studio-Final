#drafting.py
from fastapi import APIRouter, Response, HTTPException, UploadFile, File, Body
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
from app.utils.chunk_and_index import build_index_from_text
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

    # 1️⃣ Parse ONCE
    document_text = read_file_content(file)
    clean_text = document_text.replace("\x00", "").strip()

    if len(clean_text) < 50:
        raise HTTPException(
            status_code=400,
            detail="This PDF cannot be read programmatically."
        )

    # 2️⃣ Index DIRECTLY from TEXT (NO temp PDF nonsense)
    doc_hash = build_index_from_text(
        clean_text,
        source_name=file.filename
    )

    if not doc_hash:
        raise HTTPException(
            status_code=400,
            detail="Indexing failed: empty document."
        )

    # 3️⃣ LLM analysis (doc_hash aware)
    analysis_model = await analyze_legal_document(
        clean_text,
        doc_hash=doc_hash
    )
    analysis = jsonable_encoder(analysis_model)

    # 4️⃣ Optional enrichment (never crash)
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

    return {
        **analysis,
        "doc_hash": doc_hash
    }




# =========================
# MANUAL EMBEDDING ENDPOINT
# =========================
@router.post("/embed-document")
async def embed_document(file: UploadFile = File(...)):
    text = read_file_content(file)
    clean_text = text.replace("\x00", "").strip()

    if len(clean_text) < 50:
        raise HTTPException(400, "No readable text found in document")

    doc_hash = build_index_from_text(
        clean_text,
        source_name=file.filename
    )

    return {"status": "embedded", "doc_hash": doc_hash}


@router.post("/generate")
async def generate_draft_endpoint(data: DraftRequest = Body(...)):
    """
    Generates a legal draft based on template, client, opposite party, facts, and tone.
    """
    try:
        # 1️⃣ Generate draft using AI engine
        draft_data = await generate_legal_draft(data)  # only `data` argument

        # 2️⃣ draft_data already includes warnings from validate_draft inside AI engine
        return draft_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))