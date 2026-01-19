# 🔬 Technical Architecture: Job Matching System

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                                │
│           "Show me chef jobs in Mumbai"                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              AI ORCHESTRATOR (GPT-4)                         │
│  - Analyzes intent                                           │
│  - Selects appropriate tool                                  │
│  - LangChain AgentExecutor                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│JobFinder │  │Matching  │  │Application│
│  Tool    │  │  Tool    │  │   Tool    │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     ▼             ▼             ▼
┌─────────────────────────────────────┐
│        DATA LAYER                   │
│  ┌─────────┐  ┌──────────────┐     │
│  │PostgreSQL│  │ChromaDB      │     │
│  │(SQL DB)  │  │(Vector Store)│     │
│  └─────────┘  └──────────────┘     │
└─────────────────────────────────────┘
```

---

## 🧠 Part 1: Semantic Matching with Vector Embeddings

### **What are Embeddings?**

**Embeddings** convert text into high-dimensional vectors (arrays of numbers) that capture semantic meaning.

```python
# Example:
text_1 = "Experienced chef with Italian cuisine expertise"
embedding_1 = [0.23, -0.45, 0.67, ..., 0.12]  # 1536 dimensions

text_2 = "Italian cook, 5 years experience"
embedding_2 = [0.25, -0.43, 0.65, ..., 0.14]  # 1536 dimensions

# These are SIMILAR even though words differ!
# Cosine similarity: 0.92 (high similarity)
```

### **Embedding Model Used**

```python
# backend/db/vector_db.py
from langchain_openai import OpenAIEmbeddings

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",  # OpenAI's latest embedding model
    dimensions=1536  # Vector size
)
```

**Technical Specs:**
- **Model:** `text-embedding-3-small`
- **Dimensions:** 1536 (can be configured)
- **Max Input:** 8191 tokens
- **Output:** Dense vector of floating-point numbers
- **Cost:** ~$0.02 per 1M tokens

### **How Embeddings are Created**

```python
# When a new employee profile is created:
def create_employee_embedding(employee):
    # 1. Combine all profile data into text
    profile_text = f"""
    Name: {employee.full_name}
    Role: {employee.preferred_role}
    Skills: {', '.join(employee.skills)}
    Experience: {employee.years_in_hospitality} years in hospitality
    Cuisine: {', '.join(employee.cuisine_experience)}
    Certifications: {get_certifications(employee)}
    Education: {', '.join(employee.education)}
    """
    
    # 2. Generate embedding using OpenAI API
    embedding = embedding_model.embed_query(profile_text)
    # Returns: [0.234, -0.456, 0.789, ..., 0.123]  (1536 floats)
    
    # 3. Store in ChromaDB with metadata
    vector_store.add_documents([
        Document(
            page_content=profile_text,
            metadata={
                "id": employee.id,
                "type": "employee",
                "role": employee.preferred_role,
                "location": employee.preferred_location
            }
        )
    ])
```

---

## 🗄️ Part 2: ChromaDB Vector Database

### **What is ChromaDB?**

ChromaDB is a **vector database** optimized for similarity search using embeddings.

**Traditional SQL:**
```sql
SELECT * FROM jobs WHERE title LIKE '%chef%'  -- Exact keyword match
```

**Vector Database:**
```python
# Find semantically similar items
vector_store.similarity_search(
    query="experienced Italian chef",
    k=10
)
# Returns: Jobs/profiles similar in MEANING, not just keywords
```

### **ChromaDB Architecture**

```
┌──────────────────────────────────────┐
│         ChromaDB Instance            │
│                                      │
│  Collection: "employee_profiles"     │
│  ┌────────────────────────────────┐  │
│  │ Document 1:                    │  │
│  │  - ID: 1                       │  │
│  │  - Embedding: [0.23, -0.45...]│  │
│  │  - Text: "Chef with 5 yrs..."  │  │
│  │  - Metadata: {role: "chef"}    │  │
│  └────────────────────────────────┘  │
│                                      │
│  Collection: "job_postings"          │
│  ┌────────────────────────────────┐  │
│  │ Document 1:                    │  │
│  │  - ID: 101                     │  │
│  │  - Embedding: [0.25, -0.43...]│  │
│  │  - Text: "Need Italian chef.." │  │
│  │  - Metadata: {type: "chef"}    │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### **Similarity Search Algorithm**

**1. Distance Metrics**

ChromaDB supports multiple distance functions:

```python
# Cosine Similarity (default)
similarity = cosine_similarity(vector_A, vector_B)
# Range: -1 to 1 (1 = identical, -1 = opposite)

# Formula:
cosine_sim = dot(A, B) / (||A|| * ||B||)
```

**2. Approximate Nearest Neighbor (ANN)**

For fast search in large datasets:

```python
# Instead of comparing with ALL vectors (slow):
# O(n) where n = number of documents

# Uses HNSW (Hierarchical Navigable Small World) algorithm:
# O(log n) - much faster!

# HNSW creates a graph structure:
#   Layer 2: [few nodes, long jumps]
#   Layer 1: [more nodes, medium jumps]
#   Layer 0: [all nodes, precise search]
```

**3. Search Process**

```python
def similarity_search(query_text, k=5):
    # Step 1: Convert query to embedding
    query_embedding = embedding_model.embed_query(query_text)
    # [0.234, -0.456, ...]
    
    # Step 2: Find k nearest vectors using HNSW
    # Chromadb internally:
    # - Starts at top layer of graph
    # - Navigates to closest node
    # - Descends layers until reaching bottom
    # - Returns k nearest neighbors
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )
    
    # Step 3: Returns documents with distance scores
    # Distance = 1 - cosine_similarity
    # Lower distance = more similar
    
    return results
```

---

## 🎯 Part 3: The Matching Algorithm (Technical Deep Dive)

### **MatchingTool: Hybrid Scoring System**

The MatchingTool combines **semantic similarity** (AI) with **rule-based scoring** (domain expertise).

```python
class MatchingTool:
    def _run(self, query_text, job_id, top_k=5):
        # PHASE 1: Semantic Search
        # ─────────────────────────────────────────
        results = vector_store.similarity_search_with_score(
            query_text,
            k=top_k * 2  # Get 2x for re-ranking
        )
        # Returns: [(doc1, distance1), (doc2, distance2), ...]
        
        matches = []
        
        for doc, distance in results:
            # PHASE 2: Convert Distance to Base Score
            # ─────────────────────────────────────────
            # ChromaDB returns distance (0-2 range)
            # 0 = identical, 2 = opposite
            
            # Convert to similarity score (0-1)
            similarity = 1 - (distance / 2)
            
            # Scale to 0-60 points
            base_score = similarity * 60
            
            # PHASE 3: Rule-Based Bonuses
            # ─────────────────────────────────────────
            bonus_score = self._calculate_restaurant_bonus(
                employee, job
            )
            
            # PHASE 4: Combine Scores
            # ─────────────────────────────────────────
            final_score = min(base_score + bonus_score, 100)
            
            matches.append({
                "id": doc.metadata["id"],
                "base_score": base_score,      # AI semantic
                "bonus_score": bonus_score,     # Domain rules
                "final_score": final_score      # Combined
            })
        
        # PHASE 5: Re-Rank by Final Score
        # ─────────────────────────────────────────
        matches.sort(key=lambda x: x["final_score"], reverse=True)
        return matches[:top_k]
```

### **Restaurant Bonus Calculation**

```python
def _calculate_restaurant_bonus(employee, job):
    bonus = 0.0
    
    # Bonus 1: Exact Certification Match
    # ───────────────────────────────────
    if job.requires_food_safety:
        if employee.food_safety_certified:
            bonus += 10  # Critical for kitchen roles
    
    if job.requires_alcohol_cert:
        if employee.alcohol_service_certified:
            bonus += 5   # Important for bartenders
    
    # Bonus 2: Cuisine Experience
    # ───────────────────────────────────
    if job.cuisine_type and employee.cuisine_experience:
        # Check if cuisine type in list
        if job.cuisine_type in employee.cuisine_experience:
            bonus += 15  # Exact cuisine match
        
        # Partial match (similar cuisines)
        elif is_similar_cuisine(job.cuisine_type, employee.cuisine_experience):
            bonus += 7.5  # Partial credit
    
    # Bonus 3: Shift Availability
    # ───────────────────────────────────
    if job.shift_type and employee.shift_preferences:
        if job.shift_type in employee.shift_preferences:
            bonus += 5
        
        # Check adjacent shifts
        elif is_adjacent_shift(job.shift_type, employee.shift_preferences):
            bonus += 2.5  # Can probably adjust
    
    # Bonus 4: Experience Threshold
    # ───────────────────────────────────
    min_exp = job.min_hospitality_experience or 0
    employee_exp = employee.years_in_hospitality or 0
    
    if employee_exp >= min_exp:
        bonus += 10  # Meets minimum
        
        # Additional bonus for overqualification
        excess_exp = employee_exp - min_exp
        bonus += min(excess_exp * 2, 10)  # Up to +10 more
    
    # Bonus 5: Customer Service (NLP check)
    # ───────────────────────────────────────
    if job.job_category in ["waiter", "host", "bartender"]:
        # Check profile cache for extracted skills
        if cached_profile and cached_profile.top_skills:
            customer_service_keywords = [
                "customer service", "guest relations", 
                "hospitality", "communication", "friendly"
            ]
            
            for skill in cached_profile.top_skills:
                if any(kw in skill.lower() for kw in customer_service_keywords):
                    bonus += 10
                    break
    
    return min(bonus, 50)  # Cap at 50 points
```

---

## 🔢 Part 4: Mathematical Formulas

### **Cosine Similarity**

```python
import numpy as np

def cosine_similarity(vec_A, vec_B):
    """
    Calculate cosine of angle between two vectors
    Range: -1 to 1
    1 = same direction (very similar)
    0 = perpendicular (unrelated)
    -1 = opposite direction (very dissimilar)
    """
    dot_product = np.dot(vec_A, vec_B)
    norm_A = np.linalg.norm(vec_A)
    norm_B = np.linalg.norm(vec_B)
    
    return dot_product / (norm_A * norm_B)

# Example:
vec_chef = [0.23, -0.45, 0.67, 0.12]
vec_job = [0.25, -0.43, 0.65, 0.14]

similarity = cosine_similarity(vec_chef, vec_job)
# = 0.998  (very similar!)
```

### **Euclidean Distance**

```python
def euclidean_distance(vec_A, vec_B):
    """
    Straight-line distance in n-dimensional space
    Lower = more similar
    """
    return np.sqrt(np.sum((vec_A - vec_B) ** 2))

# Example:
distance = euclidean_distance(vec_chef, vec_job)
# = 0.045  (very close in vector space)
```

### **Final Score Normalization**

```python
def normalize_score(base_score, bonus_score):
    """
    Combine semantic and rule-based scores
    Ensure final score is 0-100
    """
    # Weighted combination
    semantic_weight = 0.6  # 60% AI
    rule_weight = 0.4      # 40% Rules
    
    combined = (base_score * semantic_weight) + (bonus_score * rule_weight)
    
    # Clip to valid range
    final_score = np.clip(combined, 0, 100)
    
    return final_score
```

---

## 🏗️ Part 5: Data Flow & Pipeline

### **Profile Indexing Pipeline**

```
New Employee Created
    ↓
┌────────────────────────────────┐
│ 1. ProfileAnalyzerTool         │
│    - Extracts skills using NLP │
│    - Identifies key strengths  │
│    - Uses GPT-4 for analysis   │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ 2. Create Profile Text         │
│    profile = f"""              │
│      Name: {name}              │
│      Role: {role}              │
│      Skills: {skills}          │
│      Experience: {years}       │
│    """                         │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ 3. Generate Embedding          │
│    embedding_model.embed_query │
│    → [1536 floats]             │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ 4. Store in ChromaDB           │
│    collection.add(             │
│      embeddings=[embedding],   │
│      documents=[profile_text], │
│      metadatas=[{id: 1}]       │
│    )                           │
└────────────────────────────────┘
```

### **Job Matching Query Pipeline**

```
User: "Find me chef jobs"
    ↓
┌────────────────────────────────┐
│ 1. Intent Recognition (GPT-4)  │
│    → Identifies: Job search    │
│    → Selects: JobFinderTool    │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ 2. SQL Query Execution         │
│    SELECT * FROM jobs          │
│    WHERE title LIKE '%chef%'   │
│    LIMIT 10                    │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ 3. Return Results              │
│    → 10 jobs                   │
│    → No scoring yet            │
└────────────────────────────────┘
```

### **Application Match Scoring Pipeline**

```
User: "Apply to job #5"
    ↓
┌────────────────────────────────┐
│ 1. Load Employee & Job Data    │
│    employee = db.get(id=3)     │
│    job = db.get(id=5)          │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ 2. Calculate Match Score       │
│    score = 0                   │
│    + role_match * 0.30         │
│    + cuisine_match * 0.20      │
│    + experience_match * 0.20   │
│    + cert_match * 0.15         │
│    + shift_match * 0.15        │
│    = 0.87 (87%)                │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ 3. Create Application          │
│    INSERT INTO applications    │
│      (match_score = 0.87)      │
└────────┬───────────────────────┘
         ↓
┌────────────────────────────────┐
│ 4. Return to User              │
│    "✅ You're an 87% match!"   │
└────────────────────────────────┘
```

---

## 🔧 Part 6: Performance Optimizations

### **1. Caching Layer**

```python
# Redis cache for LLM responses
from langchain.cache import RedisCache

set_llm_cache(RedisCache(redis_client))

# Tool-specific cache
@tool_cache.cached(ttl=1800)  # 30 min
def match_candidates(query):
    # Expensive vector search cached
    return results
```

### **2. Batch Processing**

```python
# Instead of processing profiles one-by-one:
for employee in employees:
    embedding = embed(employee)  # Slow!

# Process in batches:
embeddings = embedding_model.embed_documents([
    employee.profile for employee in employees
])  # 10x faster!
```

### **3. Index Optimization**

```sql
-- Database indexes for fast lookups
CREATE INDEX idx_jobs_title ON jobs(title);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_apps_employee ON applications(employee_id);
CREATE INDEX idx_apps_job ON applications(job_id);
```

### **4. HNSW Parameter Tuning**

```python
# ChromaDB HNSW configuration
collection = client.create_collection(
    name="employee_profiles",
    metadata={
        "hnsw:space": "cosine",        # Distance metric
        "hnsw:M": 16,                  # Graph connectivity
        "hnsw:ef_construction": 200,   # Index quality
        "hnsw:ef_search": 50           # Search quality
    }
)

# Trade-off:
# Higher M, ef = Better accuracy, slower indexing
# Lower M, ef = Faster indexing, lower accuracy
```

---

## 📊 Part 7: Algorithm Complexity Analysis

### **Time Complexity**

```
JobFinderTool (SQL):
- Search: O(n log n)  where n = number of jobs
- With index: O(log n)
- Very fast for <10k jobs

MatchingTool (Vector):
- Without HNSW: O(n * d)  where n = docs, d = dimensions
- With HNSW: O(log n * d)
- Approximate, but fast

JobApplicationTool (Direct):
- O(1) - Direct calculation
- No search involved
```

### **Space Complexity**

```
Embeddings:
- Per profile: 1536 floats × 4 bytes = 6.1 KB
- 1000 profiles: ~6.1 MB
- 100k profiles: ~610 MB
- Manageable with modern hardware

ChromaDB Index:
- HNSW graph: ~2-4x embedding size
- Total: ~15-25 KB per profile
```

---

## 🎓 Summary: Technical Stack

```
┌─────────────────────────────────────────┐
│         AI & ML Layer                   │
│  - OpenAI GPT-4 (reasoning)             │
│  - text-embedding-3-small (vectors)     │
│  - LangChain (orchestration)            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      Vector Database Layer              │
│  - ChromaDB (storage & search)          │
│  - HNSW algorithm (ANN)                 │
│  - Cosine similarity (metric)           │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       Relational Database               │
│  - PostgreSQL (structured data)         │
│  - B-tree indexes (fast lookups)        │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│          Caching Layer                  │
│  - Redis (LLM cache, tool cache)        │
│  - 30min-1hr TTL                        │
└─────────────────────────────────────────┘
```

**That's the deep technical architecture!** 🚀
