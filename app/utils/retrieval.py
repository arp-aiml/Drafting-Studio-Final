# app/utils/retrieval.py
from app.utils.chunk_and_index import load_faiss_index
import numpy as np

def retrieve_top_k_chunks(query: str, k: int = 5, doc_hash: str = None, index=None, metadata=None):
    """
    Retrieve top-k most relevant chunks from a document's FAISS index.

    - If `doc_hash` is provided, it loads the FAISS index for that document.
    - Otherwise, you can pass `index` and `metadata` directly.
    """
    # 1️⃣ Load per-document index if not provided
    if index is None or metadata is None:
        if doc_hash is None:
            raise ValueError("Either index/metadata or doc_hash must be provided")
        index, metadata = load_faiss_index(doc_hash)
        if index is None or metadata is None:
            return []

    # 2️⃣ Embed the query
    from app.utils.legal_embeddings import embed_text
    query_vec = embed_text(query).reshape(1, -1).astype(np.float32)

    # 3️⃣ Search FAISS
    D, I = index.search(query_vec, k)
    results = []
    for i in I[0]:
        if i < len(metadata):
            results.append(metadata[i]["text"])

    return results
