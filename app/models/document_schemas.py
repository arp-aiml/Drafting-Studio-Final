from pydantic import BaseModel
from typing import List, Optional

class Clause(BaseModel):
    clause_title: Optional[str] = None
    clause_text: Optional[str] = None

class DefenceRequirements(BaseModel):
    documents_required: List[str] = []
    previous_filings_required: List[str] = []
    internal_records_required: List[str] = []

class LegalityAnalysis(BaseModel):
    is_notice_legally_defective: Optional[bool] = None
    potential_defects: List[str] = []
    risk_level: Optional[str] = None

class SimilarCase(BaseModel):
    court: str
    case_name: str
    year: Optional[str] = None
    principle: str
    relevance: str

class DocumentAnalysisResponse(BaseModel):
    document_title: Optional[str] = None
    document_type: Optional[str] = None
    sender_party: Optional[str] = None
    receiver_party: Optional[str] = None

    key_points: List[str] = []
    clauses: List[Clause] = []

    defence_requirements: DefenceRequirements = DefenceRequirements()
    legality_analysis: LegalityAnalysis = LegalityAnalysis()
    similar_cases: List[SimilarCase] = []
