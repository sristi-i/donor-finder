"""
Minimal embeddings wrapper.

Uses sentence-transformers if available (recommended for local),
otherwise falls back to a very simple hashing vector (keeps the API usable).
"""
from __future__ import annotations
import math
import os
from typing import List

_MODEL = None
_USE_ST = False

def _init_model():
    global _MODEL, _USE_ST
    if _MODEL is not None:
        return
    try:
        from sentence_transformers import SentenceTransformer
        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        _MODEL = SentenceTransformer(model_name)
        _USE_ST = True
    except Exception:
        _MODEL = True  # sentinel
        _USE_ST = False

def _normalize(v):
    s = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / s for x in v]

def _hash_embed(text: str, dim: int = 384) -> List[float]:
    # toy hashing fallback to keep API running if no model is installed
    import hashlib, random
    h = hashlib.sha256(text.encode("utf-8")).digest()
    random.seed(h)
    return _normalize([random.random() - 0.5 for _ in range(dim)])

def embed_texts(texts: List[str]) -> List[list[float]]:
    _init_model()
    if _USE_ST:
        vecs = _MODEL.encode(texts, normalize_embeddings=True, convert_to_numpy=False)
        return [list(map(float, v)) for v in vecs]
    return [_hash_embed(t) for t in texts]

def to_pgvector(vec: list[float]) -> str:
    # pgvector text representation: '[0.01,0.02,...]'
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
