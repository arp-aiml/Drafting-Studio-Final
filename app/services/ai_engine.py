import os
from dotenv import load_dotenv
from openai import OpenAI

from app.models.schemas import DraftRequest          # ✅ REQUIRED
from app.services.validator import validate_draft   # ✅ REQUIRED
from app.utils.prompts import build_legal_prompt
from app.utils.retrieval import retrieve_top_k_chunks

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "gpt-4o-mini"


# ======================================================
# MAIN DRAFT GENERATOR (NOW RAG-AWARE)
# ======================================================
async def generate_legal_draft(data: DraftRequest, web_context: str = ""):
    """
    Generates legal draft.
    Uses embeddings ONLY if doc_hash is present.
    """
    # -------------------------
    # 1️⃣ RAG CONTEXT
    # -------------------------
    rag_context = web_context

    if getattr(data, "doc_hash", None) and not rag_context:
        chunks = retrieve_top_k_chunks(
            query=(data.facts or "")[:500],
            k=5,
            doc_hash=data.doc_hash
        )
        rag_context = "\n\n".join(chunks)

    # -------------------------
    # 2️⃣ PROMPT BUILDING
    # -------------------------
    prompt = build_legal_prompt(
        data=data,
        web_context=rag_context
    )

    # -------------------------
    # 3️⃣ LLM CALL
    # -------------------------
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a Senior Indian Legal Drafting AI."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    draft_text = response.choices[0].message.content.strip()

    # -------------------------
    # 4️⃣ VALIDATION (template_type required)
    # -------------------------
    warnings = validate_draft(draft_text, data.template_type)

    return {
        "content": draft_text,
        "warnings": warnings
    }


# ======================================================
# REFINEMENT TOOL (UNCHANGED)
# ======================================================
async def refine_text(text, instruction):
    """Refines the ENTIRE document."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Senior Legal Editor. "
                        "Rewrite the legal document according to the instruction. "
                        "Output only the refined text."
                    )
                },
                {
                    "role": "user",
                    "content": f"Instruction: {instruction}\n\nDocument Content:\n{text}"
                }
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return str(e)


# ======================================================
# CASE LAW SUGGESTION TOOL (UNCHANGED)
# ======================================================
async def suggest_case_laws_ai(text):
    """Suggests RELEVANT SECTIONS and CASE LAWS."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Legal Researcher. Analyze the text and suggest "
                        "**Indian Statutory Provisions (Sections/Acts)** and "
                        "**Case Laws**.\n\n"
                        "Output Format:\n"
                        "**Relevant Laws:**\n"
                        "- Section X of [Act Name]: [Brief Explanation]\n\n"
                        "**Case Precedents:**\n"
                        "- Case Name (Year): [One line summary]"
                    )
                },
                {
                    "role": "user",
                    "content": f"Analyze this draft and find legal grounds:\n{text[:3000]}"
                }
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Error fetching legal research."
