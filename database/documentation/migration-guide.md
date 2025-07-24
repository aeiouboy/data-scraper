# Database Migration Guide

This guide provides detailed instructions for managing database migrations in the RIS Data Scrap project.

## Migration Overview

Database migrations are organized chronologically in numbered directories. Each migration represents a specific set of database changes that can be applied and, where possible, rolled back.

## Migration Directory Structure

```
migrations/
├── 001_initial_schema/           # Initial database setup
├── 002_multi_retailer/           # Multi-retailer support
├── 003_adaptive_scraping/        # Adaptive scraping features
├── 004_scrape_jobs/              # Scrape jobs enhancements
├── 005_monitoring/               # Monitoring schedules
├── 006_brand_aliases/            # Brand aliases system
├── 007_match_groups/             # Product match groups
└── 008_performance_optimizations/ # Performance improvements
```

## Running Migrations

### Prerequisites

1. **Supabase Access**: Ensure you have access to Supabase SQL editor
2. **Service Role Key**: Required for schema modifications
3. **Database Backup**: Always backup before running migrations
4. **Testing Environment**: Test migrations on development environment first

### Step-by-Step Migration Process

#### 1. Backup Current Database
```sql
-- Create backup (run in Supabase SQL editor)
-- Note: Supabase handles backups automatically, but verify backup exists
SELECT 'Backup verification - Current timestamp: ' || NOW();
```

#### 2. Run Migrations in Order

**Migration 001: Initial Schema**
```bash
# Location: database/migrations/001_initial_schema/initial_schema.sql
# Purpose: Creates core database structure
# Dependencies: None
```

**Migration 002: Multi-Retailer Support**
```bash
# Location: database/migrations/002_multi_retailer/
# Files:
#   - multi_retailer_schema.sql (full implementation)
#   - multi_retailer_schema_safe.sql (safe version)
# Dependencies: 001_initial_schema
```

**Migration 003: Adaptive Scraping**
```bash
# Location: database/migrations/003_adaptive_scraping/adaptive_scraping_schema.sql
# Purpose: Implements adaptive scraping features
# Dependencies: 002_multi_retailer
```

**Migration 004: Scrape Jobs Enhancement**
```bash
# Location: database/migrations/004_scrape_jobs/add_missing_columns.sql
# Purpose: Adds retailer_code and duration_seconds columns
# Dependencies: 003_adaptive_scraping
```

**Migration 005: Monitoring Schedules**
```bash
# Location: database/migrations/005_monitoring/monitoring_schedules_table.sql
# Purpose: Creates monitoring schedules table
# Dependencies: 004_scrape_jobs
```

**Migration 006: Brand Aliases**
```bash
# Location: database/migrations/006_brand_aliases/brand_aliases_table.sql
# Purpose: Implements brand aliases system
# Dependencies: 005_monitoring
```

**Migration 007: Match Groups**
```bash
# Location: database/migrations/007_match_groups/match_groups_schema.sql
# Purpose: Creates product match groups
# Dependencies: 006_brand_aliases
```

**Migration 008: Performance Optimizations**
```bash
# Location: database/migrations/008_performance_optimizations/price_comparisons_optimization.sql
# Purpose: Applies performance improvements
# Dependencies: 007_match_groups
```

#### 3. Apply Performance Indexes
```bash
# Location: database/indexes/performance/general_indexes.sql
# Purpose: Core performance indexes
# Run after: All migrations completed
```

### Migration Commands

#### In Supabase SQL Editor

1. **Open SQL Editor** in your Supabase dashboard
2. **Copy migration file contents** to editor
3. **Execute** the SQL commands
4. **Verify** migration success using validation queries

#### Using psql (if direct access available)

```bash
# Connect to database
psql "postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/[DATABASE]"

# Run migration file
\i /path/to/migration/file.sql

# Verify migration
\dt  # List tables
\d table_name  # Describe specific table
```

## Migration Validation

### After Each Migration

1. **Check Tables Created**:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;
```

2. **Verify Columns Added**:
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'your_table_name'
ORDER BY ordinal_position;
```

3. **Test Basic Operations**:
```sql
-- Insert test record
INSERT INTO categories (name, name_en) VALUES ('Test Category', 'Test Category');

-- Verify insert
SELECT * FROM categories WHERE name = 'Test Category';

-- Cleanup test
DELETE FROM categories WHERE name = 'Test Category';
```

## Rollback Procedures

### Safe Rollback Guidelines

1. **Migration 001**: Cannot rollback (drops entire schema)
2. **Migration 002-007**: Can rollback table creations with DROP statements
3. **Migration 008**: Can rollback index creations with DROP INDEX statements

### Rollback Examples

**Rollback Column Additions** (Migration 004):
```sql
-- Remove added columns
ALTER TABLE scrape_jobs DROP COLUMN IF EXISTS retailer_code;
ALTER TABLE scrape_jobs DROP COLUMN IF EXISTS duration_seconds;

-- Remove indexes
DROP INDEX IF EXISTS idx_scrape_jobs_retailer_code;
DROP INDEX IF EXISTS idx_scrape_jobs_retailer_created;
```

**Rollback Table Creations**:
```sql
-- Remove created tables (be careful with dependencies)
DROP TABLE IF EXISTS monitoring_schedules CASCADE;
DROP TABLE IF EXISTS brand_aliases CASCADE;
```

## Troubleshooting

### Common Issues

**Permission Denied**:
- Ensure using service role key, not anon key
- Verify Supabase project permissions

**Table Already Exists**:
- Check if migration was already applied
- Use `IF NOT EXISTS` in CREATE statements

**Foreign Key Violations**:
- Ensure dependent tables exist
- Check data integrity before migration

**Index Creation Failures**:
- Verify table exists first
- Check for duplicate index names

### Error Recovery

1. **Check Migration Status**:
```sql
-- Check what tables exist
\dt

-- Check specific table structure
\d table_name

-- Check for partial migrations
SELECT * FROM information_schema.tables WHERE table_name LIKE 'your_prefix%';
```

2. **Manual Cleanup**:
```sql
-- Drop problematic objects
DROP TABLE IF EXISTS problematic_table CASCADE;
DROP INDEX IF EXISTS problematic_index;
```

3. **Retry Migration**:
- Fix issues in migration file
- Re-run corrected migration

## Best Practices

### Before Migration
- [ ] Backup database
- [ ] Test on development environment
- [ ] Review migration files for syntax errors
- [ ] Verify dependencies are met

### During Migration
- [ ] Run migrations in correct order
- [ ] Monitor for errors
- [ ] Validate each step
- [ ] Document any issues

### After Migration
- [ ] Run full validation tests
- [ ] Update application code if needed
- [ ] Monitor application performance
- [ ] Document migration completion

## Migration Log Template

Use this template to document migration execution:

```
Migration: [Migration Number and Name]
Date: [YYYY-MM-DD]
Executed by: [Name]
Environment: [Development/Staging/Production]

Pre-migration checks:
- [ ] Database backed up
- [ ] Dependencies verified
- [ ] Syntax validated

Execution:
- Start time: [HH:MM:SS]
- End time: [HH:MM:SS]
- Status: [Success/Failed]
- Errors: [Any errors encountered]

Post-migration validation:
- [ ] Tables created/modified as expected
- [ ] Indexes applied successfully
- [ ] Data integrity maintained
- [ ] Application functionality verified

Notes: [Any additional notes or observations]
```

---
*For support with database migrations, consult the main database documentation or project maintainers.*