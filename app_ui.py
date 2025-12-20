# app_ui.py
import streamlit as st
import requests
from app.utils.file_handler import read_file_content

API_URL = "http://127.0.0.1:8000/draft"

st.set_page_config(page_title="LexFlow Studio", layout="wide", page_icon="⚖️")

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

st.title("⚖️ LexFlow AI - Drafting Studio")

# ===================== STATE =====================
defaults = {
    "draft": "",
    "warnings": [],
    "case_law_suggestions": "",
    "doc_analysis": None,
    "client_name": "",
    "opposite_party": "",
    "facts": "",
    "document_title": ""
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

# ===================== LAYOUT =====================
col_left, col_center, col_right = st.columns([1, 2, 1])

# ===================== LEFT =====================
with col_left:
    st.header("1. Setup")

    # ===================== AUTO-POPULATE FROM DOCUMENT =====================
    if st.session_state.get("populate_from_doc") and st.session_state.get("doc_analysis"):
        d = st.session_state["doc_analysis"]
        st.session_state["client_name"] = d.get("receiver_party") or ""
        st.session_state["opposite_party"] = d.get("sender_party") or ""
        st.session_state["facts"] = "\n".join(d.get("key_points", []))
        st.session_state["draft"] = ""
        st.session_state["populate_from_doc"] = False

    # ===================== SIDEBAR UI =====================
    draft_mode = st.radio("Source", ["New Draft", "Upload Template (RAG)"], horizontal=True)
    uploaded_text = ""

    if draft_mode == "Upload Template (RAG)":
        uploaded_file = st.file_uploader("Upload Legal Document", type=["docx", "pdf", "txt"])
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
                            timeout=600  # generous timeout
                        )
                        if res.status_code == 200:
                            st.session_state["doc_analysis"] = res.json()
                            st.toast("Document analyzed successfully")
                        else:
                            st.error(f"Analysis failed: {res.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error analyzing document: {e}")

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
            "tone": tone
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
            st.toast("Populating sidebar fields…")
            st.rerun()


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
