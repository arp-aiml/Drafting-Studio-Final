def build_legal_prompt(data, web_context):
    """
    Constructs the prompt for a Senior Legal Drafting AI.
    Output Format: Clean Markdown (No HTML).
    """
    
    system_persona = """
    ROLE: Senior Advocate (Supreme Court of India).
    TASK: Draft a professional legal document.
    FORMAT: Markdown only. 
    - Use '###' for Section Headers.
    - Use '**' for Bold text.
    - Use '>' for Blockquotes (citations).
    
    CRITICAL INSTRUCTION: You MUST use the specific Section Headers defined in the 'STRUCTURE' below. 
    Do not skip them, or the document will fail compliance checks.
    """

    templates = {
        # --- GST & INDIRECT TAX ---
        "gst_show_cause_reply": f"""
            **DOC:** Reply to GST Show Cause Notice (Form GST DRC-06).
            **CONTEXT:** {data.facts}
            **RESEARCHED LAW:** {web_context}
            
            **STRUCTURE (Strictly follow these headers):**
            ### Subject
            (Include Reference No and Date)
            ### Facts
            (Narrate the facts clearly)
            ### Submission
            (Legal arguments. Cite Section 16(2) or 73/74 explicitly. Use the researched law.)
            ### Prayer
            (Request to drop demand and personal hearing)
        """,

        "gst_appeal_draft": f"""
            **DOC:** GST Appeal (Form GST APL-01).
            **FACTS:** {data.facts}
            **STRUCTURE:**
            ### Statement of Facts
            ### Grounds of Appeal
            ### Relief
            ### Verification
        """,

        # --- CORPORATE ---
        "nda": f"""
            **DOC:** Non-Disclosure Agreement (NDA).
            **PARTIES:** {data.client_name} (Disclosing) AND {data.opposite_party} (Receiving).
            **CONTEXT:** {data.facts}
            
            **STRUCTURE (Strictly follow these headers):**
            ### Preamble
            ### Definition of Confidential Information
            ### Obligations
            (Strict non-disclosure duties)
            ### Exclusions
            (Standard exceptions)
            ### Term
            ### Indemnity
            ### Governing Law
        """,

        # --- EMPLOYMENT ---
        "employment_contract": f"""
            **DOC:** Employment Agreement.
            **ROLE:** {data.facts}
            
            **STRUCTURE (Strictly follow these headers):**
            ### Appointment
            ### Remuneration
            (CTC Details)
            ### Probation
            ### Termination
            ### Non-Compete
            (Reasonable restrictions under Sec 27)
        """,
        
        "commercial_lease": f"""
            **DOC:** Commercial Lease Deed.
            **PROPERTY:** {data.facts}
            **STRUCTURE:**
            ### Demised Premises
            ### Rent
            ### Security Deposit
            ### Term
            ### Termination
        """,

        # Fallback for others
        "board_resolution": f"""
            **DOC:** Board Resolution.
            **AGENDA:** {data.facts}
            **FORMAT:** Start with "CERTIFIED TRUE COPY..." followed by "RESOLVED THAT..."
        """
    }

    # Handling Fallback Context
    if "STATUTORY_FALLBACK" in web_context:
        context_block = "Standard Statutory Provisions. CITE specific Sections (e.g. Section 16, Section 27) from your internal legal knowledge."
    else:
        # It's a Verified Source
        context_block = web_context

    specific_instr = templates.get(data.template_type, f"Draft a formal legal document regarding: {data.facts}. Use context: {context_block}")

    return f"""
    {system_persona}
    {specific_instr}
    
    **TONE:** {data.tone} (Must be professional).
    **PARTIES:** {data.client_name} vs {data.opposite_party}.
    """