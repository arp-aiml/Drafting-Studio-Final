import re

def validate_draft(text: str, template_type: str):
    """
    Scans the draft to ensure mandatory legal sections are present based on the document type.
    """
    warnings = []
    
    # 1. Define Mandatory Keywords for each Document Type
    rules = {
        "gst_show_cause_reply": ["Subject", "Facts", "Submission", "Prayer"],
        "gst_appeal": ["Grounds of Appeal", "Statement of Facts", "Relief", "Verification"],
        "tax_scrutiny_reply": ["Subject", "Reference", "Reply", "Prayer"],
        "nda": ["Confidential Information", "Obligations", "Exclusions", "Term", "Indemnity"],
        "shareholders_agreement": ["Transfer of Shares", "Board", "Termination"],
        "board_resolution": ["CERTIFIED TRUE COPY", "RESOLVED THAT", "Board of Directors"],
        "employment_contract": ["Appointment", "Remuneration", "Probation", "Termination", "Notice Period"],
        "commercial_lease": ["Rent", "Security Deposit", "Term", "Termination"],
        "vendor_agreement": ["Scope of Services", "Payment", "Indemnity", "Confidentiality"],
        "affidavit": ["Solemnly Affirm", "Verification", "Deponent"],
        "mou": ["Purpose", "Parties", "Non-binding"]
    }
    
    required_keywords = rules.get(template_type, [])
    
    # 2. Check for Missing Sections
    for keyword in required_keywords:
        if not re.search(f"{keyword}", text, re.IGNORECASE):
            warnings.append(f"⚠️ Missing Critical Section: '{keyword}'")
            
    # 3. Check for Unfilled Placeholders
    if re.search(r"\[.*?\]", text):
        warnings.append("⚠️ Unfilled Placeholders detected (e.g., [DATE] or [AMOUNT]).")

    return warnings