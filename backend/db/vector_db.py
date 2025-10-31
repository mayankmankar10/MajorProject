# backend/db/vector_db.py

import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Load environment variables
load_dotenv()

# Constants
VECTOR_DB_DIR = "./vectors/chroma"
COLLECTION_NAME = "manpower_connector"

# Cache objects
_embeddings = None
_store_cache = {}

# Initialize vector directory
def init_vector_store():
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)

# Get embeddings instance
def get_embeddings():
    global _embeddings
    if _embeddings is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("⚠️ OPENAI_API_KEY not found in .env")
        _embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return _embeddings

# Get or create Chroma vector store
def get_vector_store(collection_name: str = COLLECTION_NAME):
    global _store_cache
    if collection_name in _store_cache:
        return _store_cache[collection_name]

    init_vector_store()
    embeddings = get_embeddings()

    store = Chroma(
        persist_directory=VECTOR_DB_DIR,
        embedding_function=embeddings,
        collection_name=collection_name,
    )

    _store_cache[collection_name] = store
    return store
