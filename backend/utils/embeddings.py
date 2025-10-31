# backend/utils/embeddings.py
from backend.db.vector_db import get_embeddings

def get_embedding_function():
    return get_embeddings()
