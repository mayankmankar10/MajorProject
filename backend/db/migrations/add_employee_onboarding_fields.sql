"""
Database migration to add missing Employee fields for onboarding.
Run this SQL script manually in your database.
"""

-- Add missing columns to employees table
ALTER TABLE employees ADD COLUMN IF NOT EXISTS preferred_shift VARCHAR;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS expected_salary_min INTEGER;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS expected_salary_max INTEGER;

-- Add comments
COMMENT ON COLUMN employees.preferred_shift IS 'Single preferred shift from onboarding (e.g., Morning, Evening, Night)';
COMMENT ON COLUMN employees.expected_salary_min IS 'Minimum expected salary in rupees per month';
COMMENT ON COLUMN employees.expected_salary_max IS 'Maximum expected salary in rupees per month';
