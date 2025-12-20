# app/utils/legal_embeddings.py
# app/utils/legal_embeddings.py
import os
import torch
import numpy as np
from sentence_transformers import SentenceTransformer

# HARD FORCE CPU + SINGLE THREAD (optional)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

MODEL_NAME = "nlpaueb/legal-bert-base-uncased"

print("🔹 Loading embedding model...")
model = SentenceTransformer(MODEL_NAME, device="cpu")
print("✅ Embedding model loaded")

def embed_text(text: str) -> np.ndarray:
    """
    Returns normalized sentence embedding suitable for FAISS.
    Handles long text.
    """
    if not text.strip():
        return np.zeros(model.get_sentence_embedding_dimension(), dtype="float32")
    
    emb = model.encode(
        text,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )
    return emb.astype("float32")
