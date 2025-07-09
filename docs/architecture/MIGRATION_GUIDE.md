# Database Migration Guide

## Overview

This guide covers the database migration needed to fix the missing columns error in the scrape_jobs table.

## Error Description

The monitoring router (`/api/v1/monitoring/*`) endpoints are failing with:
- `column scrape_jobs.retailer_code does not exist`
- `column scrape_jobs.duration_seconds does not exist`

## Migration Steps

### 1. Run the Migration Script

Execute the following SQL script in your Supabase SQL Editor:

```sql
-- Location: scripts/add_missing_scrape_jobs_columns.sql
```

This script will:
- Add `retailer_code` column (VARCHAR(5)) to track which retailer the job is for
- Add `duration_seconds` column (INTEGER) to track job execution time
- Create indexes for better query performance
- Update existing rows with default values where applicable

### 2. Apply the Multi-Retailer Schema (Optional but Recommended)

If you haven't already applied the multi-retailer schema updates, run:

```sql
-- Location: scripts/multi_retailer_schema.sql
```

This adds comprehensive multi-retailer support including:
- Retailer configurations
- Product matching across retailers
- Monitoring tiers
- Performance views

### 3. Verify the Migration

After running the scripts, verify the changes:

```sql
-- Check if columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'scrape_jobs' 
AND column_name IN ('retailer_code', 'duration_seconds');

-- Check indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'scrape_jobs' 
AND indexname LIKE '%retailer%';
```

## Code Updates Applied

The following code changes have been made to support the new columns:

### 1. Updated ScrapeJob Model (`app/models/product.py`)

- Added `retailer_code: Optional[str] = None` field
- Added `duration_seconds: Optional[int] = None` field
- Added `to_supabase_dict()` method that automatically calculates duration_seconds

### 2. Monitoring Router Compatibility

The monitoring router (`app/api/routers/monitoring.py`) expects these columns for:
- Filtering jobs by retailer
- Calculating average job duration
- Generating retailer-specific health metrics

## Usage in Code

When creating new scrape jobs, include the retailer_code:

```python
from app.models.product import ScrapeJob

job = ScrapeJob(
    job_type="product",
    status="pending",
    retailer_code="HP",  # or "TWD", "GH", "DH", "BT", "MH"
    target_url="https://example.com/category"
)

# When saving to Supabase
job_data = job.to_supabase_dict()
# duration_seconds will be calculated automatically when job completes
```

## Monitoring Endpoints

After migration, these endpoints will work correctly:

- `GET /api/v1/monitoring/health` - Overall system health metrics
- `GET /api/v1/monitoring/retailers` - Per-retailer health status
- `GET /api/v1/monitoring/metrics` - Hourly job metrics
- `GET /api/v1/monitoring/alerts` - Active system alerts

## Troubleshooting

If you still see errors after migration:

1. **Clear any cached connections** - Restart your API server
2. **Check RLS policies** - Ensure the new columns are accessible:
   ```sql
   -- If using RLS, you may need to update policies
   DROP POLICY IF EXISTS "Authenticated users can manage scrape jobs" ON scrape_jobs;
   CREATE POLICY "Authenticated users can manage scrape jobs" ON scrape_jobs
       FOR ALL USING (auth.role() = 'authenticated');
   ```

3. **Verify data types match** - The monitoring router expects:
   - `retailer_code`: string (max 5 chars)
   - `duration_seconds`: number (integer)

## Future Considerations

Consider implementing:
- Automatic retailer_code assignment based on target_url domain
- Background job to calculate missing duration_seconds for historical data
- Alerts for jobs with unusually long duration_seconds