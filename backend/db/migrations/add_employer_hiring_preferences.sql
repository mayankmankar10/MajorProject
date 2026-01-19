-- Migration: Add hiring_preferences to employers table
-- Date: 2026-01-03
-- Description: Add hiring_preferences JSON column to store employer's typical hiring needs

-- Add hiring_preferences column
ALTER TABLE employers ADD COLUMN hiring_preferences JSON DEFAULT '[]';

-- Update existing records to have empty array
UPDATE employers SET hiring_preferences = '[]' WHERE hiring_preferences IS NULL;
