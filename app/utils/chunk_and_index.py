# app/utils/chunk_and_index.py
# app/utils/chunk_and_index.py

import os
import pickle
import hashlib
import faiss
import numpy as np
from tqdm import tqdm
from io import BytesIO

from app.utils.file_handler import read_file_content
from app.utils.legal_embeddings import embed_text


# =============================
# BASE PATH
# =============================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
INDEX_ROOT = os.path.join(BASE_DIR, "index_data")
os.makedirs(INDEX_ROOT, exist_ok=True)


# =============================
# HELPERS
# =============================
def _hash_text(text: str) -> str:
    """Stable hash for document isolation"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _index_paths(doc_hash: str):
    folder = os.path.join(INDEX_ROOT, doc_hash)
    os.makedirs(folder, exist_ok=True)

    return (
        os.path.join(folder, "faiss.index"),
        os.path.join(folder, "metadata.pkl"),
    )


# =============================
# CHUNKING
# =============================
def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50):
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
# BUILD INDEX (PER FILE)
# =============================
def build_index_from_file(file_path: str):
    """
    Builds FAISS index for ONE document.
    NEVER overwrites another document's index.
    """

    # Read bytes
    with open(file_path, "rb") as f:
        raw_bytes = f.read()

    # Fake UploadFile
    class Dummy:
        def __init__(self, b):
            self.file = BytesIO(b)
            self.filename = file_path

    text = read_file_content(Dummy(raw_bytes))
    print(f"Loaded {os.path.basename(file_path)} | chars={len(text)}")

    if len(text.strip()) < 50:
        print("FAISS: No readable text, skipping index build")
        return None

    # 🔑 DOCUMENT ID
    doc_hash = _hash_text(text)
    INDEX_PATH, META_PATH = _index_paths(doc_hash)

    chunks = chunk_text(text)
    print(f"Chunks created: {len(chunks)}")

    if not chunks:
        return None

    dim = embed_text("test").shape[0]
    index = faiss.IndexFlatL2(dim)
    metadata = []

    for i, chunk in enumerate(tqdm(chunks, desc="Embedding chunks")):
        emb = embed_text(chunk).reshape(1, -1)
        index.add(emb)

        metadata.append({
            "id": i,
            "text": chunk,
            "source_file": os.path.basename(file_path),
            "doc_hash": doc_hash,
        })

    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(metadata, f)

    print(f"✅ FAISS index saved: {doc_hash}")
    return doc_hash


# =============================
# LOAD INDEX (BY HASH)
# =============================
def load_faiss_index(doc_hash: str):
    INDEX_PATH, META_PATH = _index_paths(doc_hash)

    if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
        return None, None

    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "rb") as f:
        metadata = pickle.load(f)

    return index, metadata
