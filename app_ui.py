# app_ui.py
import os
import json
import pickle
import streamlit as st
import requests
from app.utils.file_handler import read_file_content

API_URL = "http://127.0.0.1:8000/draft"
INDEX_DATA_DIR = "index_data"
METADATA_FILE = os.path.join(INDEX_DATA_DIR, "metadata.pkl")


st.set_page_config(page_title="LexFlow Studio", layout="wide", page_icon="⚖️")

def populate_facts_from_keypoints(key_points):
    st.session_state.facts = "\n".join(key_points)

# ===================== CSS =====================
st.markdown("""
<style>
    .stTextArea textarea {
        font-family: 'Times New Roman', serif;
        font-size: 16px;
        line-height: 1.6;
        color: #000;
        background-color: #fff;
        border: 1px solid #ccc;
    }
    .main { background-color: #f9f9f9; }
</style>
""", unsafe_allow_html=True)

st.title("⚖️ LexFlow AI - Upload and Analyze")

uploaded_file = st.file_uploader("Upload Legal Document for Analysis", type=["docx", "pdf", "txt"])
if uploaded_file:
    uploaded_text = read_file_content(uploaded_file)
    st.success(f"Loaded {len(uploaded_text)} characters")

    if st.button("🔍 Analyze Document"):
        uploaded_file.seek(0)
        with st.spinner("Analyzing document..."):
            try:
                res = requests.post(
                    f"{API_URL}/analyze-document",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                    timeout=600
                )
                if res.status_code == 200:
                    st.session_state["doc_analysis"] = res.json()
                    st.toast("Document analyzed successfully")
                else:
                    st.error(f"Analysis failed: {res.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error analyzing document: {e}")

st.title("⚖️ LexFlow AI - Drafting Studio")


# ===================== DOCUMENT INTELLIGENCE =====================
if st.session_state.get("doc_analysis"):
    d = st.session_state["doc_analysis"]

    meta = d.get("document_metadata", {})
    key_points = d.get("key_points_summary", [])
    defence = d.get("defence_preparation_checklist", [])
    legality = d.get("legality_assessment", {})
    cases = d.get("relevant_judicial_precedents", [])

    with st.expander("📄 Document Intelligence", expanded=True):
        st.markdown(f"### {meta.get('document_title') or 'Uploaded Legal Notice'}")
        st.write("**Document Type:**", meta.get("document_type") or "Not identified")
        st.write("**Issued By / Court:**", meta.get("issuing_authority_or_court") or "Not identified")
        st.write("**Addressed To:**", meta.get("addressed_to") or "Not identified")

        other_parties = meta.get("other_parties_involved", [])
        if other_parties:
            st.write("**Other Parties:**", ", ".join(other_parties))

        st.markdown("### 🧾 Key Points / Summary")
        if key_points:
            for p in key_points:
                st.write(f"- {p}")
        else:
            st.info("No key points identified.")

        st.markdown("### 🗂 Defence Preparation Checklist")
        if defence:
            for item in defence:
                st.write(f"- {item}")
        else:
            st.info("No defence checklist items identified.")

        st.markdown("### ⚠️ Notice Legality Assessment")
        is_valid = legality.get("is_notice_legally_valid")
        authority_error = legality.get("authority_error_possible")
        party_fault = legality.get("party_non_compliance_possible")
        risk = legality.get("overall_risk_level")
        defects = legality.get("identified_issues_or_defects", [])

        if is_valid is False:
            st.error("⚠️ The notice appears to suffer from legal/procedural defects.")
        elif is_valid is True:
            st.success("✅ The notice appears legally valid.")
        else:
            st.info("ℹ️ Cannot conclusively determine legality from text alone.")

        if authority_error:
            st.warning("⚖️ Possible issuing authority error.")
        if party_fault:
            st.warning("📌 Possible non-compliance by noticee.")

        if risk:
            if risk.lower() == "high":
                st.error(f"Overall Risk Level: {risk.upper()}")
            elif risk.lower() == "medium":
                st.warning(f"Overall Risk Level: {risk.upper()}")
            else:
                st.success(f"Overall Risk Level: {risk.upper()}")

        if defects:
            st.markdown("**Identified Issues:**")
            for issue in defects:
                st.warning(issue)

        # ---------- Judicial Precedents ----------
        st.markdown("### ⚖️ Relevant Judicial Precedents")
        if cases:
            for case in cases:
                st.markdown(
                    f"**{case.get('case_name', 'Unnamed Case')} – {case.get('court', '—')}**\n"
                    f"• Legal Principle: {case.get('legal_principle', 'Not specified')}\n"
                    f"• Relevance: {case.get('relevance_to_present_document', 'Not specified')}"
                )
        else:
            st.info("No relevant judicial precedents found.")

        if st.button("🪄 Use Key Points as Facts"):
            st.session_state.populate_from_doc = True
            st.rerun()


# ===================== STATE =====================
defaults = {
    "draft": "",
    "warnings": [],
    "case_law_suggestions": "",
    "doc_analysis": None,
    "client_name": "",
    "opposite_party": "",
    "facts": "",
    "document_title": "",
    "doc_hash": None,
}


if "populate_from_doc" not in st.session_state:
    st.session_state["populate_from_doc"] = False

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ===================== HELPERS =====================
def force_refresh_editor(new_text=""):
    st.session_state["draft"] = new_text
    st.rerun()

def apply_global_refinement(instruction):
    if not st.session_state["draft"]:
        st.toast("⚠️ Editor is empty")
        return
    try:
        res = requests.post(
            f"{API_URL}/refine",
            json={"selected_text": st.session_state["draft"], "instruction": instruction},
            timeout=300
        )
        if res.status_code == 200:
            force_refresh_editor(res.json()["refined_content"])
        else:
            st.error(f"Refinement failed: {res.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")

def fetch_case_laws():
    if not st.session_state["draft"]:
        return
    try:
        res = requests.post(
            f"{API_URL}/suggest-cases",
            json={"content": st.session_state["draft"]},
            timeout=300
        )
        if res.status_code == 200:
            st.session_state["case_law_suggestions"] = res.json().get("suggestions", "")
            st.rerun()
        else:
            st.error(f"Case law fetch failed: {res.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")


def get_available_documents():
    base_dir = "index_data"
    docs_map = {}

    if not os.path.exists(base_dir):
        return docs_map

    for doc_hash in os.listdir(base_dir):
        doc_dir = os.path.join(base_dir, doc_hash)

        if not os.path.isdir(doc_dir):
            continue

        metadata_path = os.path.join(doc_dir, "doc_metadata.pkl")
        if not os.path.exists(metadata_path):
            continue

        try:
            with open(metadata_path, "rb") as f:
                data = pickle.load(f)

            file_name = data.get("file_name")
            if file_name:
                docs_map[file_name] = doc_hash

        except Exception:
            continue

    return docs_map


def load_doc_analysis_by_hash(doc_hash):
    folder = os.path.join("index_data", doc_hash)
    doc_meta_path = os.path.join(folder, "doc_metadata.pkl")
    chunk_meta_path = os.path.join(folder, "chunks_metadata.pkl")

    if not os.path.exists(doc_meta_path) or not os.path.exists(chunk_meta_path):
        return None

    with open(doc_meta_path, "rb") as f:
        doc_meta = pickle.load(f)

    with open(chunk_meta_path, "rb") as f:
        chunks = pickle.load(f)

    full_text = "\n".join(c["text"] for c in chunks)

    # Simple heuristics for client/opposite
    client, opposite = "", ""
    for line in full_text.splitlines():
        if "versus" in line.lower() or "vs." in line.lower():
            parts = line.lower().replace("vs.", "vs").split("vs")
            if len(parts) == 2:
                client = parts[0].strip().title()
                opposite = parts[1].strip().title()
                break

    return {
        "client_name": doc_meta.get("addressed_to", client),  # fallback
        "opposite_party": doc_meta.get("issuing_authority_or_court", opposite),  # fallback
        "facts": full_text,  # store FULL text here, not just first 3000 chars
        "document_metadata": doc_meta,
        "full_text": full_text  # NEW: store full text for heuristics
    }

def extract_parties(analysis):
    """
    Extract client name & opposite party from Indian legal documents
    using layered heuristics (metadata → structure → roles → vs).
    """

    meta = analysis.get("document_metadata", {})
    full_text = analysis.get("full_text", "")

    # ---------- 0️⃣ Metadata (best signal if present)
    client = meta.get("addressed_to", "").strip()
    opposite = meta.get("issuing_authority_or_court", "").strip()

    lines = [l.strip() for l in full_text.splitlines() if l.strip()]

    # ---------- 1️⃣ First 40 lines → role keywords
    CLIENT_KEYWORDS = [
        "petitioner", "plaintiff", "applicant", "complainant", "to:"
    ]

    OPPOSITE_KEYWORDS = [
        "respondent", "defendant", "accused", "opposite party", "from:", "by:"
    ]

    for line in lines[:40]:
        low = line.lower()

        if not client:
            for kw in CLIENT_KEYWORDS:
                if kw in low:
                    client = line.split(":", 1)[-1].strip().title()
                    break

        if not opposite:
            for kw in OPPOSITE_KEYWORDS:
                if kw in low:
                    opposite = line.split(":", 1)[-1].strip().title()
                    break

        if client and opposite:
            return client, opposite

    # ---------- 2️⃣ "IN THE MATTER OF" pattern (very common in India)
    for i, line in enumerate(lines[:25]):
        if "in the matter of" in line.lower():
            if i + 1 < len(lines):
                client = client or lines[i + 1].title()
            if i + 3 < len(lines):
                opposite = opposite or lines[i + 3].title()
            return client, opposite

    # ---------- 3️⃣ Structured format:
    # A
    # ... Petitioner
    # Versus
    # B
    # ... Respondent
    for i in range(len(lines) - 3):
        if "petitioner" in lines[i + 1].lower():
            client = client or lines[i].title()
        if "respondent" in lines[i + 1].lower():
            opposite = opposite or lines[i].title()

        if client and opposite:
            return client, opposite

    # ---------- 4️⃣ vs / versus fallback (anywhere in document)
    for line in lines:
        low = line.lower()
        if " vs " in low or " versus " in low:
            sep = " versus " if " versus " in low else " vs "
            parts = low.split(sep)
            if len(parts) == 2:
                client = client or parts[0].strip().title()
                opposite = opposite or parts[1].strip().title()
                return client, opposite

    # ---------- 5️⃣ Last resort: return whatever we managed
    return client, opposite



# ===================== LAYOUT =====================
col_left, col_center, col_right = st.columns([1, 2, 1])

# ===================== LEFT =====================
with col_left:
    st.header("1. Setup")

    docs_map = get_available_documents()
    selected_filename = st.selectbox("📄 Select Document", [""] + list(docs_map.keys()))

    if selected_filename:
        doc_hash = docs_map[selected_filename]
        if st.session_state.get("doc_hash") != doc_hash:
            st.session_state["doc_hash"] = doc_hash

            # Try to load saved analysis first
            analysis = None
            analysis_path = os.path.join("index_data", doc_hash, "doc_analysis.json")
            if os.path.exists(analysis_path):
                with open(analysis_path, "r") as f:
                    analysis = json.load(f)

            # fallback: load from saved chunks & metadata
            if not analysis:
                folder = os.path.join("index_data", doc_hash)
                doc_meta_path = os.path.join(folder, "doc_metadata.pkl")
                chunk_meta_path = os.path.join(folder, "chunks_metadata.pkl")
                if os.path.exists(doc_meta_path) and os.path.exists(chunk_meta_path):
                    with open(doc_meta_path, "rb") as f:
                        doc_meta = pickle.load(f)
                    with open(chunk_meta_path, "rb") as f:
                        chunks = pickle.load(f)
                    full_text = "\n".join(c["text"] for c in chunks)
                    analysis = {
                        "document_metadata": doc_meta,
                        "full_text": full_text
                    }

            if analysis:
                st.session_state["client_name"], st.session_state["opposite_party"] = extract_parties(analysis)

                key_points = analysis.get("key_points_summary", [])
                st.session_state["facts"] = "\n".join(key_points) if key_points else analysis.get("full_text", "")

                st.rerun()




    # ===================== AUTO-POPULATE FROM DOCUMENT =====================
    if st.session_state.get("populate_from_doc"):
    # Load document
        if st.session_state.get("doc_hash"):
            d = load_doc_analysis_by_hash(st.session_state["doc_hash"])
        else:
            d = st.session_state.get("doc_analysis")

        if d:
            meta = d.get("document_metadata", {})

            # First try metadata
            st.session_state["client_name"] = meta.get("addressed_to", "")
            st.session_state["opposite_party"] = meta.get("issuing_authority_or_court", "")

            # Use key points for facts if available, else full text
            key_points = d.get("key_points_summary", [])
            if key_points:
                st.session_state["facts"] = "\n".join(key_points)
            else:
                st.session_state["facts"] = d.get("full_text", "")

            # 🔹 Heuristic fallback using FULL TEXT
            if not st.session_state["client_name"] or not st.session_state["opposite_party"]:
                for line in d.get("full_text", "").splitlines():
                    if "vs" in line.lower() or "versus" in line.lower():
                        parts = line.lower().replace("vs.", "vs").split("vs")
                        if len(parts) == 2:
                            st.session_state["client_name"] = st.session_state["client_name"] or parts[0].strip().title()
                            st.session_state["opposite_party"] = st.session_state["opposite_party"] or parts[1].strip().title()
                            break

        st.session_state["populate_from_doc"] = False




    # ===================== SIDEBAR UI =====================
    draft_mode = st.radio("Source", ["New Draft", "Upload Template (RAG)"], horizontal=True)

    if draft_mode == "Upload Template (RAG)":
        template_file = st.file_uploader("Upload Template (for Drafting only)", type=["docx", "pdf", "txt"], key="template")
        if template_file:
            template_text = read_file_content(template_file)
            st.success(f"Template loaded ({len(template_text)} chars)")

    template_type = st.selectbox(
        "Document Type",
        ["gst_show_cause_reply", "nda", "employment_contract", "lease_deed", "commercial_agreement"]
    )

    st.text_input("Client Name", key="client_name")
    st.text_input("Opposite Party", key="opposite_party")
    st.text_area("Facts / Instructions", height=180, key="facts")
    tone = st.selectbox("Tone", ["Formal", "Persuasive", "Firm"])

    if st.button("✨ Generate Draft", type="primary"):
        payload = {
            "template_type": template_type,
            "client_name": st.session_state["client_name"],
            "opposite_party": st.session_state["opposite_party"],
            "facts": st.session_state["facts"],
            "tone": tone,
            "doc_hash": st.session_state.get("doc_hash")
        }

        try:
            res = requests.post(f"{API_URL}/generate", json=payload, timeout=600)
            if res.status_code == 200:
                data = res.json()
                st.session_state["warnings"] = data.get("warnings", [])
                force_refresh_editor(data["content"])
            else:
                st.error(f"Draft generation failed: {res.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error generating draft: {e}")


# ===================== CENTER =====================
with col_center:
    st.subheader("📝 Editor Workspace")
    if st.session_state["warnings"]:
        with st.expander("⚠️ Compliance Checks"):
            for w in st.session_state["warnings"]:
                st.warning(w)

    if st.session_state["case_law_suggestions"]:
        st.info(st.session_state["case_law_suggestions"])

    draft_content = st.text_area(
        "Draft",
        value=st.session_state["draft"],
        height=1000
    )
    if draft_content != st.session_state["draft"]:
        st.session_state["draft"] = draft_content

# ===================== RIGHT =====================
with col_right:
    st.header("⚡ Tools")
    if st.button("💪 Stronger"):
        apply_global_refinement("Make the legal language stronger.")
    if st.button("🤝 Polite"):
        apply_global_refinement("Make the tone more polite.")
    if st.button("📉 Simplify"):
        apply_global_refinement("Simplify the language.")
    if st.button("⚖️ Legalese"):
        apply_global_refinement("Correct legal terminology.")

    st.divider()
    if st.button("🔍 Suggest Laws & Cases"):
        fetch_case_laws()
