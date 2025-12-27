def build_legal_prompt(data, web_context):
    """
    Plain-text professional Indian legal drafting prompt
    with mandatory TO / SUBJECT structure.
    """

    if isinstance(web_context, str) and web_context.strip():
        context_block = web_context
    else:
        context_block = (
            "Apply relevant statutory provisions, settled principles of law, "
            "and principles of natural justice applicable to the subject matter."
        )

    return f"""
You are a Senior Advocate practising before the Supreme Court of India.

Draft a formal Indian legal document strictly in plain text format.
Do not use bullet points, numbering, markdown, asterisks, or headings.
Write in continuous professional legal paragraphs.

The draft must follow the exact structural format used in real legal notices
and replies issued by Indian law offices.

DOCUMENT STRUCTURE (MANDATORY):

The draft must begin exactly in the following manner:

To,
{data.opposite_party}
[Complete Postal Address]

Date: [Insert Date]

Subject: [Concise subject describing the nature of the reply / proceedings]

Sir / Madam,

BODY OF THE DOCUMENT:

Begin by identifying the client {data.client_name}, the authority or party addressed,
and the reference to the notice, communication, or proceedings to which this document
is a reply.

Set out the factual background in clear chronological paragraphs.

Thereafter, respond to the allegations, claims, or issues raised by the opposite party
with proper factual explanations, legal submissions, and statutory support.

Apply the following legal context where relevant:

{context_block}

Maintain a formal Indian legal drafting tone using expressions such as
"it is respectfully submitted", "without prejudice", "it is denied",
"it is submitted that", and similar professional language.

Avoid informal language, lists, or formatting.

CONCLUSION AND CLOSING:

Conclude with a paragraph clearly stating the reliefs sought, requests for
withdrawal or dropping of proceedings, and reservation of rights.

The document must end exactly in the following format:

Yours faithfully,

For {data.client_name}

Authorized Signatory

Ensure the final output appears like a real legal draft capable of being
printed, signed, and issued without any modification.
"""
