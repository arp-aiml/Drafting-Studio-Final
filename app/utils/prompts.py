def build_legal_prompt(data, web_context):
    """
    Constructs the prompt for a Senior Legal Drafting AI.
    Output Format: Clean Markdown (No HTML).
    """

    # =============================
    # 1️⃣ SYSTEM PERSONA
    # =============================
    system_persona = """
ROLE: Senior Advocate (Supreme Court of India).
TASK: Draft a professional legal document.
FORMAT: Markdown only.
- Use '###' for Section Headers.
- Use '**' for Bold text.
- Use '>' for Blockquotes (citations).

CRITICAL INSTRUCTION:
You MUST use the exact Section Headers defined below.
Do NOT skip or merge sections.
"""

    # =============================
    # 2️⃣ SAFE CONTEXT RESOLUTION
    # =============================
    if isinstance(web_context, str) and web_context.strip():
        if "STATUTORY_FALLBACK" in web_context:
            context_block = (
                "Standard GST statutory provisions and settled judicial principles. "
                "Rely on Sections such as Section 16 (ITC), Sections 73/74 (Demand), "
                "limitation provisions, and principles of natural justice."
            )
        else:
            context_block = web_context
    else:
        context_block = (
            "No external case law retrieved. "
            "Apply settled GST statutory provisions and principles of law."
        )

    # =============================
    # 3️⃣ TEMPLATES (NOW SAFE)
    # =============================
    templates = {
        "gst_show_cause_reply": f"""
**DOC:** Reply to GST Show Cause Notice  
**CLIENT (Noticee):** {data.client_name}  
**AUTHORITY (Issuing Authority):** {data.opposite_party}  

**NOTICE FACTS / ALLEGATIONS (AS RECEIVED):**  
{data.facts}

**LEGAL RESEARCH CONTEXT (STATUTES / CASE LAW):**  
{context_block}

========================
STRICT STRUCTURE — DO NOT CHANGE
========================

### 1. Introduction of the Noticee
Introduce the Noticee including:
• Nature of business  
• GST registration details  
• Jurisdiction  
• Compliance history  

---

### 2. Brief Summary of the Notice & Issues Raised
Summarise:
• Nature of proceedings  
• Period involved  
• Allegations  
• Amount demanded (if any)  

---

### 3. Point-wise Reply to Allegations
For **each allegation**:
• Quote/paraphrase allegation  
• Factual rebuttal  
• Legal rebuttal  
• Relevant GST provisions  

---

### 4. Legality and Sustainability of the Demand
Examine:
• Jurisdiction  
• Limitation  
• Wrong invocation of sections  
• Violation of natural justice  
• Vague or mechanical notice  

Clearly conclude whether the demand is:
• Unsustainable in law, OR  
• Procedurally defective, OR  
• Requires reconsideration  

---

### 5. Closing Submissions & Prayer
Pray for:
• Dropping of proceedings  
• Personal hearing  
• Reasoned order  

========================
COMPLIANCE RULES
========================
• DO NOT skip sections  
• DO NOT merge sections  
• Maintain formal Indian legal drafting style  
""",

        "gst_appeal_draft": f"""
**DOC:** GST Appeal (Form GST APL-01)
### Statement of Facts
### Grounds of Appeal
### Relief
### Verification
""",
    }

    # =============================
    # 4️⃣ TEMPLATE SELECTION
    # =============================
    specific_instr = templates.get(
        data.template_type,
        f"Draft a formal legal document regarding: {data.facts}"
    )

    # =============================
    # 5️⃣ FINAL PROMPT
    # =============================
    return f"""
{system_persona}
{specific_instr}

**TONE:** {data.tone}  
**PARTIES:** {data.client_name} vs {data.opposite_party}
"""
