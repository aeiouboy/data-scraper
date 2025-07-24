-- Migration: Add missing columns to scrape_jobs table
-- This script adds retailer_code and duration_seconds columns that are required by the monitoring API

-- Add retailer_code column to track which retailer the job is for
ALTER TABLE scrape_jobs 
ADD COLUMN IF NOT EXISTS retailer_code VARCHAR(5);

-- Add duration_seconds column to track job execution time
ALTER TABLE scrape_jobs 
ADD COLUMN IF NOT EXISTS duration_seconds INTEGER;

-- Add index for better performance when filtering by retailer
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_retailer_code ON scrape_jobs(retailer_code);

-- Add index for queries that filter by date and retailer
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_retailer_created ON scrape_jobs(retailer_code, created_at DESC);

-- Update existing jobs to have a default retailer_code if needed
-- This assumes existing jobs were for HomePro (HP)
UPDATE scrape_jobs 
SET retailer_code = 'HP' 
WHERE retailer_code IS NULL;

-- Calculate duration_seconds for completed jobs that have both started_at and completed_at
UPDATE scrape_jobs 
SET duration_seconds = EXTRACT(EPOCH FROM (completed_at - started_at))::INTEGER
WHERE duration_seconds IS NULL 
  AND started_at IS NOT NULL 
  AND completed_at IS NOT NULL;

-- Add comment to document the columns
COMMENT ON COLUMN scrape_jobs.retailer_code IS 'Retailer code (HP=HomePro, TWD=Thai Watsadu, GH=Global House, DH=DoHome, BT=Boonthavorn, MH=MegaHome)';
COMMENT ON COLUMN scrape_jobs.duration_seconds IS 'Job execution duration in seconds';

-- Verify the migration
DO $$
BEGIN
    -- Check if columns exist
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'scrape_jobs' 
        AND column_name IN ('retailer_code', 'duration_seconds')
    ) THEN
        RAISE NOTICE 'Migration completed successfully!';
        RAISE NOTICE 'Added columns: retailer_code (VARCHAR), duration_seconds (INTEGER)';
    ELSE
        RAISE EXCEPTION 'Migration failed - columns were not added';
    END IF;
END
$$;

-- Optional: Update the scrape_jobs table constraint to ensure duration is non-negative
ALTER TABLE scrape_jobs 
ADD CONSTRAINT check_duration_positive 
CHECK (duration_seconds IS NULL OR duration_seconds >= 0);