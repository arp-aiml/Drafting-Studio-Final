#drafting.py
# drafting.py
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


# =========================
# LOAD FAISS ONCE (CRITICAL)
# =========================
INDEX, METADATA = load_faiss_index()


class CaseLawRequest(BaseModel):
    content: str


# =========================
# DRAFT GENERATION (RAG)
# =========================
@router.post("/generate")
async def create_draft(request: DraftRequest):
    """
    Draft generation using:
    - Embedded document context (RAG)
    - Web/statutory context
    """

    # 1️⃣ Web research
    search_query = f"{request.template_type.replace('_', ' ')} {request.facts[:80]}"
    web_context = scrape_legal_context(search_query, request.template_type)

    # 2️⃣ Embedded document context
    embedded_context = ""

    if INDEX and METADATA:
        chunks = retrieve_top_k_chunks(
            index=INDEX,
            metadata=METADATA,
            query=request.facts,
            k=3
        )
        embedded_context = "\n\n".join(chunks)

    final_context = f"""
EMBEDDED DOCUMENT CONTEXT:
{embedded_context}

STATUTORY / WEB CONTEXT:
{web_context}
"""

    # 3️⃣ Draft generation
    content = await generate_legal_draft(request, final_context)
    warnings = validate_draft(content, request.template_type)

    return {
        "content": content,
        "warnings": warnings
    }


# =========================
# REFINE SELECTION
# =========================
@router.post("/refine")
async def modify_selection(request: RefineRequest):
    refined = await refine_text(request.selected_text, request.instruction)
    return {"refined_content": refined}


# =========================
# CASE LAW SUGGESTIONS
# =========================
@router.post("/suggest-cases")
async def suggest_cases(request: CaseLawRequest):
    suggestions = await suggest_case_laws_ai(request.content)
    return {"suggestions": suggestions}


# =========================
# EXPORTS
# =========================
@router.post("/export/word")
async def download_word(request: ExportRequest):
    file_stream = export_to_word(request.content)
    return Response(
        content=file_stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="Draft.docx"'}
    )


@router.post("/export/pdf")
async def download_pdf(request: ExportRequest):
    file_stream = export_to_pdf(request.content)
    return Response(
        content=file_stream.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="Draft.pdf"'}
    )


# =========================
# EMAIL
# =========================
@router.post("/send-email")
async def email_draft(request: EmailRequest):
    try:
        await send_draft_email(
            request.recipient,
            request.subject,
            request.content
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# DOCUMENT ANALYSIS (UPLOAD → EMBED → ANALYSE)
# =========================
@router.post("/analyze-document")
async def analyze_document(file: UploadFile = File(...)):
    # 1️⃣ Read file safely
    document_text = read_file_content(file)
    clean_text = document_text.replace("\x00", "").strip()

    # 🚫 HARD STOP — unreadable PDF
    if len(clean_text) < 50:
        raise HTTPException(
            status_code=400,
            detail="This PDF cannot be read programmatically. Please upload a standard text-based PDF."
        )

    # 2️⃣ FAISS indexing (ONLY if text is valid)
    suffix = os.path.splitext(file.filename)[1] or ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(clean_text.encode("utf-8"))
        temp_path = tmp.name

    try:
        build_index_from_file(temp_path)
    finally:
        os.unlink(temp_path)

    # 3️⃣ LLM legal analysis
    analysis_model = await analyze_legal_document(clean_text)
    analysis = jsonable_encoder(analysis_model)

    # 4️⃣ Optional enrichment (safe)
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
        # 🔇 enrichment must NEVER fail request
        pass

    return analysis


# =========================
# MANUAL EMBEDDING ENDPOINT
# =========================
@router.post("/embed-document")
async def embed_document(file: UploadFile = File(...)):
    text = read_file_content(file)
    clean_text = text.replace("\x00", "").strip()

    if len(clean_text) < 300:
        raise HTTPException(400, "No readable text found in document")

    build_index_from_text(
        clean_text,
        source_name=file.filename
    )

    return {"status": "embedded"}
