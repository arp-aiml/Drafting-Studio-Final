import docx
from pypdf import PdfReader
from io import BytesIO

def read_file_content(uploaded_file):
    """
    Reads text from uploaded .docx, .pdf, or .txt files.
    """
    if uploaded_file is None:
        return ""
    
    try:
        # 1. Handle Word Documents
        if uploaded_file.name.endswith(".docx"):
            doc = docx.Document(uploaded_file)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return "\n".join(full_text)
        
        # 2. Handle PDF Documents
        elif uploaded_file.name.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        
        # 3. Handle Text Files
        elif uploaded_file.name.endswith(".txt"):
            return uploaded_file.getvalue().decode("utf-8")

    except Exception as e:
        return f"[Error reading file: {str(e)}]"
    
    return ""