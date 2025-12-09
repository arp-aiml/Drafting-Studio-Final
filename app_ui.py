import streamlit as st
import requests
from app.utils.file_handler import read_file_content

# URL Matches Backend Prefix
API_URL = "http://127.0.0.1:8000/draft"

st.set_page_config(page_title="LexFlow Studio", layout="wide", page_icon="⚖️")

# --- CUSTOM CSS ---
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
    div[data-testid="stExpander"] details summary {
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚖️ LexFlow AI - Drafting Studio")

# --- INITIALIZE STATE ---
if 'draft' not in st.session_state: st.session_state['draft'] = ""
if 'research' not in st.session_state: st.session_state['research'] = ""
if 'warnings' not in st.session_state: st.session_state['warnings'] = []
if 'case_law_suggestions' not in st.session_state: st.session_state['case_law_suggestions'] = ""

# --- HELPER FUNCTIONS ---

def force_refresh_editor(new_text):
    """Updates the state and reruns the app (No Key = No Conflict)."""
    st.session_state['draft'] = new_text
    st.rerun()

def apply_global_refinement(instruction):
    """Sends the WHOLE draft for refinement."""
    current_text = st.session_state.get('draft', "")
    if not current_text:
        st.toast("⚠️ Editor is empty!")
        return
    
    with st.spinner(f"Refining ({instruction})..."):
        try:
            res = requests.post(f"{API_URL}/refine", json={"selected_text": current_text, "instruction": instruction})
            if res.status_code == 200:
                force_refresh_editor(res.json()['refined_content'])
                st.toast("✅ Document Refined!")
            else:
                st.error("Refinement Failed")
        except Exception as e:
            st.error(f"Error: {e}")

def fetch_case_laws():
    """Fetches Laws & Case Laws."""
    current_text = st.session_state.get('draft', "")
    if not current_text:
        st.toast("⚠️ Draft is empty.")
        return

    with st.spinner("🕵️ Finding Relevant Sections & Cases..."):
        try:
            res = requests.post(f"{API_URL}/suggest-cases", json={"content": current_text})
            if res.status_code == 200:
                st.session_state['case_law_suggestions'] = res.json()['suggestions']
                st.rerun() 
            else:
                st.error("Failed to fetch research.")
        except Exception as e:
            st.error(f"Error: {e}")

# ================= LAYOUT =================
col_left, col_center, col_right = st.columns([1, 2, 1])

# --- 1. LEFT SIDEBAR: INPUTS ---
with col_left:
    st.header("1. Setup")
    
    draft_mode = st.radio("Source:", ["New Draft", "Upload Template (RAG)"], horizontal=True)
    
    uploaded_text = ""
    if draft_mode == "Upload Template (RAG)":
        uploaded_file = st.file_uploader("Upload .docx or .pdf", type=["docx", "pdf", "txt"])
        if uploaded_file:
            uploaded_text = read_file_content(uploaded_file)
            st.success(f"✅ Loaded {len(uploaded_text)} chars")

    template_type = st.selectbox("Document Type", [
        "gst_show_cause_reply", "nda", "employment_contract", 
        "lease_deed", "commercial_agreement"
    ], key="doc_selector")
    
    client_name = st.text_input("Client Name", "Apex Corp", key="client_input")
    opposite_party = st.text_input("Opposite Party", "The Authority", key="opp_party_input")
    facts = st.text_area("Facts / Instructions", height=150, key="facts_input")
    tone = st.selectbox("Tone", ["Formal", "Persuasive", "Firm"], key="tone_input")

    if st.button("✨ Generate Draft", type="primary"):
        with st.spinner("🤖 Drafting..."):
            payload = {
                "template_type": template_type,
                "client_name": client_name,
                "opposite_party": opposite_party,
                "facts": facts,
                "tone": tone,
                "template_text": uploaded_text
            }
            try:
                res = requests.post(f"{API_URL}/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    st.session_state['research'] = data.get('research_note', "")
                    st.session_state['warnings'] = data.get('warnings', [])
                    force_refresh_editor(data['content'])
                else:
                    st.error(f"Error: {res.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")

# --- 2. CENTER: EDITOR ---
with col_center:
    st.subheader("📝 Editor Workspace")

    if st.session_state['warnings']:
        with st.expander("⚠️ Compliance Checks", expanded=False):
            for w in st.session_state['warnings']: st.warning(w)

    # RELEVANT LAWS SECTION (UPDATED)
    if st.session_state['case_law_suggestions']:
        st.info(f"📚 **Legal Authorities Found:**\n\n{st.session_state['case_law_suggestions']}")
        
        # INSERT BUTTON
        if st.button("📥 Insert Authorities into Draft"):
             force_refresh_editor(st.session_state['draft'] + "\n\n### Legal Authorities & Precedents\n" + st.session_state['case_law_suggestions'])

    # MAIN EDITOR WIDGET
    draft_content = st.text_area(
        "Draft", 
        value=st.session_state['draft'], 
        height=650
    )
    
    if draft_content != st.session_state['draft']:
        st.session_state['draft'] = draft_content

    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("💾 Save"): st.toast("Draft Saved!")
    with c2: 
        if st.button("📄 Word"):
             res = requests.post(f"{API_URL}/export/word", json={"content": st.session_state['draft']})
             st.download_button("Download Docx", res.content, "Draft.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with c3:
        if st.button("📕 PDF"):
             res = requests.post(f"{API_URL}/export/pdf", json={"content": st.session_state['draft']})
             st.download_button("Download PDF", res.content, "Draft.pdf", "application/pdf")

# --- 3. RIGHT SIDEBAR: TOOLS ---
with col_right:
    st.header("⚡ Tools")
    
    st.markdown("### ✨ AI Refinement")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("💪 Stronger"):
            apply_global_refinement("Make the legal language stronger and more protective.")
    with col_r2:
        if st.button("🤝 Polite"):
            apply_global_refinement("Make the tone more collaborative and polite.")
            
    col_r3, col_r4 = st.columns(2)
    with col_r3:
        if st.button("📉 Simplify"):
            apply_global_refinement("Simplify the language for a layperson.")
    with col_r4:
        if st.button("⚖️ Legalese"):
            apply_global_refinement("Correct any improper legal terminology.")

    st.divider()

    # UPDATED BUTTON LABEL
    st.markdown("### 📚 Legal Research")
    if st.button("🔍 Suggest Laws & Cases"):
        fetch_case_laws() 

    st.divider()
    
    st.markdown("### 📌 Append Clause")
    if st.button("🛡️ Indemnity"):
        force_refresh_editor(st.session_state['draft'] + "\n\n### Indemnity\nThe Party shall indemnify, defend, and hold harmless the other Party from all claims, losses, and damages arising from breach of this Agreement.")
        
    if st.button("🛑 Termination"):
        force_refresh_editor(st.session_state['draft'] + "\n\n### Termination\nEither Party may terminate this Agreement with 30 days' prior written notice to the other Party.")
        
    if st.button("⚖️ Dispute Resolution"):
        force_refresh_editor(st.session_state['draft'] + "\n\n### Dispute Resolution\nAny dispute arising out of this Agreement shall be referred to arbitration in accordance with the Arbitration and Conciliation Act, 1996.")

    st.divider()
    
    with st.expander("📧 Email Client"):
        recipient = st.text_input("To:", key="email_to")
        subj = st.text_input("Subject:", "Legal Draft", key="email_sub")
        if st.button("Send Email"):
             if recipient:
                requests.post(f"{API_URL}/send-email", json={"recipient": recipient, "subject": subj, "content": st.session_state['draft']})
                st.success("Email Sent!")