# app/utils/chunk_and_index.py
import os
import pickle
import faiss
import numpy as np
from tqdm import tqdm
from io import BytesIO
from app.utils.file_handler import read_file_content
from app.utils.legal_embeddings import embed_text

# =============================
# PATHS
# =============================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
INDEX_DIR = os.path.join(BASE_DIR, "index_data")
os.makedirs(INDEX_DIR, exist_ok=True)

INDEX_PATH = os.path.join(INDEX_DIR, "faiss.index")
META_PATH = os.path.join(INDEX_DIR, "metadata.pkl")

# =============================
# Chunking
# =============================
def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50):
    """
    Split text into overlapping chunks suitable for BERT embedding
    """
    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks

# =============================
# Build FAISS Index
# =============================
def build_index_from_file(file_path: str):
    """
    Parse file, embed chunks, build FAISS index, and save metadata
    """
    with open(file_path, "rb") as f:
        raw_bytes = f.read()

    class Dummy:
        def __init__(self, b):
            self.file = BytesIO(b)
            self.filename = file_path

    text = read_file_content(Dummy(raw_bytes))
    print(f"Loaded {os.path.basename(file_path)} | chars={len(text)}")

    if not text.strip():
        print("FAISS: No text extracted, skipping index build")
        return None


    chunks = chunk_text(text)
    print(f"Chunks created: {len(chunks)}")

    # Embed first chunk to get dimension
    dim = embed_text("test").shape[0]
    index = faiss.IndexFlatL2(dim)
    metadata = []

    # Batch embedding chunks
    for i, chunk in enumerate(tqdm(chunks, desc="Embedding chunks")):
        emb = embed_text(chunk).reshape(1, -1)
        index.add(emb)
        metadata.append({
            "id": i,
            "text": chunk,
            "source_file": os.path.basename(file_path)
        })

    # Save FAISS index and metadata
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(metadata, f)

    print("✅ FAISS index saved")
    print("✅ Metadata saved")


# =============================
# Load FAISS Index
# =============================
def load_faiss_index():
    if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
        print("❌ FAISS index not found")
        return None, None

    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "rb") as f:
        metadata = pickle.load(f)

    print("✅ FAISS index loaded from disk")
    return index, metadata
