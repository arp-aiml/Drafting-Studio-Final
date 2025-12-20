# document_intelligence.py
import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI
import asyncio

from app.utils.retrieval import retrieve_top_k_chunks

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "gpt-4o-mini"

MAX_LLM_CHARS = 6000

async def analyze_legal_document(document_text: str, doc_hash: str = None):
    """
    Legal analysis using embedded document chunks (RAG).
    Handles large documents safely.
    If doc_hash is provided, retrieves only from that document's index.
    """
    try:
        # -----------------------------
        # 1️⃣ RAG: Retrieve top-k relevant chunks
        # -----------------------------
        query_text = document_text[:1000]  # initial slice for embedding query
        retrieved_chunks = []

        # ✅ Only use RAG if document has meaningful text
        if len(document_text.strip()) > 200:
            retrieved_chunks = retrieve_top_k_chunks(
                query=query_text,
                k=5,
                doc_hash=doc_hash  # now per-file retrieval
            )

        context = "\n\n".join(retrieved_chunks)

        if not context.strip():
            context = document_text[:3000]

        if len(context) > MAX_LLM_CHARS:
            context = context[:MAX_LLM_CHARS]  # trim for LLM

        if not context.strip():
            # fallback to first 3k chars
            context = document_text[:3000]

        # -----------------------------
        # 2️⃣ SYSTEM PROMPT
        # -----------------------------
        system_prompt = """
You are a Senior Indian Litigation and Defence Lawyer.

You are analyzing a legal notice / judgment / order for the purpose of
defence preparation and risk assessment.

You MUST extract structured legal information even if the document is
incomplete or imperfectly drafted.

If information is missing, infer cautiously and mark assumptions clearly.
DO NOT default to "no defect" unless compliance is explicit.

----------------------------------
REQUIRED OUTPUT (STRICT JSON ONLY)
----------------------------------

{
  "document_metadata": {
    "document_title": string | null,
    "document_type": string | null,
    "issuing_authority_or_court": string | null,
    "addressed_to": string | null,
    "other_parties_involved": [string]
  },

  "key_points_summary": [
    string
  ],

  "defence_preparation_checklist": [
    string
  ],

  "legality_assessment": {
    "is_notice_legally_valid": true | false | null,
    "authority_error_possible": true | false | null,
    "party_non_compliance_possible": true | false | null,
    "identified_issues_or_defects": [string],
    "overall_risk_level": "low" | "medium" | "high"
  },

  "relevant_judicial_precedents": [
    {
      "case_name": string,
      "court": "Supreme Court" | "High Court",
      "legal_principle": string,
      "relevance_to_present_document": string
    }
  ]
}

----------------------------------
ANALYSIS RULES
----------------------------------
- Use the provided document + embedded context
- If legality is unclear → risk MUST be "medium"
- If rights, jurisdiction, procedure, or authority are questionable → flag defects
- Do NOT write explanations outside JSON
"""

        # -----------------------------
        # 3️⃣ LLM CALL
        # -----------------------------
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"DOCUMENT CONTENT:\n{context}"}
                ],
                temperature=0
            )
            raw_output = response.choices[0].message.content.strip()
        except Exception as e:
            print("LLM call failed:", e)
            raise ValueError(f"LLM call failed: {e}")

        # -----------------------------
        # 4️⃣ Parse JSON safely
        # -----------------------------
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw_output, re.DOTALL)
            if not match:
                raise ValueError("AI output not valid JSON")
            return json.loads(match.group())

    except Exception as e:
        print("Document analysis failed:", e)
        raise ValueError(f"Document analysis failed: {e}")
