# app/utils/retrieval.py
import numpy as np
from app.utils.chunk_and_index import load_faiss_index
from app.utils.legal_embeddings import embed_text

# Load FAISS index once
INDEX, METADATA = load_faiss_index()

def retrieve_top_k_chunks(query: str, k: int = 5):
    """
    Returns top-k most relevant document chunks for a query
    """
    if INDEX is None or METADATA is None:
        return []

    query_vec = embed_text(query).reshape(1, -1)
    distances, indices = INDEX.search(query_vec, k)

    results = []
    for idx in indices[0]:
        if idx < len(METADATA):
            results.append(METADATA[idx]["text"])

    return results