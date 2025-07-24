-- Master migration runner script
-- This script runs all migrations in the correct order
-- Run this in Supabase SQL editor or psql

-- Enable timing and verbose output
\timing on
\echo 'Starting RIS Data Scrap database migration process...'

-- Check if we're running on the correct database
DO $$
BEGIN
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'User: %', current_user;
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

-- Initialize migration tracking (run this first)
\echo 'Initializing migration tracking system...'
-- Uncomment the line below when ready to run
-- \i migration_log.sql

-- Migration 001: Initial Schema
\echo 'Running Migration 001: Initial Schema...'
DO $$
BEGIN
    IF NOT migration_applied('001') THEN
        RAISE NOTICE 'Applying migration 001: Initial Schema';
        -- Uncomment the line below when ready to run
        -- \i 001_initial_schema/initial_schema.sql
        PERFORM record_migration('001', 'initial_schema', 'Initial database schema creation');
        RAISE NOTICE 'Migration 001 completed successfully';
    ELSE
        RAISE NOTICE 'Migration 001 already applied, skipping';
    END IF;
END $$;

-- Migration 002: Multi-Retailer Support
\echo 'Running Migration 002: Multi-Retailer Support...'
DO $$
BEGIN
    IF NOT migration_applied('002') THEN
        RAISE NOTICE 'Applying migration 002: Multi-Retailer Support';
        -- Check dependencies
        IF NOT migration_applied('001') THEN
            RAISE EXCEPTION 'Migration 002 requires migration 001 to be applied first';
        END IF;
        -- Uncomment the lines below when ready to run
        -- \i 002_multi_retailer/multi_retailer_schema.sql
        -- Alternative safe version: \i 002_multi_retailer/multi_retailer_schema_safe.sql
        PERFORM record_migration('002', 'multi_retailer', 'Multi-retailer support enhancement');
        RAISE NOTICE 'Migration 002 completed successfully';
    ELSE
        RAISE NOTICE 'Migration 002 already applied, skipping';
    END IF;
END $$;

-- Migration 003: Adaptive Scraping
\echo 'Running Migration 003: Adaptive Scraping...'
DO $$
BEGIN
    IF NOT migration_applied('003') THEN
        RAISE NOTICE 'Applying migration 003: Adaptive Scraping';
        -- Check dependencies  
        IF NOT (migration_applied('001') AND migration_applied('002')) THEN
            RAISE EXCEPTION 'Migration 003 requires migrations 001 and 002 to be applied first';
        END IF;
        -- Uncomment the line below when ready to run
        -- \i 003_adaptive_scraping/adaptive_scraping_schema.sql
        PERFORM record_migration('003', 'adaptive_scraping', 'Adaptive scraping features');
        RAISE NOTICE 'Migration 003 completed successfully';
    ELSE
        RAISE NOTICE 'Migration 003 already applied, skipping';
    END IF;
END $$;

-- Migration 004: Scrape Jobs Enhancement
\echo 'Running Migration 004: Scrape Jobs Enhancement...'
DO $$
BEGIN
    IF NOT migration_applied('004') THEN
        RAISE NOTICE 'Applying migration 004: Scrape Jobs Enhancement';
        -- Check dependencies
        IF NOT (migration_applied('001') AND migration_applied('002') AND migration_applied('003')) THEN
            RAISE EXCEPTION 'Migration 004 requires migrations 001-003 to be applied first';
        END IF;
        -- Uncomment the line below when ready to run
        -- \i 004_scrape_jobs/add_missing_columns.sql
        PERFORM record_migration('004', 'scrape_jobs', 'Scrape jobs enhancements');
        RAISE NOTICE 'Migration 004 completed successfully';
    ELSE
        RAISE NOTICE 'Migration 004 already applied, skipping';
    END IF;
END $$;

-- Migration 005: Monitoring Schedules
\echo 'Running Migration 005: Monitoring Schedules...'
DO $$
BEGIN
    IF NOT migration_applied('005') THEN
        RAISE NOTICE 'Applying migration 005: Monitoring Schedules';
        -- Check dependencies
        IF NOT (migration_applied('001') AND migration_applied('002') AND migration_applied('003') AND migration_applied('004')) THEN
            RAISE EXCEPTION 'Migration 005 requires migrations 001-004 to be applied first';
        END IF;
        -- Uncomment the line below when ready to run
        -- \i 005_monitoring/monitoring_schedules_table.sql
        PERFORM record_migration('005', 'monitoring', 'Monitoring schedules');
        RAISE NOTICE 'Migration 005 completed successfully';
    ELSE
        RAISE NOTICE 'Migration 005 already applied, skipping';
    END IF;
END $$;

-- Migration 006: Brand Aliases
\echo 'Running Migration 006: Brand Aliases...'
DO $$
BEGIN
    IF NOT migration_applied('006') THEN
        RAISE NOTICE 'Applying migration 006: Brand Aliases';
        -- Uncomment the line below when ready to run
        -- \i 006_brand_aliases/brand_aliases_table.sql
        PERFORM record_migration('006', 'brand_aliases', 'Brand aliases system');
        RAISE NOTICE 'Migration 006 completed successfully';
    ELSE
        RAISE NOTICE 'Migration 006 already applied, skipping';
    END IF;
END $$;

-- Migration 007: Match Groups
\echo 'Running Migration 007: Match Groups...'
DO $$
BEGIN
    IF NOT migration_applied('007') THEN
        RAISE NOTICE 'Applying migration 007: Match Groups';
        -- Check dependencies (brand aliases recommended but not required)
        -- Uncomment the line below when ready to run
        -- \i 007_match_groups/match_groups_schema.sql
        PERFORM record_migration('007', 'match_groups', 'Product match groups');
        RAISE NOTICE 'Migration 007 completed successfully';
    ELSE
        RAISE NOTICE 'Migration 007 already applied, skipping';
    END IF;
END $$;

-- Migration 008: Performance Optimizations
\echo 'Running Migration 008: Performance Optimizations...'
DO $$
BEGIN
    IF NOT migration_applied('008') THEN
        RAISE NOTICE 'Applying migration 008: Performance Optimizations';
        -- This migration should run after all data is populated
        -- Uncomment the line below when ready to run
        -- \i 008_performance_optimizations/price_comparisons_optimization.sql
        PERFORM record_migration('008', 'performance_optimizations', 'Performance optimizations');
        RAISE NOTICE 'Migration 008 completed successfully';
    ELSE
        RAISE NOTICE 'Migration 008 already applied, skipping';
    END IF;
END $$;

-- Apply Performance Indexes
\echo 'Applying performance indexes...'
DO $$
BEGIN
    RAISE NOTICE 'Creating performance indexes';
    -- Uncomment the line below when ready to run
    -- \i ../indexes/performance/general_indexes.sql
    RAISE NOTICE 'Performance indexes created successfully';
END $$;

-- Final validation
\echo 'Running final validation...'
DO $$
DECLARE
    migration_count INTEGER;
    expected_count INTEGER := 8;
BEGIN
    SELECT COUNT(*) INTO migration_count 
    FROM migration_log 
    WHERE status = 'completed';
    
    RAISE NOTICE 'Applied migrations: % / %', migration_count, expected_count;
    
    IF migration_count = expected_count THEN
        RAISE NOTICE '✅ All migrations completed successfully!';
    ELSE
        RAISE WARNING '⚠️  Some migrations may not have been applied';
    END IF;
    
    -- Show migration status
    RAISE NOTICE 'Migration Status Summary:';
END $$;

-- Display final status
SELECT * FROM migration_status;

\echo 'Migration process completed. Check the output above for any errors.'
\echo 'If all migrations show as completed, your database is up to date.'

-- Uncomment below to show basic table info
-- \dt
-- \d products
-- \d product_matches