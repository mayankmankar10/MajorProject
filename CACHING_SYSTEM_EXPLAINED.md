# Background Caching System Explained

Your manpower_connector application has a **multi-layered caching system** that optimizes performance and reduces costs. Here's how it all works together.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  Tool Cache      │      │  Redis Cache     │            │
│  │  (In-Memory)     │      │  (External)      │            │
│  │  - 100 entries   │      │  - Chat history  │            │
│  │  - 5 min TTL     │      │  - Optional      │            │
│  └──────────────────┘      └──────────────────┘            │
│           │                          │                       │
│           └──────────┬───────────────┘                       │
│                      │                                       │
│         ┌────────────▼──────────────┐                       │
│         │  Database Cache           │                       │
│         │  (ProfileCache table)     │                       │
│         │  - Permanent storage      │                       │
│         │  - AI analysis results    │                       │
│         └───────────────────────────┘                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘

         ┌────────────────────────────┐
         │  Background Jobs           │
         │  - Nightly analysis (00:00)│
         │  - Weekly cleanup (Sun 02:00)│
         └────────────────────────────┘
```

---

## 📦 Layer 1: Tool Cache (In-Memory)

**File:** [`backend/cache/tool_cache.py`](file:///c:/manpower_connector/backend/cache/tool_cache.py)

### What It Does
Caches results from AI tool calls (like profile analysis, job matching) to avoid repeating expensive operations.

### How It Works

1. **Before running a tool:**
   ```python
   # Check cache first
   cached_result = tool_cache.get("ProfileAnalyzer", employee_id=123)
   if cached_result:
       return cached_result  # ✅ Cache HIT - no AI call needed!
   ```

2. **After running a tool:**
   ```python
   # Store result for future use
   tool_cache.set("ProfileAnalyzer", result, ttl=300, employee_id=123)
   ```

### Configuration
- **Max Size:** 100 entries
- **TTL:** 5 minutes (300 seconds)
- **Eviction:** FIFO (First In, First Out) when full
- **Auto-cleanup:** Expired entries removed automatically

### Key Features
- **MD5 Hashing:** Generates unique keys from tool name + parameters
- **Statistics:** Tracks cache hits/misses for monitoring
- **Expiration:** Old entries automatically expire
- **Memory-efficient:** Limited to 100 entries max

### Example Use Case
```python
# First call - MISS (runs AI analysis)
analyze_profile(employee_id=123)  # Takes 2 seconds, costs $0.01

# Second call within 5 minutes - HIT (instant)
analyze_profile(employee_id=123)  # Takes 0.001 seconds, costs $0.00
```

---

## 🔴 Layer 2: Redis Cache (External, Optional)

**File:** [`backend/cache/redis_client.py`](file:///c:/manpower_connector/backend/cache/redis_client.py)

### What It Does
Provides persistent caching across server restarts, primarily used for **chat history**.

### How It Works

```python
# Check if Redis is enabled
if redis_cache.enabled:
    # Try to get from Redis first
    cached_data = redis_cache.get(f"chat:{session_id}")
    if cached_data:
        return json.loads(cached_data)

# If not in cache, fetch from database
history = fetch_from_database(session_id)

# Store in Redis for next time
if redis_cache.enabled:
    redis_cache.set(f"chat:{session_id}", json.dumps(history), ttl=3600)
```

### Configuration
- **Status:** Currently **DISABLED** (`REDIS_ENABLED=false` in `.env`)
- **TTL:** 1 hour (3600 seconds) for chat sessions
- **Fallback:** Gracefully degrades to database-only if unavailable

### Features
- **Automatic Fallback:** If Redis is unavailable, system continues working
- **Connection Testing:** Tests connection on startup
- **Error Handling:** All errors caught and logged
- **Pattern Matching:** Can clear multiple keys at once

### Why It's Optional
- ✅ **Development:** Works fine without Redis
- ✅ **Production:** Recommended for high-traffic applications
- ✅ **Your Current Setup:** Database + in-memory caching is sufficient

---

## 💾 Layer 3: Database Cache (ProfileCache Table)

**Model:** [`backend/db/models.py:ProfileCache`](file:///c:/manpower_connector/backend/db/models.py#L230-L253)

### What It Does
Permanently stores AI-generated profile analysis results in the database.

### Database Schema
```sql
CREATE TABLE profile_cache (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER UNIQUE,  -- One cache per employee
    professional_summary TEXT,
    experience_level VARCHAR,     -- "entry", "mid", "senior"
    top_skills JSON,             -- ["customer service", ...]
    recommended_roles JSON,      -- ["waiter", "server", ...]
    strengths JSON,              -- ["Friendly", "Fast learner"]
    analyzed_at DATETIME,
    cache_version INTEGER,       -- For invalidation
    is_stale BOOLEAN             -- Mark for re-analysis
);
```

### How It Works

1. **AI analyzes profile:**
   ```python
   result = await analyze_employee_profile(employee_id=123)
   ```

2. **Stores in database:**
   ```python
   cache_entry = ProfileCache(
       employee_id=123,
       professional_summary="Experienced waiter...",
       experience_level="mid",
       top_skills=["customer service", "multitasking"],
       analyzed_at=datetime.utcnow()
   )
   db.add(cache_entry)
   db.commit()
   ```

3. **Future requests use cached data:**
   ```python
   # Check database first
   cached = db.query(ProfileCache).filter_by(employee_id=123).first()
   if cached:
       return cached  # No AI call needed!
   ```

### When Data is Refreshed
- **Manual update:** When employee updates their profile
- **Background job:** Nightly analysis of new/updated profiles
- **Stale marker:** `is_stale=True` forces re-analysis

---

## ⏰ Layer 4: Background Jobs (Scheduled Tasks)

**File:** [`backend/background_jobs.py`](file:///c:/manpower_connector/backend/background_jobs.py)

### What They Do
Automatic maintenance tasks that keep your cache fresh without manual intervention.

### Job 1: Nightly Profile Analysis

**Schedule:** Every day at **00:00 (midnight)**

**What it does:**
```python
async def analyze_profiles_nightly():
    # Find employees with new/updated profiles
    # Run AI analysis on them
    # Store results in ProfileCache table
    # Log statistics (processed, cost, duration)
```

**Purpose:**
- Analyzes profiles added/updated during the day
- Runs during low-traffic hours (midnight)
- Keeps cache fresh for next day's job matching
- Processes in batches (10 at a time) to manage cost

### Job 2: Weekly Cache Cleanup

**Schedule:** Every **Sunday at 02:00 AM**

**What it does:**
```python
async def cleanup_stale_cache_weekly():
    # Find cache entries older than 30 days
    # Delete them from ProfileCache table
    # Free up database space
```

**Purpose:**
- Removes outdated analysis results
- Keeps database size manageable
- Forces re-analysis of old profiles

### Job 3: Startup Catch-Up

**Schedule:** Runs **once when backend starts**

**What it does:**
```python
async def check_and_run_startup_catchup():
    # Check when last analysis ran
    # If > 24 hours ago, run analysis
    # Catches up on missed jobs
```

**Purpose:**
- Handles missed jobs if server was down
- Ensures cache is recent on startup
- First-time setup for new installations

---

## 🔄 Complete Caching Flow Example

Let's trace what happens when a job is posted and needs matching:

### Step 1: New Job Posted
```python
employer_posts_job(title="Waiter Needed", cuisine="Italian")
```

### Step 2: Find Matching Employees
```python
# System needs to analyze all employee profiles
for employee in employees:
    
    # Check Tool Cache first (in-memory, 5 min TTL)
    profile = tool_cache.get("ProfileAnalyzer", employee_id=employee.id)
    
    if profile:
        # ✅ HIT: Use cached result (instant, $0.00)
        continue
    
    # Check Database Cache (ProfileCache table)
    profile = db.query(ProfileCache).filter_by(
        employee_id=employee.id
    ).first()
    
    if profile:
        # ✅ HIT: Use database cache (fast, $0.00)
        # Also store in tool cache for faster subsequent access
        tool_cache.set("ProfileAnalyzer", profile, employee_id=employee.id)
        continue
    
    # ❌ MISS: Need to run AI analysis
    profile = await run_expensive_ai_analysis(employee)  # 2 sec, $0.01
    
    # Store in both caches
    tool_cache.set("ProfileAnalyzer", profile, employee_id=employee.id)
    db.add(ProfileCache(employee_id=employee.id, **profile))
    db.commit()
```

### Step 3: Next Day (Background Job Runs)
```python
# At midnight, background job runs
# Analyzes any new/updated profiles
# Updates ProfileCache table
# Next job match will hit cache immediately
```

---

## 📊 Performance Impact

### Without Caching
```
Job Match Request
├─ Analyze 100 employees
│  └─ Each takes 2 seconds, costs $0.01
├─ Total: 200 seconds (3.3 minutes)
└─ Total cost: $1.00
```

### With Caching (After First Run)
```
Job Match Request
├─ Check 100 employees
│  └─ 95 HITs from cache (instant)
│  └─ 5 MISSes need analysis (10 seconds)
├─ Total: 10 seconds
└─ Total cost: $0.05
```

**Improvement:**
- ⚡ **95% faster** (10s vs 200s)
- 💰 **95% cheaper** ($0.05 vs $1.00)

---

## 🎯 Cache Strategy Summary

| Cache Layer | Storage | TTL | Use Case |
|------------|---------|-----|----------|
| **Tool Cache** | In-Memory | 5 min | Quick repeated calls within session |
| **Redis** | External | 1 hour | Chat history, cross-session persistence |
| **ProfileCache** | Database | Permanent | AI analysis results, long-term storage |
| **Background Jobs** | - | Nightly/Weekly | Keep caches fresh automatically |

---

## 🔧 Configuration

### Current Setup (`.env`)
```bash
# Redis is currently DISABLED
REDIS_ENABLED=false
# REDIS_URL=redis://localhost:6379
```

### Tool Cache (Hardcoded)
```python
tool_cache = ToolCache(
    max_size=100,        # 100 entries max
    default_ttl=300      # 5 minutes
)
```

### Database Cache (Automatic)
- No configuration needed
- Managed by background jobs
- Refreshed nightly

---

## 📈 Monitoring Cache Performance

### Check Tool Cache Stats
```python
from backend.cache.tool_cache import tool_cache

stats = tool_cache.get_stats()
# {
#     'size': 45,           # 45/100 slots used
#     'hits': 120,          # 120 cache hits
#     'misses': 30,         # 30 cache misses
#     'hit_rate': 0.80,     # 80% hit rate
#     'utilization': 0.45   # 45% full
# }
```

### Check Background Jobs
```python
# View scheduled jobs
from backend.background_jobs import scheduler
jobs = scheduler.get_jobs()

# Manually trigger (for testing)
await trigger_profile_analysis_manually()
```

### Check Database Cache
```sql
-- See cache coverage
SELECT COUNT(*) as cached_profiles FROM profile_cache;

-- See recent analyses
SELECT employee_id, analyzed_at, experience_level 
FROM profile_cache 
ORDER BY analyzed_at DESC 
LIMIT 10;
```

---

## 💡 Key Takeaways

1. **Three-Layer System:**
   - Tool Cache (in-memory) → Fastest, shortest TTL
   - Redis (optional) → Medium speed, session-level
   - Database (permanent) → Permanent, AI results

2. **Background Jobs:**
   - Nightly at midnight: Analyze new profiles
   - Sunday at 2 AM: Clean old cache
   - Startup: Catch-up if needed

3. **Performance:**
   - 95% reduction in AI costs after first analysis
   - Near-instant job matching for cached profiles
   - Automatic cache maintenance

4. **Reliability:**
   - Redis failure doesn't break the app
   - Database cache persists across restarts
   - Background jobs catch up after downtime

Your caching system is designed for **cost efficiency** and **performance** while maintaining **reliability**! 🎉
