import os
from openai import OpenAI
from app.utils.prompts import build_legal_prompt
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_NAME = "gpt-4o-mini" 

async def generate_legal_draft(data, web_context=""):
    try:
        if data.template_text and len(data.template_text) > 20:
            system_instruction = "You are a Senior Legal Editor. Fill placeholders and adapt the User's provided template based on their facts. Preserve original clauses."
            user_content = f"TEMPLATE:\n{data.template_text}\n\nFACTS:\n{data.facts}\n\nCONTEXT:\n{web_context}"
        else:
            system_instruction = "You are LexFlow AI. Draft authoritative legal documents in Markdown."
            user_content = build_legal_prompt(data, web_context)

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

async def refine_text(text, instruction):
    """Refines the ENTIRE document."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a Senior Legal Editor. Rewrite the legal document according to the instruction. Output only the refined text."},
                {"role": "user", "content": f"Instruction: {instruction}\n\nDocument Content:\n{text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return str(e)

async def suggest_case_laws_ai(text):
    """Suggests RELEVANT SECTIONS and CASE LAWS."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a Legal Researcher. Analyze the text and suggest relevant **Indian Statutory Provisions (Sections/Acts)** and **Case Laws**. \n\nOutput Format:\n**Relevant Laws:**\n- Section X of [Act Name]: [Brief Explanation]\n\n**Case Precedents:**\n- Case Name (Year): [One line summary]"},
                {"role": "user", "content": f"Analyze this draft and find legal grounds:\n{text[:3000]}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Error fetching legal research."