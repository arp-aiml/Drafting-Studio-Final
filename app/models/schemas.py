from pydantic import BaseModel, EmailStr
from typing import Optional

class DraftRequest(BaseModel):
    template_type: str
    client_name: str
    opposite_party: str
    facts: str
    tone: str
    template_text: Optional[str] = None 
    doc_hash: Optional[str] = None

class RefineRequest(BaseModel):
    selected_text: str
    instruction: str

class ExportRequest(BaseModel):
    content: str

class EmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    content: str


class DraftRequest(BaseModel):
    template_type: str | None = None
    client_name: str
    opposite_party: str
    facts: str
    tone: str | None = "formal"
    web_context: str | None = None
    language: str = "english"   # allowed: english, hindi, bilingual
