# 🌱 Data Seeding Guide for SmartServe

## Overview

This guide explains all the ways you can add **real, legitimate data** to your SmartServe database for proper testing of agents and tools.

---

## 🎯 Why You Need Real Data

Testing with real data helps you:
- ✅ Verify agents understand complex, realistic queries
- ✅ Test tool performance with varied inputs
- ✅ Identify edge cases and errors
- ✅ Validate match scores and recommendations
- ✅ Ensure the system works with production-like scenarios

---

## 📋 Methods to Add Real Data

### **Method 1: Automated Realistic Data Seeder** ⭐ **RECOMMENDED**

Use the comprehensive seeding script that creates production-quality data.

#### **What It Creates:**
- **8 Employers:** Real Mumbai restaurants (Tamarind, Oberoi, Social, Bastian, etc.)
- **8 Employees:** Realistic profiles with detailed resumes
  - Executive Chef (12 years exp)
  - Pastry Chef (8 years exp)
  - Sous Chef (6 years exp)
  - Restaurant Supervisor (7 years exp)
  - Head Bartender (5 years exp)
  - Line Cook (3 years exp)
  - Restaurant Manager (10 years exp)
  - Fresher/Trainee
- **15+ Jobs:** Varied positions with realistic descriptions
- **30+ Applications:** With calculated match scores and varied statuses

#### **How to Run:**

```powershell
# Navigate to backend directory
cd backend

# Run the seeding script
python scripts/seed_realistic_data.py
```

#### **Options:**
1. **Seed new data** - Adds data to existing database
2. **Clear and seed fresh** - ⚠️ Deletes all data first, then seeds

#### **Login Credentials:**

**Employers:**
```
Tamarind Restaurant:
  Email: hr@tamarindrestaurant.com
  Password: Tamarind@2024

The Oberoi Hotel:
  Email: careers@theoberoidelhi.com  
  Password: Oberoi@2024

Social Restaurants:
  Email: jobs@socialoffline.in
  Password: Social@2024

(See script for all 8 employers)
```

**Employees:**
```
Arjun Mehta (Executive Chef):
  Email: chef.arjun@gmail.com
  Password: Chef@2024

Maria Rodrigues (Pastry Chef):
  Email: maria.rodrigues@gmail.com
  Password: Maria@2024

(See script for all 8 employees)
```

---

### **Method 2: Through the UI (Manual Registration)**

#### **For Employees:**

1. **Register New Account**
   - Go to `/auth/register`
   - Select "Employee" role
   - Fill in email and password

2. **Complete Onboarding**
   - Upload/paste resume
   - Add skills
   - Set preferences
   - Specify availability

3. **Browse and Apply to Jobs**
   - Search for jobs
   - Use "Quick Apply" feature
   - Applications create real records with match scores

#### **For Employers:**

1. **Register New Account**
   - Go to `/auth/register`
   - Select "Employer" role
   - Fill in company details

2. **Post Jobs**
   - Use job posting form
   - Or chat with AI: "Post a chef job in Mumbai, salary 50-80k"
   - Jobs get indexed in vector store

3. **Review Applications**
   - View candidates for your jobs
   - Update application statuses
   - Schedule interviews

---

### **Method 3: Through AI Chat Interface** ⚡ **BEST FOR TESTING AGENTS**

This is the most powerful way to test your agents and tools!

#### **Employee Chat Commands:**

```
"Find chef jobs in Mumbai"
→ Tests JobSearchTool

"Apply to job #5"
→ Tests JobApplicationTool

"What's my application status?"
→ Tests ApplicationStatusTool

"Show my profile"
→ Tests ProfileRetrievalTool

"Update my skills to include Italian cuisine and team leadership"
→ Tests ProfileUpdateTool
```

#### **Employer Chat Commands:**

```
"Post a job for Executive Chef, salary 60-90k, location Mumbai"
→ Tests JobPostingTool

"Find candidates for job #3"
→ Tests CandidateSearchTool

"Show applications for my latest job"
→ Tests ApplicationStatusTool

"Schedule interview for application #12 on 2024-12-28 at 2 PM"
→ Tests InterviewManagementTool

"Update application #15 status to interview_scheduled"
→ Tests ApplicationStatusTool
```

---

### **Method 4: Direct API Calls (For Advanced Testing)**

Use tools like Postman or `curl` to make direct API requests.

#### **Example: Create Employee Profile**

```powershell
# Register user
curl -X POST http://localhost:8000/api/auth/register `
  -H "Content-Type: application/json" `
  -d '{
    "email": "test.chef@example.com",
    "password": "TestPass123",
    "role": "employee",
    "full_name": "Test Chef"
  }'

# Login to get token
curl -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{
    "email": "test.chef@example.com",
    "password": "TestPass123"
  }'

# Use token to update profile
curl -X PUT http://localhost:8000/api/employees/me `
  -H "Authorization: Bearer <your_token>" `
  -H "Content-Type: application/json" `
  -d '{
    "skills": ["Italian Cuisine", "Team Leadership"],
    "experience_years": 8,
    "resume_text": "..."
  }'
```

---

### **Method 5: Database Migration/Import**

If you have existing data in CSV or JSON format:

#### **Step 1: Create Import Script**

```python
# backend/scripts/import_from_csv.py
import pandas as pd
from backend.db.sql_db import SessionLocal
from backend.db.models import Employee, User
from backend.utils.security import get_password_hash

db = SessionLocal()

# Read CSV
df = pd.read_csv('employees.csv')

for _, row in df.iterrows():
    user = User(
        email=row['email'],
        hashed_password=get_password_hash(row['password']),
        role='employee'
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    employee = Employee(
        user_id=user.id,
        full_name=row['name'],
        skills=row['skills'].split(','),
        experience_years=row['experience'],
        resume_text=row['resume']
    )
    db.add(employee)
    db.commit()

print("Import complete!")
```

#### **Step 2: Run Import**

```powershell
python backend/scripts/import_from_csv.py
```

---

## 🧪 Testing Your Agents with Real Data

After seeding data, test your agents systematically:

### **1. Test Job Matching**

```python
# Login as employee (e.g., chef.arjun@gmail.com)
Chat: "Find chef jobs in Mumbai"

Expected:
- JobSearchTool is called
- Returns relevant jobs based on skills
- Match scores are calculated
- Results are well-formatted
```

### **2. Test Application Flow**

```python
Chat: "Apply to the Executive Chef position at Tamarind"

Expected:
- JobApplicationTool is called
- Match score is calculated
- Application record is created
- Confirmation message is returned
```

### **3. Test Status Tracking**

```python
Chat: "What's the status of my applications?"

Expected:
- ApplicationStatusTool is called
- Returns all applications with current status
- Shows match scores and dates
- Formatted clearly
```

### **4. Test Employer Tools**

```python
# Login as employer (e.g., hr@tamarindrestaurant.com)
Chat: "Show me the best candidates for my Executive Chef position"

Expected:
- CandidateSearchTool is called
- Returns ranked candidates
- Shows match scores
- Includes relevant experience
```

### **5. Test Interview Scheduling**

```python
Chat: "Schedule an interview with Arjun Mehta for tomorrow at 3 PM"

Expected:
- InterviewManagementTool is called
- Creates interview record
- Updates application status
- Returns confirmation
```

---

## 📊 Verifying Data Quality

### **Check Database Records:**

```powershell
# Connect to your database
# For SQLite:
sqlite3 backend/smartserve.db

# Run queries
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM employers;
SELECT COUNT(*) FROM employees;
SELECT COUNT(*) FROM jobs;
SELECT COUNT(*) FROM applications;

# Check specific data
SELECT full_name, experience_years FROM employees;
SELECT company_name, COUNT(jobs.id) as job_count 
FROM employers 
LEFT JOIN jobs ON employers.id = jobs.employer_id 
GROUP BY employers.id;
```

### **Check via API:**

```powershell
# Get all jobs
curl http://localhost:8000/api/jobs

# Get specific employee
curl http://localhost:8000/api/employees/1

# Check applications
curl http://localhost:8000/api/applications
```

---

## 🎨 Customizing the Realistic Data

You can modify `backend/scripts/seed_realistic_data.py` to:

### **Add Your Own Restaurants:**

```python
employers_data.append({
    "email": "your@restaurant.com",
    "password": "YourPass@2024",
    "company_name": "Your Restaurant Name",
    "industry": "Fine Dining",
    "location": "Your Location",
    "description": "Your description...",
    "website": "www.yoursite.com",
    "verified": True
})
```

### **Add Custom Employees:**

```python
employees_data.append({
    "email": "custom.employee@gmail.com",
    "password": "Pass@2024",
    "full_name": "Employee Name",
    "phone": "+91-1234567890",
    "location": "Mumbai",
    "current_role": "Your Role",
    "experience_years": 5,
    "skills": ["Skill1", "Skill2"],
    "preferred_roles": ["chef"],
    "availability": "Immediate",
    "resume_text": """YOUR DETAILED RESUME HERE"""
})
```

### **Add More Jobs:**

```python
"Your Restaurant Name": [
    {
        "title": "Your Job Title",
        "description": "Detailed job description...",
        "requirements": "Requirements list",
        "location": "Location",
        "job_type": "full_time",
        "salary_min": 50000,
        "salary_max": 80000,
        "job_category": JobCategory.CHEF,
        "quantity_needed": 1
    },
]
```

---

## 🔄 Resetting Data

### **Clear All Data:**

```python
python backend/scripts/seed_realistic_data.py
# Choose option 2: "Clear ALL data and seed fresh"
```

### **Clear Specific Tables:**

```python
# Create a custom script
from backend.db.sql_db import SessionLocal
from backend.db.models import Application, Job

db = SessionLocal()

# Delete all applications
db.query(Application).delete()
db.commit()

# Delete all jobs
db.query(Job).delete()
db.commit()

print("Cleared applications and jobs")
```

---

## 📝 Best Practices

1. ✅ **Start with realistic seeder** for comprehensive testing
2. ✅ **Test one agent/tool at a time** to isolate issues
3. ✅ **Use varied employee profiles** (junior, senior, specialized)
4. ✅ **Create jobs with different requirements** to test matching
5. ✅ **Vary application statuses** to test status tracking
6. ✅ **Test edge cases**: no skills, very high/low experience, etc.
7. ✅ **Monitor agent responses** and tool calls in logs
8. ✅ **Keep test data separate** from production data

---

## 🐛 Troubleshooting

### **Issue: "No users found"**
- **Solution:** Run the seeding script
- Verify database connection in `.env`

### **Issue: "Match scores all 0.5"**
- **Solution:** Ensure employee skills are set
- Check job descriptions contain relevant keywords

### **Issue: "Agent not calling tools"**
- **Solution:** Check orchestrator initialization
- Verify tools are registered
- Check agent prompts

### **Issue: "Database locked"**
- **Solution:** Close any open database connections
- Restart the backend server

---

## 📚 Additional Resources

- **Database Models:** `backend/db/models.py`
- **API Routes:** `backend/routes/`
- **Tools:** `backend/tools_langchain/`
- **Agent Logic:** `backend/orchestration/`

---

## 🎯 Quick Start Checklist

- [ ] Run realistic data seeder
- [ ] Verify data in database
- [ ] Login as employee (chef.arjun@gmail.com)
- [ ] Test job search in chat
- [ ] Test application creation
- [ ] Login as employer (hr@tamarindrestaurant.com)
- [ ] Test candidate search
- [ ] Test interview scheduling
- [ ] Monitor logs for tool calls
- [ ] Verify database records updated

---

**Now you're ready to test your agents with real, production-quality data! 🚀**
