# Database Schema Fix - Manual Instructions

## Issue
The database is missing two columns that the application expects:
1. `name` column in the `runs` table
2. `updated_at` column in the `athlete_baselines` table

## Solution
Execute the following SQL statements in your Supabase SQL Editor:

### 1. Add missing 'name' column to runs table
```sql
ALTER TABLE runs 
ADD COLUMN IF NOT EXISTS name TEXT DEFAULT 'Untitled Run';

-- Add comment for documentation
COMMENT ON COLUMN runs.name IS 'Activity name from Strava (e.g., "Morning Run", "Lunch Run")';
```

### 2. Add missing 'updated_at' column to athlete_baselines table
```sql
ALTER TABLE athlete_baselines 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add comment for documentation  
COMMENT ON COLUMN athlete_baselines.updated_at IS 'Last update timestamp for the baseline record';
```

### 3. Create indexes for better performance
```sql
-- Index for athlete_baselines.updated_at
CREATE INDEX IF NOT EXISTS idx_athlete_baselines_updated_at ON athlete_baselines(updated_at);

-- Index for runs.name (optional, for search performance)
CREATE INDEX IF NOT EXISTS idx_runs_name ON runs(name);
```

### 4. Verify the changes
```sql
-- Check runs table columns
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'runs' 
AND table_schema = 'public'
ORDER BY ordinal_position;

-- Check athlete_baselines table columns
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'athlete_baselines' 
AND table_schema = 'public'
ORDER BY ordinal_position;
```

## How to Execute

### Option 1: Supabase Dashboard
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy and paste each SQL block above
4. Execute them one by one

### Option 2: Using psql (if you have direct database access)
```bash
psql -h your-project-ref.supabase.co -U postgres -d postgres -f migrations/v4_2_fix_missing_columns.sql
```

### Option 3: Using the migration script
```bash
python migrate.py
```

## After Execution
After running these SQL statements, the PGRST204 errors should be resolved and the application should be able to save runs and update athlete baselines properly.

## Testing
1. Restart your Streamlit application
2. Try syncing activities from Strava
3. Check that runs are being saved without the "name column" error
4. Check that athlete baselines are being updated without the "updated_at column" error