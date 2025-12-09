from pydantic import BaseModel, EmailStr
from typing import Optional

class DraftRequest(BaseModel):
    template_type: str
    client_name: str
    opposite_party: str
    facts: str
    tone: str
    template_text: Optional[str] = None 

class RefineRequest(BaseModel):
    selected_text: str
    instruction: str

class ExportRequest(BaseModel):
    content: str

class EmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    content: str