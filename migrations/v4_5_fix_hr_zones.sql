-- Migration: Fix hr_zones column in athletes table
-- Date: 2026-02-04
-- Issue: PGRST204 - Column 'hr_zones' not found in schema cache

-- Add hr_zones column if it doesn't exist
ALTER TABLE athletes 
ADD COLUMN IF NOT EXISTS hr_zones JSONB DEFAULT '[]'::jsonb;

-- Add comment for documentation
COMMENT ON COLUMN athletes.hr_zones IS 'Heart rate zones from Strava API (array of zone objects)';

-- Optional: Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_athletes_hr_zones ON athletes USING GIN (hr_zones);
