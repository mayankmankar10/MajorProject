# Database Data Management Guide

Complete guide for validating, cleaning, and generating test data for the Manpower Connector database.

## Quick Start

### 1. Validate Your Database

Check for data integrity issues:

```bash
python validate_database.py
```

**Output**: Console report + JSON file (`validation_report_YYYYMMDD_HHMMSS.json`)

---

### 2. Clean Up Issues (Optional)

Preview cleanup (dry-run, no changes):

```bash
python cleanup_database.py --dry-run
```

Execute cleanup (creates backup automatically):

```bash
python cleanup_database.py --execute
```

Skip confirmation prompts:

```bash
python cleanup_database.py --execute --auto-confirm
```

---

### 3. Generate Realistic Test Data

Generate 50 employers and 100 employees:

```bash
python generate_realistic_data.py --employers 50 --employees 100
```

**Key Features:**
- Each employer posts **3-8 different job roles** (Chef, Waiter, Bartender, Cook, Host, Manager)
- Realistic Indian names, cities, companies
- City-based salary adjustments (Tier 1/2/3 cities)
- Experience-based salary calculations
- Automatic duplicate prevention
- Backup created before generation

**Arguments:**
- `--employers N`: Number of employer accounts to create (default: 50)
- `--employees N`: Number of employee accounts to create (default: 100)
- `--applications-per-job N`: Average applications per job (default: 3)
- `--no-backup`: Skip automatic backup

---

## Current Database Status

From latest validation (`2025-12-29`):

**Statistics:**
- Users: 311
- Employers: 202
- Employees: 108  
- Jobs: 181
- Applications: 298

**Issues Found:** 16 total
- 12 orphaned jobs (employer_id 12345 doesn't exist)
- 4 invalid phone formats (missing +91 prefix)

---

## Tools Reference

### validate_database.py

**What it checks:**
- ✅ Duplicate users (same email)
- ✅ Duplicate employers (same company + location)
- ✅ Duplicate employee profiles (same user)
- ✅ Duplicate applications (same job + employee)
- ✅ Orphaned employers (no user account)
- ✅ Orphaned employees (no user account)
- ✅ Orphaned jobs (no employer)
- ✅ Orphaned applications (no job or employee)
- ✅ Missing required fields (email, company_name, full_name, title)
- ✅ Invalid data formats (email, phone, experience)
- ✅ Match scores (must be 0.0-1.0)
- ✅ Relationship consistency (user role matches profile type)
- ✅ Date consistency (updated_at >= created_at)

**Output:**
- Console: Human-readable summary
- File: Detailed JSON report

---

### cleanup_database.py

**Safety Features:**
- **Dry-run mode by default** - preview changes first
- **Automatic backup** before making changes
- **User confirmation** for each operation
- **Detailed logging** of all changes

**Options:**
```bash
--dry-run        # Preview only (default)
--execute        # Actually apply changes
--auto-confirm   # Skip confirmation prompts
--no-backup      # Skip backup creation
```

**What it removes:**
- Duplicate users (keeps oldest by ID)
- Duplicate applications (keeps oldest)
- Orphaned employer profiles
- Orphaned employee profiles
- Orphaned jobs
- Orphaned applications

---

### generate_realistic_data.py

**Realistic Patterns:**

1. **Multiple Roles Per Employer**
   - Each restaurant posts 3-8 different positions
   - Core roles: Chef (1x), Cooks (2-4x), Waiters (3-6x)
   - Optional: Bartender (1-2x), Host (1x), Manager (1x)

2. **Salary Calculation**
   - Base salary by job category:
     - Chef: ₹50,000-100,000
     - Cook: ₹25,000-45,000
     - Bartender: ₹30,000-60,000
     - Waiter: ₹18,000-35,000
     - Manager: ₹60,000-120,000
   - **City multiplier:**
     - Tier 1 (Mumbai, Delhi, Bangalore): 1.3x
     - Tier 2 (Ahmedabad, Jaipur): 1.1x
     - Tier 3: 1.0x
   - **Experience multiplier:** +5% per year

3. **Data Quality**
   - 200+ Indian first names
   - 50+ last names
   - Realistic company names (e.g., "The Golden Spice Italian Restaurant")
   - Valid email formats
   - Proper phone numbers (+91-XXXXXXXXXX)
   - Skill sets matched to roles
   - Cuisine specialization

4. **Duplicate Prevention**
   - Checks existing emails before creation
   - Unique company + location combinations
   - Prevents duplicate applications

**Example Commands:**

```bash
# Create 100 employers, 200 employees
python generate_realistic_data.py --employers 100 --employees 200

# Create data with higher application rate
python generate_realistic_data.py --employers 50 --employees 150 --applications-per-job 5

# Skip backup (not recommended)
python generate_realistic_data.py --employers 25 --employees 50 --no-backup
```

---

### backup_database.py

**Commands:**

```bash
# Create a backup
python backup_database.py create

# List all backups
python backup_database.py list

# Restore from backup (interactive)
python backup_database.py restore

# Restore from specific file
python backup_database.py restore --file db_backups/manpower_backup_20251229_191224.db

# Clean up old backups (keeps last 10)
python backup_database.py cleanup
```

**Features:**
- Timestamped backups
- Automatic verification (checks required tables)
- Safety backup before restore
- Auto-cleanup (max 10 backups)

---

## Recommended Workflow

### First Time Setup

1. **Validate current state:**
   ```bash
   python validate_database.py
   ```

2. **Create backup:**
   ```bash
   python backup_database.py create
   ```

3. **Clean up issues (if any):**
   ```bash
   # Preview first
   python cleanup_database.py --dry-run
   
   # Apply if satisfied
   python cleanup_database.py --execute
   ```

4. **Generate fresh test data:**
   ```bash
   python generate_realistic_data.py --employers 100 --employees 200
   ```

5. **Verify generated data:**
   ```bash
   python validate_database.py
   python show_db_stats.py
   ```

### Regular Maintenance

```bash
# Weekly: Validate data integrity
python validate_database.py

# Monthly: Create backup
python backup_database.py create

# As needed: Generate more test data
python generate_realistic_data.py --employers 50 --employees 100
```

---

## Fixing Current Issues

Based on latest validation, here's how to fix the 16 issues:

### 1. Remove Orphaned Jobs (12 issues)

```bash
python cleanup_database.py --execute
# When prompted, confirm removal of orphaned jobs
```

### 2. Fix Invalid Phone Numbers (4 issues)

**Option A:** Let the data generator create new employees with correct formats

**Option B:** Manual SQL fix:
```sql
UPDATE employees 
SET phone = '+91-' || phone 
WHERE phone NOT LIKE '+91%' AND phone IS NOT NULL;
```

---

## Tips & Best Practices

1. **Always backup before cleanup:**
   - `cleanup_database.py` creates backup automatically (unless `--no-backup`)
   - Manual backups: `python backup_database.py create`

2. **Use dry-run mode first:**
   - Preview changes with `--dry-run` before `--execute`

3. **Check validation after changes:**
   - Run `validate_database.py` after cleanup or generation

4. **Realistic data patterns:**
   - Use Tier 1 cities for higher salaries
   - Mix of experience levels (1-15 years)
   - Diverse roles per employer (3-8 positions)

5. **Scale gradually:**
   - Start with 50 employers, 100 employees 
   - Scale up: 100 employers, 200 employees
   - Large scale: 200+ employers, 300+ employees

---

## Troubleshooting

**Q: "Email already exists" error during generation**
- The generator checks existing emails automatically
- If you hit this, the generator will skip that record
- Increase the `--employers` or `--employees` count

**Q: Validation shows orphaned records after generation**
- Should not happen with new generator
- If it does, run `cleanup_database.py --execute`

**Q: Want to start completely fresh**
1. Backup current database: `python backup_database.py create`
2. Delete or rename `manpower.db`
3. Run Django migrations or schema setup
4. Generate data: `python generate_realistic_data.py --employers 100 --employees 200`

**Q: Generated phone numbers don't match format**
- Update `validate_database.py` phone pattern if needed
- Generator creates phones in format: `+91-XXXXXXXXXX`

---

## File Outputs

| Script | Output Files |
|--------|-------------|
| `validate_database.py` | `validation_report_YYYYMMDD_HHMMSS.json` |
| `cleanup_database.py` | `cleanup_report_YYYYMMDD_HHMMSS.json` |
| `backup_database.py` | `db_backups/manpower_backup_YYYYMMDD_HHMMSS.db` |
| `generate_realistic_data.py` | (Database records only) |

---

## Summary

✅ **validate_database.py** - Find all data issues  
✅ **cleanup_database.py** - Fix duplicates & orphaned records (with backup)  
✅ **generate_realistic_data.py** - Create 100s of realistic records  
✅ **backup_database.py** - Manage database backups  

**All scripts include:**
- Safety features (dry-run, backups)
- Detailed logging & reports
- Error handling
- Progress tracking
