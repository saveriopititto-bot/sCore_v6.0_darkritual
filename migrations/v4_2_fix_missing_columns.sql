-- Migration: Fix Missing Columns for v4.2 Schema
-- Date: 2026-02-05
-- Issues: PGRST204 - Column 'name' not found in runs table, Column 'updated_at' not found in athlete_baselines table

-- 1. Add missing 'name' column to runs table
ALTER TABLE runs 
ADD COLUMN IF NOT EXISTS name TEXT DEFAULT 'Untitled Run';

-- Add comment for documentation
COMMENT ON COLUMN runs.name IS 'Activity name from Strava (e.g., "Morning Run", "Lunch Run")';

-- 2. Add missing 'updated_at' column to athlete_baselines table
ALTER TABLE athlete_baselines 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add comment for documentation  
COMMENT ON COLUMN athlete_baselines.updated_at IS 'Last update timestamp for the baseline record';

-- 3. Create index for better query performance on athlete_baselines
CREATE INDEX IF NOT EXISTS idx_athlete_baselines_updated_at ON athlete_baselines(updated_at);

-- 4. Optional: Add index for runs.name for better search performance
CREATE INDEX IF NOT EXISTS idx_runs_name ON runs(name);