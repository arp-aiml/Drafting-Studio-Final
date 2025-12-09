from fastapi import APIRouter, Response, HTTPException
from app.models.schemas import DraftRequest, RefineRequest, ExportRequest, EmailRequest
from app.services.ai_engine import generate_legal_draft, refine_text, suggest_case_laws_ai
from app.services.scraper import scrape_legal_context
from app.services.export_engine import export_to_word, export_to_pdf
from app.services.validator import validate_draft
from app.services.email_engine import send_draft_email
from pydantic import BaseModel

# PREFIX DEFINED HERE: URL becomes http://localhost:8000/draft/generate
router = APIRouter(prefix="/draft", tags=["Drafting Studio"])

class CaseLawRequest(BaseModel):
    content: str

@router.post("/generate")
async def create_draft(request: DraftRequest):
    # 1. Research
    search_query = f"{request.template_type.replace('_', ' ')} {request.facts[:80]}"
    web_context = scrape_legal_context(search_query, request.template_type)
    
    # 2. Draft
    content = await generate_legal_draft(request, web_context)
    
    # 3. Validate
    warnings = validate_draft(content, request.template_type)
    
    return {"content": content, "research_note": web_context, "warnings": warnings}

@router.post("/refine")
async def modify_selection(request: RefineRequest):
    refined = await refine_text(request.selected_text, request.instruction)
    return {"refined_content": refined}

@router.post("/suggest-cases")
async def suggest_cases(request: CaseLawRequest):
    suggestions = await suggest_case_laws_ai(request.content)
    return {"suggestions": suggestions}

@router.post("/export/word")
async def download_word(request: ExportRequest):
    file_stream = export_to_word(request.content)
    headers = {'Content-Disposition': 'attachment; filename="Draft.docx"'}
    return Response(content=file_stream.getvalue(), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers=headers)

@router.post("/export/pdf")
async def download_pdf(request: ExportRequest):
    file_stream = export_to_pdf(request.content)
    headers = {'Content-Disposition': 'attachment; filename="Draft.pdf"'}
    return Response(content=file_stream.getvalue(), media_type="application/pdf", headers=headers)

@router.post("/send-email")
async def email_draft(request: EmailRequest):
    try:
        await send_draft_email(request.recipient, request.subject, request.content)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))