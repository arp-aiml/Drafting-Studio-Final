# app/utils/chunk_and_index.py
# Per-document FAISS indexing (SAFE + UI-compatible)

import os
import pickle
import hashlib
import faiss
from tqdm import tqdm
from io import BytesIO
from app.utils.file_handler import read_file_content
from app.utils.legal_embeddings import embed_text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
INDEX_ROOT = os.path.join(BASE_DIR, "index_data")
os.makedirs(INDEX_ROOT, exist_ok=True)


# ===================== HELPERS =====================

def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _doc_folder(doc_hash: str):
    folder = os.path.join(INDEX_ROOT, doc_hash)
    os.makedirs(folder, exist_ok=True)
    return folder


def _index_paths(doc_hash: str):
    folder = _doc_folder(doc_hash)
    return {
        "index": os.path.join(folder, "faiss.index"),
        "doc_meta": os.path.join(folder, "doc_metadata.pkl"),
        "chunk_meta": os.path.join(folder, "chunks_metadata.pkl"),
    }


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


# ===================== BUILD INDEX (FILE) =====================

def build_index_from_file(file_path: str):
    """
    Per-document FAISS indexing.
    SAFE: does not overwrite other documents.
    """

    class Dummy:
        def __init__(self, b):
            self.file = BytesIO(b)
            self.filename = file_path

    with open(file_path, "rb") as f:
        raw_bytes = f.read()

    text = read_file_content(Dummy(raw_bytes))
    print(f"Loaded {os.path.basename(file_path)} | chars={len(text)}")

    if len(text.strip()) < 20:
        print("FAISS: No readable text, skipping")
        return None

    doc_hash = _hash_text(text)
    paths = _index_paths(doc_hash)

    chunks = chunk_text(text)
    if not chunks:
        return None

    dim = embed_text("test").shape[0]
    index = faiss.IndexFlatL2(dim)

    chunk_metadata = []

    for i, chunk in enumerate(tqdm(chunks, desc="Embedding chunks")):
        emb = embed_text(chunk).reshape(1, -1)
        index.add(emb)
        chunk_metadata.append({
            "id": i,
            "text": chunk,
        })

    # ✅ Document-level metadata (FOR UI DROPDOWN)
    doc_metadata = {
        "doc_hash": doc_hash,
        "file_name": os.path.basename(file_path),
        "num_chunks": len(chunks),
    }

    faiss.write_index(index, paths["index"])

    with open(paths["doc_meta"], "wb") as f:
        pickle.dump(doc_metadata, f)

    with open(paths["chunk_meta"], "wb") as f:
        pickle.dump(chunk_metadata, f)

    print(f"✅ FAISS index saved for {doc_metadata['file_name']} → {doc_hash}")
    return doc_hash


# ===================== BUILD INDEX (TEXT) =====================

def build_index_from_text(text: str, source_name: str):
    if len(text.strip()) < 20:
        return None

    doc_hash = _hash_text(text)
    paths = _index_paths(doc_hash)

    chunks = chunk_text(text)
    if not chunks:
        return None

    dim = embed_text("test").shape[0]
    index = faiss.IndexFlatL2(dim)

    chunk_metadata = []

    for i, chunk in enumerate(chunks):
        emb = embed_text(chunk).reshape(1, -1)
        index.add(emb)
        chunk_metadata.append({
            "id": i,
            "text": chunk,
        })

    doc_metadata = {
        "doc_hash": doc_hash,
        "file_name": source_name,
        "num_chunks": len(chunks),
    }

    faiss.write_index(index, paths["index"])

    with open(paths["doc_meta"], "wb") as f:
        pickle.dump(doc_metadata, f)

    with open(paths["chunk_meta"], "wb") as f:
        pickle.dump(chunk_metadata, f)

    print(f"✅ FAISS index saved for {source_name} → {doc_hash}")
    return doc_hash


# ===================== LOAD INDEX (RAG SAFE) =====================

def load_faiss_index(doc_hash: str):
    """
    Used by retrieval layer.
    RETURNS: (faiss_index, chunk_metadata)
    """

    paths = _index_paths(doc_hash)

    if not os.path.exists(paths["index"]) or not os.path.exists(paths["chunk_meta"]):
        return None, None

    index = faiss.read_index(paths["index"])
    with open(paths["chunk_meta"], "rb") as f:
        chunk_metadata = pickle.load(f)

    return index, chunk_metadata
