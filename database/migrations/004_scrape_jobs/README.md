# Migration 004: Scrape Jobs Enhancement

**Migration ID**: 004
**Name**: Scrape Jobs Enhancement
**Dependencies**: 001, 002, 003
**Applied**: Scrape job monitoring enhancements

## Purpose

Enhances the scrape_jobs table with additional columns required for comprehensive job monitoring and retailer-specific tracking.

## Changes Made

### Columns Added
- **retailer_code** (VARCHAR(5)): Tracks which retailer the job is for
- **duration_seconds** (INTEGER): Records job execution time in seconds

### Indexes Added
- `idx_scrape_jobs_retailer_code`: For filtering by retailer
- `idx_scrape_jobs_retailer_created`: Composite index for retailer + date queries

### Constraints Added
- `check_duration_positive`: Ensures duration is non-negative

### Data Migration
- Updates existing jobs with default retailer_code 'HP'
- Calculates duration for completed jobs with start/end times

## Files

- `add_missing_columns.sql` - Main migration script with all enhancements

## Execution Notes

1. **Prerequisites**: Migrations 001-003 applied
2. **Execution Time**: ~10-30 seconds depending on existing data
3. **Rollback**: Safe (can drop columns and indexes)
4. **Data Impact**: Adds metadata, no data loss

## Validation Queries

```sql
-- Verify columns were added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'scrape_jobs' 
AND column_name IN ('retailer_code', 'duration_seconds');

-- Verify indexes were created
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'scrape_jobs' 
AND indexname LIKE 'idx_scrape_jobs_%';

-- Verify constraint was added
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'scrape_jobs' 
AND constraint_name = 'check_duration_positive';

-- Test the enhanced functionality
SELECT retailer_code, COUNT(*), AVG(duration_seconds)
FROM scrape_jobs 
WHERE duration_seconds IS NOT NULL
GROUP BY retailer_code;
```

## Business Impact

After this migration:
- ✅ Job monitoring includes retailer-specific tracking
- ✅ Execution time tracking for performance analysis
- ✅ Better query performance for retailer-filtered reports
- ✅ Historical data preserved and enhanced with defaults

## API Changes

The monitoring API endpoints now support:
- Filtering jobs by retailer_code
- Performance metrics with duration tracking
- Retailer-specific job statistics

## Rollback Procedure

If rollback is needed:

```sql
-- Remove constraint
ALTER TABLE scrape_jobs DROP CONSTRAINT IF EXISTS check_duration_positive;

-- Remove indexes
DROP INDEX IF EXISTS idx_scrape_jobs_retailer_code;
DROP INDEX IF EXISTS idx_scrape_jobs_retailer_created;

-- Remove columns
ALTER TABLE scrape_jobs DROP COLUMN IF EXISTS retailer_code;
ALTER TABLE scrape_jobs DROP COLUMN IF EXISTS duration_seconds;
```

## Next Steps

After successful application:
1. Update scraping scripts to populate retailer_code
2. Implement duration tracking in scraping logic
3. Update monitoring dashboards to use new fields
4. Proceed to Migration 005 (Monitoring Schedules)

---
*This migration is safe to rollback and enhances existing functionality without breaking changes.*