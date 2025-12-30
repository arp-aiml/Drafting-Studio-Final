# prompts.py

def build_legal_prompt(data, web_context=None):
    """
    Builds a professional Indian legal drafting prompt with:
    - strict legal document structure
    - language control (English / Hindi / Bilingual)
    - tone conditioning
    """

    # ---------- Safe defaults to avoid None → API crash ----------
    client_name = getattr(data, "client_name", "") or ""
    opposite_party = getattr(data, "opposite_party", "") or ""
    facts = getattr(data, "facts", "") or ""
    tone = getattr(data, "tone", "formal") or "formal"
    language = getattr(data, "language", "english") or "english"

    # ---------- Context Block ----------
    if isinstance(web_context, str) and web_context.strip():
        context_block = web_context.strip()
    else:
        context_block = (
            "Apply relevant statutory provisions, settled principles of law, "
            "binding precedents of the Supreme Court of India and High Courts, "
            "and principles of natural justice applicable to the present matter."
        )

    # ---------- Language instruction ----------
    language = language.lower().strip()

    if language == "hindi":
        language_instruction = (
            "Draft the entire document in formal Legal Hindi using Devanagari script. "
            "Do not mix English words unless they are statutory or proper nouns."
        )
    elif language == "bilingual":
        language_instruction = (
            "Draft the document in bilingual format. "
            "For every paragraph, first write it in English, immediately followed by the same paragraph "
            "in formal Legal Hindi using Devanagari script. "
            "Ensure meaning equivalence and do not use transliteration (no Hinglish)."
        )
    else:
        language_instruction = (
            "Draft the entire document in formal Indian English appropriate for legal correspondence."
        )

    # ---------- Tone Instruction ----------
    tone = tone.lower()
    if tone.startswith("persu"):
        tone_instruction = "Maintain a persuasive professional tone."
    elif tone.startswith("firm"):
        tone_instruction = "Maintain a firm, assertive legal tone."
    else:
        tone_instruction = "Maintain a formal, neutral legal tone."

    # ---------- Final Prompt ----------
    prompt = f"""
You are a Senior Advocate practising before the Supreme Court of India and various High Courts.

{language_instruction}
{tone_instruction}

You are required to draft a formal legal document strictly in plain text format.
Do not use bullet points, numbering, markdown, headings, asterisks, or section labels.
Write only continuous professional legal paragraphs.

The draft must follow the structural format used in real Indian legal notices and replies.

The draft must begin exactly as follows:

To,
{opposite_party}
[Complete Postal Address]

Date: [Insert Date]

Subject: [Concise subject describing the nature of the reply / proceedings]

Sir / Madam,

BODY OF THE DOCUMENT:

Identify the client {client_name} and the authority or party addressed.
Refer to the notice, order, letter, or communication that is being replied to.

Narrate the facts in clear chronological sequence based on the following facts/instructions:
{facts}

Respond to allegations, claims, and assertions made by the opposite party by stating what is admitted,
what is denied, and on what legal and factual grounds it is denied.

Apply legal reasoning based on the following context where relevant:
{context_block}

Use standard Indian legal drafting terminology including expressions such as
"it is respectfully submitted", "without prejudice", "it is denied", "it is submitted that".

Do NOT invent facts, dates, numbers, or case laws beyond what is provided.
Do NOT assume attachments or annexures unless explicitly stated.

CONCLUSION AND CLOSING:

Conclude with a clear statement of reliefs sought and reservation of rights and remedies.

The draft must end exactly as follows:

Yours faithfully,

For {client_name}

Authorized Signatory

Ensure the final output reads like a real legal document that can be printed, signed, and issued without modification.
"""

    return prompt.strip()
