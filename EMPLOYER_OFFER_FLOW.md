# Employer Offer Flow - Match Score Handling

## 🎯 Overview

When **employers make offers to employees** (reverse flow from employee applying), the system handles match scores differently depending on the scenario.

---

## 📋 Two Main Scenarios

### **Scenario 1: Bulk Hiring Workflow** 
**Tool:** [`BulkHiringWorkflowTool`](file:///c:/manpower_connector/backend/tools_langchain/bulk_hiring_workflow_tool.py)

**When it happens:**
- Employer uses AI chat: "Need 5 waiters and 2 chefs for my Italian restaurant"
- Fully automated end-to-end hiring pipeline

**How match scores are calculated:**

#### Step-by-Step Process:

1️⃣ **Parse Positions** (Natural Language → Structured Data)
   - Input: "Need 5 waiters, 2 chefs"
   - Output: [chef: 2, waiter: 5]

2️⃣ **Create Job Postings** in database

3️⃣ **Match Candidates Using AI Semantic Search**
   ```python
   # Uses MatchingTool with vector embeddings
   match_result = await matcher._arun(
       query_text=job_description,
       match_type="job_to_candidates",
       top_k=quantity * 3,  # Get 3x candidates for selection
       job_id=job_id
   )
   ```

4️⃣ **Calculate Match Scores** (Hybrid AI + Rules)
   - **Semantic similarity** (ChromaDB vector search): 0-60 points
   - **Restaurant-specific bonus**: 0-50 points
     - Food safety cert: +10
     - Alcohol cert: +5  
     - Cuisine match: +15
     - Shift match: +5
     - Experience: +10
     - Customer service: +10
   - **Total score**: 0-100, normalized to 0.00-1.00

5️⃣ **Select Top Candidates**
   - Ranks by final match score
   - Selects exact quantity needed per position

6️⃣ **Create Applications & Offers**
   ```python
   # Line 308-330 in bulk_hiring_workflow_tool.py
   match_score = candidate.get("match_score", 0.75)  # From matching results
   
   # Create or find application
   application = Application(
       job_id=job_id,
       employee_id=employee.id,
       status=ApplicationStatus.OFFER_SENT,
       match_score=match_score  # ✅ Stored in DB
   )
   
   # Create offer record
   offer = Offer(
       application_id=application.id,
       salary_offered="Competitive",
       status="pending"
   )
   ```

7️⃣ **Send Notifications**
   ```python
   # Line 347-360
   notification = Notification(
       title="🎉 Job Offer Received!",
       message=f"Congratulations! You've received an offer for {job_title} 
                at {employer_name}. Match: {int(match_score*100)}%.",
       notification_type="offer_received",
       action_url="/employee/offers"
   )
   ```

**Result:** Employee receives offer with match score already calculated!

---

### **Scenario 2: Manual Employer Selection**
**Tool:** Employer reviews applications manually through UI

**How it works:**

1️⃣ **Employee applies to job** → Match score calculated by `JobApplicationTool`
   ```python
   # _calculate_match_score() - 5 factors
   - Role match: 30%
   - Cuisine: 20%
   - Experience: 20%
   - Certifications: 15%
   - Shift: 15%
   ```

2️⃣ **Employer reviews applications** in dashboard
   - Applications sorted by match score (descending)
   - Employer sees: 87% match, 92% match, etc.

3️⃣ **Employer manually selects candidates**
   - Updates application status: `reviewing` → `selected` → `offer_sent`
   - Match score **remains from original application**
   - No recalculation needed

---

## 🔍 Key Differences

| Aspect | Employee Applies | Employer Offers (Bulk) |
|--------|------------------|------------------------|
| **Match Score Source** | `JobApplicationTool._calculate_match_score()` | `MatchingTool` (AI semantic + bonus) |
| **Calculation Method** | Rule-based (5 weighted factors) | Hybrid (60% AI + 40% rules) |
| **When Calculated** | At application submission | During candidate search |
| **Application Created** | Immediately | Auto-created when offer sent |
| **Score Range** | 0.00 - 1.00 | 0.00 - 1.00 |
| **Stored in DB** | ✅ `applications.match_score` | ✅ `applications.match_score` |

---

## 💡 What This Means for Your Reset

**After resetting the applications table:**

### ✅ Employee Applies to Jobs:
- New applications created
- Match scores calculated fresh using `JobApplicationTool`
- Uses latest employee/job data

### ✅ Employer Uses Bulk Hiring:
- New applications auto-created
- Match scores calculated using `MatchingTool` (AI semantic search)
- Creates offers immediately
- Employees notified with match score

### ✅ Employer Reviews Existing Applications:
- **No applications exist after reset!**
- Employees must apply first
- Then employer can review with match scores

---

## 🔄 Match Score Calculation Summary

### **JobApplicationTool Formula** (Employee-initiated)

```python
def _calculate_match_score(employee, job):
    score = 0.0
    
    # Role match (30%)
    if employee.preferred_role == job.job_category:
        score += 0.30
    
    # Cuisine (20%)
    if job.cuisine_type in employee.cuisine_experience:
        score += 0.20
    
    # Experience (20% + bonus 5%)
    if employee.years >= job.min_experience:
        score += 0.20
        if employee.years >= job.min_experience + 2:
            score += 0.05
    
    # Certifications (15%)
    if job.requires_food_safety and employee.food_safety_certified:
        score += 0.10
    if job.requires_alcohol and employee.alcohol_certified:
        score += 0.05
    
    # Shift (15%)
    if job.shift_type in employee.shift_preferences:
        score += 0.15
    
    return round(score, 2)  # 0.00 to 1.00
```

### **MatchingTool Formula** (Employer bulk hiring)

```python
def calculate_final_score():
    # Phase 1: AI Semantic Similarity
    embedding_similarity = cosine_similarity(job_embedding, employee_embedding)
    base_score = embedding_similarity * 60  # 0-60 points
    
    # Phase 2: Restaurant Bonus
    bonus = 0
    bonus += 10 if food_safety_match else 0
    bonus += 5 if alcohol_cert_match else 0
    bonus += 15 if cuisine_match else 0
    bonus += 5 if shift_match else 0
    bonus += 10 if experience_match else 0
    bonus += 10 if customer_service_skills else 0
    # Max bonus: 50 points
    
    # Phase 3: Combine
    final_score = min(base_score + bonus, 100) / 100  # Normalize to 0-1
    
    return round(final_score, 2)
```

---

## 🎯 Recommendations After Reset

1. **Test Employee Applications First**
   - Have employees apply to jobs through chat/UI
   - Verify match scores are calculated correctly
   - Check scores in applications table

2. **Test Bulk Hiring Workflow**
   - Use employer chat: "Need 3 chefs and 2 waiters"
   - Verify AI semantic matching works
   - Check that offers are created with match scores

3. **Verify Data Consistency**
   - All match scores should reflect fresh employee/job data
   - No old/stale scores from previous onboarding

---

## 📊 Database After Reset & New Activity

**Current State (After Reset):**
```
Applications:     0
Offers:           0
Interviews:       0
Jobs:            56
Employees:       90
Employers:        8
```

**After Employees Apply (Example):**
```sql
-- Application record
INSERT INTO applications (
    job_id, 
    employee_id, 
    status, 
    match_score  -- ✅ Calculated by JobApplicationTool
) VALUES (5, 12, 'pending', 0.87);
```

**After Employer Bulk Hiring (Example):**
```sql
-- Application auto-created
INSERT INTO applications (
    job_id, 
    employee_id, 
    status, 
    match_score  -- ✅ Calculated by MatchingTool (AI)
) VALUES (8, 15, 'offer_sent', 0.92);

-- Offer created
INSERT INTO offers (
    application_id,
    salary_offered,
    status
) VALUES (1, 'Rs. 25,000', 'pending');
```

---

## ✨ Summary

**When employers offer employees:**
- **Bulk Hiring (AI):** Uses semantic matching + restaurant bonuses
- **Manual Review:** Uses existing match scores from employee applications
- **Both approaches:** Store match scores in `applications.match_score`
- **After reset:** All match scores will be fresh and reflect updated data!

Your system is ready to calculate match scores correctly from both directions! 🚀
