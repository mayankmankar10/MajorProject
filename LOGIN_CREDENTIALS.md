# SmartServe Login Credentials - Test Accounts

## 🏢 Employer Accounts

### 1. Nike (Primary Test Account)
- **Email:** `nil123@gmail.com`
- **Password:** *(Created via manual onboarding)*
- **Company:** Nike
- **User ID:** 3
- **Status:** ✅ Active

---

### 2. Tamarind Restaurant
- **Email:** `hr@tamarindrestaurant.com`
- **Password:** `Tamarind@2024`
- **Company:** Tamarind Restaurant (Fine Dining)
- **Location:** Nariman Point, Mumbai
- **Status:** ✅ Verified

### 3. The Oberoi Hotel Mumbai
- **Email:** `careers@theoberoidelhi.com`
- **Password:** `Oberoi@2024`
- **Company:** The Oberoi Hotel Mumbai (5-Star Luxury)
- **Location:** Nariman Point, Mumbai
- **Status:** ✅ Verified

### 4. Social Restaurants
- **Email:** `jobs@socialoffline.in`
- **Password:** `Social@2024`
- **Company:** Social Restaurants (Casual Dining Chain)
- **Location:** Multiple locations, Mumbai
- **Status:** ✅ Verified

### 5. Indigo Delicatessen
- **Email:** `hr@indigo-mumbai.com`
- **Password:** `Indigo@2024`
- **Company:** Indigo Delicatessen (European Cafe)
- **Location:** Colaba, Mumbai
- **Status:** ✅ Verified

### 6. Bastian - Seafood & Bar
- **Email:** `hiring@bastianrestaurant.com`
- **Password:** `Bastian@2024`
- **Company:** Bastian (Seafood Restaurant)
- **Location:** Bandra, Mumbai
- **Status:** ✅ Verified

### 7. The Bombay Canteen
- **Email:** `jobs@thebombaycanteen.com`
- **Password:** `BombayCanteen@2024`
- **Company:** The Bombay Canteen (Regional Indian)
- **Location:** Lower Parel, Mumbai
- **Status:** ✅ Verified

### 8. Olive Bar & Kitchen
- **Email:** `careers@olive-bar.com`
- **Password:** `Olive@2024`
- **Company:** Olive Bar & Kitchen (Mediterranean)
- **Location:** Bandra, Mumbai
- **Status:** ✅ Verified

### 9. Zomato Kitchen
- **Email:** `hr@zomatokitchen.com`
- **Password:** `ZomatoKitchen@2024`
- **Company:** Zomato Kitchen (Cloud Kitchen)
- **Location:** Andheri, Mumbai
- **Status:** ✅ Verified

---

## 👨‍🍳 Employee Accounts

### 1. Arjun Mehta (Executive Chef)
- **Email:** `chef.arjun@gmail.com`
- **Password:** `Chef@2024`
- **Role:** Executive Chef
- **Experience:** 12 years
- **Specialization:** North Indian Cuisine, Fine Dining
- **Status:** ✅ Active

### 2. Maria Rodrigues (Pastry Chef)
- **Email:** `maria.rodrigues@gmail.com`
- **Password:** `Maria@2024`
- **Role:** Pastry Chef
- **Experience:** 8 years
- **Specialization:** French Pastry, Desserts, Chocolate Work
- **Status:** ✅ Active

### 3. Rajesh Kumar (Sous Chef)
- **Email:** `rajesh.kumar.chef@gmail.com`
- **Password:** `Rajesh@2024`
- **Role:** Sous Chef
- **Experience:** 6 years
- **Specialization:** Multi-Cuisine, Continental, Italian
- **Status:** ✅ Active

### 4. Priya Nair (Restaurant Supervisor)
- **Email:** `priya.nair.server@gmail.com`
- **Password:** `Priya@2024`
- **Role:** Restaurant Supervisor
- **Experience:** 7 years
- **Specialization:** Customer Service, Wine Service, Staff Training
- **Status:** ✅ Active

### 5. Vikram Singh (Head Bartender)
- **Email:** `vikram.bartender@gmail.com`
- **Password:** `Vikram@2024`
- **Role:** Head Bartender
- **Experience:** 5 years
- **Specialization:** Mixology, Cocktail Creation, Bar Management
- **Status:** ✅ Active

### 6. Sneha Deshmukh (Line Cook)
- **Email:** `sneha.cook@gmail.com`
- **Password:** `Sneha@2024`
- **Role:** Line Cook
- **Experience:** 3 years
- **Specialization:** Basic Cooking, Food Prep, Grill
- **Status:** ✅ Active

### 7. Amit Kapoor (Restaurant Manager)
- **Email:** `amit.operations@gmail.com`
- **Password:** `Amit@2024`
- **Role:** Restaurant Manager
- **Experience:** 10 years
- **Specialization:** Operations, P&L Management, Staff Management
- **Status:** ✅ Active

### 8. Ravi Yadav (Fresher)
- **Email:** `ravi.fresher@gmail.com`
- **Password:** `Ravi@2024`
- **Role:** Student/Fresher
- **Experience:** 0 years
- **Specialization:** Entry-level, Eager to Learn
- **Status:** ✅ Active

---

## 🔐 Additional Users (Generated During Onboarding)

The database also contains 90+ employee accounts created through your data generation scripts. These follow the pattern:
- **Email format:** `firstname.lastname##@email.com`
- **Examples:**
  - `aarti.trivedi2@email.com`
  - `tarun.mukherjee5@email.com`
  - `payal.shah7@email.com`

**Note:** These auto-generated accounts likely use a default password. Check your seed scripts for the default password pattern.

---

## 📝 Quick Test Scenarios

### Scenario 1: Employer Posting Jobs
1. Login as: `nil123@gmail.com` or any employer account above
2. Navigate to Jobs page
3. Create new job posting or use bulk hiring

### Scenario 2: Employee Job Search & Application
1. Login as: `chef.arjun@gmail.com` (experienced chef)
2. Browse jobs
3. Apply to relevant positions
4. Check match scores

### Scenario 3: Chat-Based Onboarding
1. Login as: `ravi.fresher@gmail.com` (new employee)
2. Use AI chat to complete profile
3. Test onboarding progress tracking

### Scenario 4: Match Score Testing
1. Login as employer (e.g., Tamarind Restaurant)
2. Post a job requiring specific skills
3. Login as matching employee (e.g., Arjun Mehta)
4. Apply and verify match score calculation

---

## 🌐 Application URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 🔑 Security Note

**⚠️ IMPORTANT:** These are TEST credentials for development only.
- Never use these in production
- All passwords are stored as bcrypt hashes in the database
- Change passwords before deploying to production

---

**Last Updated:** 2026-01-06 12:57 IST
