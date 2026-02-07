-- Migration for Heart Rate Zones
-- Adds a JSONB column to store athlete's heart rate zones imported from Strava

ALTER TABLE athletes ADD COLUMN IF NOT EXISTS hr_zones JSONB DEFAULT '{}'::jsonb;
