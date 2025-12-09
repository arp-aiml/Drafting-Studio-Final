
# ⚖️ LexFlow AI - Drafting Studio

**The AI-Powered Workspace for Indian Legal & Tax Professionals.**

LexFlow AI automates the drafting of complex legal documents (GST Replies, NDAs, Contracts) by combining **Generative AI** with **Real-Time Legal Research**. It ensures every draft is legally sound by citing specific Indian Acts and Judgments found via live government website scraping.

---

## ⚡ Quick Start (Run in 3 Steps)

**1. Clone & Install**
```bash
git clone [https://github.com/ShubhamUPES/Drafting_Studio_AIMill.git](https://github.com/shubham-aimill/Drafting_studio_aimill.git)
cd lexflow-backend
python -m venv .venv
.\.venv\Scripts\Activate  # Windows
pip install -r requirements.txt
````

**2. Configure Keys**
Create a `.env` file in the root folder and paste your keys:

```ini
OPENAI_API_KEY=sk-proj-your-key
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # Use Gmail App Password, NOT login password
MAIL_FROM=your-email@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
```

**3. Run the App**
Open **Two Terminals**:

  * **Terminal 1 (Backend):** `python main.py`
  * **Terminal 2 (Frontend):** `streamlit run app_ui.py`

👉 *Open your browser at `http://localhost:8501` to start drafting.*

-----

## 🌟 What Can It Do?

### 1\. 📝 Draft Legal Documents Instantly

Select a template, enter client facts, and get a professional draft in seconds. Supports:

  * **GST:** Show Cause Replies (DRC-06), Appeals (APL-01).
  * **Corporate:** Shareholder Agreements, Board Resolutions, JVs.
  * **Contracts:** NDAs, Employment Contracts, Leases.

### 2\. 🔍 Research-First Intelligence

Unlike standard AI, LexFlow **researches before it writes**.

  * It scrapes **`indiankanoon.org`**, **`cbic.gov.in`**, and **`incometaxindia.gov.in`**.
  * It finds relevant **Case Laws** and **Sections** relative to your specific facts.
  * *Safety:* If no official link is found, it switches to "Statutory Mode" (Drafting based on the Act) to avoid hallucinating fake cases.

### 3\. ✍️ Edit, Refine & Export

  * **Smart Refiner:** Highlight any text and ask AI to "Make it Tougher," "Polite," or "Legally Precise."
  * **Client-Ready Export:** Download as **Word (.docx)** or **PDF** with perfect legal formatting (Times New Roman, Justified, No messy formatting).
  * **Email:** Send the draft directly to your client from the dashboard.

-----

## 🛡️ Safety & Compliance (Zero-Trust)

We built this for lawyers, so accuracy is non-negotiable.

| Feature | Description |
| :--- | :--- |
| **Strict Whitelist** | The scraper is hard-coded to visit **ONLY** government (`.gov.in`) and legal repo (`indiankanoon.org`) sites. It blocks blogs/forums. |
| **Validator Engine** | Before you download, the system scans your draft for mandatory sections (e.g., missing "Prayer" in a Petition triggers a warning). |
| **Fallback Mode** | If the internet is down or no case law is found, the AI defaults to "Statutory Mode" (General Principles) rather than inventing fake citations. |

-----

## 📂 Project Structure

```text
lexflow-backend/
├── main.py                 # 🧠 Backend API (FastAPI)
├── app_ui.py               # 💻 Frontend UI (Streamlit)
├── .env                    # 🔑 API Keys (Hidden)
├── requirements.txt        # 📦 Dependencies
└── app/
    ├── services/
    │   ├── ai_engine.py    # OpenAI Integration
    │   ├── scraper.py      # BeautifulSoup Web Scraper (The Researcher)
    │   ├── validator.py    # Compliance Checker (The Gatekeeper)
    │   ├── export_engine.py# Document Formatter (Word/PDF)
    │   └── email_engine.py # Email Sender
    └── utils/
        ├── prompts.py      # "Senior Advocate" System Prompts
```

-----

## ❓ Troubleshooting

**Q: The PDF download failed.**

  * **Fix:** Ensure you are using the latest `export_engine.py` which uses standard fonts (Helvetica/Times) to avoid compatibility issues.

**Q: Email is giving a 500 Error.**

  * **Fix:** You cannot use your normal Gmail login password. You must generate an **App Password** from your Google Account \> Security \> 2-Step Verification.

**Q: The "Research" box is Yellow, not Green.**

  * **Reason:** The scraper couldn't find a high-confidence match on a Government site.
  * **Fix:** Try adding specific keywords to your facts, like *"Cite Section 16(4) of CGST Act"* or *"Refer to Arise India judgment"*.

-----

## 📜 License

**Proprietary & Confidential.** Designed for LexFlow AI.

```
```