# backend/db/vector_db.py
"""
Vector database utilities using FAISS with Gemini embeddings.
Supports separate indices for employees and jobs.
"""

import os
import logging
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Constants
VECTOR_DB_DIR = "./vectors/faiss"
EMPLOYEE_INDEX_NAME = "employee_index"
JOB_INDEX_NAME = "job_index"

# Legacy index name (for backward compatibility during migration)
LEGACY_INDEX_NAME = "manpower_index"

# Universal Match Score Thresholds (0-1 scale)
# These provide consistent matching across the platform
DEFAULT_MATCH_THRESHOLD = 0.50  # 50% - Primary threshold for job-to-candidate matching
CANDIDATE_JOB_THRESHOLD = 0.45  # 45% - For candidate job search (show more options)
HIGH_CONFIDENCE_THRESHOLD = 0.75  # 75% - Excellent match for auto-recommendations
MINIMUM_VIABLE_THRESHOLD = 0.30  # 30% - Absolute minimum (don't show below this)

# Cache objects
_embeddings = None
_employee_store_cache = None
_job_store_cache = None


def init_vector_store():
    """Initialize vector directory."""
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)


def get_embeddings():
    """
    Get Gemini embeddings instance.
    Uses text-embedding-004 model (768 dimensions, high quality, FREE).
    Falls back to OpenAI if Gemini is not available.
    """
    global _embeddings
    if _embeddings is not None:
        return _embeddings
    
    # Try Gemini first (FREE!)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            _embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=gemini_key
            )
            logger.info("✅ Using Gemini text-embedding-004 (FREE)")
            return _embeddings
        except Exception as e:
            logger.error(f"❌ Gemini embeddings failed: {e}")
            raise e  # Don't fallback, it causes dimension mismatch with existing index
    
    # Only use OpenAI if no Gemini key is present at all
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        from langchain_openai import OpenAIEmbeddings
        _embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        logger.info("📦 Using OpenAI text-embedding-3-small (paid)")
        return _embeddings
    
    raise ValueError("⚠️ No embedding API key found. Set GEMINI_API_KEY or OPENAI_API_KEY in .env")


def get_vector_store(index_type: str = "employee"):
    """
    Get or load FAISS vector store for specified type.
    
    Args:
        index_type: "employee" or "job"
    
    Returns:
        FAISS vector store or None if not created yet
    """
    global _employee_store_cache, _job_store_cache
    
    # Check cache
    if index_type == "employee" and _employee_store_cache is not None:
        return _employee_store_cache
    if index_type == "job" and _job_store_cache is not None:
        return _job_store_cache
    
    init_vector_store()
    embeddings = get_embeddings()
    
    # Determine index name
    if index_type == "employee":
        index_name = EMPLOYEE_INDEX_NAME
    elif index_type == "job":
        index_name = JOB_INDEX_NAME
    else:
        raise ValueError(f"Unknown index_type: {index_type}")
    
    index_path = os.path.join(VECTOR_DB_DIR, f"{index_name}.faiss")
    
    # Try loading existing index
    if os.path.exists(index_path):
        try:
            store = FAISS.load_local(
                VECTOR_DB_DIR,
                embeddings,
                index_name=index_name,
                allow_dangerous_deserialization=True
            )
            
            # Update cache
            if index_type == "employee":
                _employee_store_cache = store
            else:
                _job_store_cache = store
            
            logger.info(f"✅ Loaded {index_type} vector store ({index_name})")
            return store
        except Exception as e:
            logger.warning(f"⚠️ Failed to load {index_type} index: {e}")
    
    # Try legacy index for employee (backward compatibility)
    if index_type == "employee":
        legacy_path = os.path.join(VECTOR_DB_DIR, f"{LEGACY_INDEX_NAME}.faiss")
        if os.path.exists(legacy_path):
            try:
                store = FAISS.load_local(
                    VECTOR_DB_DIR,
                    embeddings,
                    index_name=LEGACY_INDEX_NAME,
                    allow_dangerous_deserialization=True
                )
                _employee_store_cache = store
                logger.info(f"✅ Loaded legacy employee index ({LEGACY_INDEX_NAME})")
                return store
            except Exception as e:
                logger.warning(f"⚠️ Failed to load legacy index: {e}")
    
    logger.info(f"ℹ️ No {index_type} index found - will create on first sync")
    return None


def create_vector_store(documents, index_type: str = "employee"):
    """
    Create a new FAISS index from documents and save it.
    
    Uses Gemini text-embedding-004 (768 dimensions) for all embeddings.
    Separate indices for employees and jobs enable optimized searches.
    
    Args:
        documents: List of Document objects with page_content and metadata
        index_type: "employee" or "job" - specifies which index to create
    
    Returns:
        FAISS vector store instance
    """
    global _employee_store_cache, _job_store_cache
    
    init_vector_store()
    embeddings = get_embeddings()
    
    index_name = EMPLOYEE_INDEX_NAME if index_type == "employee" else JOB_INDEX_NAME
    
    store = FAISS.from_documents(documents, embeddings)
    store.save_local(VECTOR_DB_DIR, index_name=index_name)
    
    # Update cache
    if index_type == "employee":
        _employee_store_cache = store
    else:
        _job_store_cache = store
    
    logger.info(f"✅ Created {index_type} vector store with {len(documents)} documents")
    return store


def add_to_vector_store(documents, index_type: str = "employee"):
    """
    Add documents to existing vector store or create new one.
    
    Args:
        documents: List of Document objects
        index_type: "employee" or "job"
    """
    store = get_vector_store(index_type)
    index_name = EMPLOYEE_INDEX_NAME if index_type == "employee" else JOB_INDEX_NAME
    
    if store:
        store.add_documents(documents)
        store.save_local(VECTOR_DB_DIR, index_name=index_name)
        logger.info(f"✅ Added {len(documents)} documents to {index_type} index")
    else:
        create_vector_store(documents, index_type)


def clear_cache():
    """Clear cached vector stores (useful for re-initialization)."""
    global _embeddings, _employee_store_cache, _job_store_cache
    _embeddings = None
    _employee_store_cache = None
    _job_store_cache = None
    logger.info("🧹 Vector store cache cleared")


# Backward compatibility - default to employee store
def get_store():
    """Alias for get_vector_store('employee')."""
    return get_vector_store("employee")
