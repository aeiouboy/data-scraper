-- Rollback migration script
-- This script provides rollback procedures for each migration
-- CAUTION: Rollbacks may result in data loss. Always backup first!

-- Enable timing and verbose output
\timing on
\echo 'RIS Data Scrap Database Rollback Procedures'
\echo 'CAUTION: This may result in data loss. Ensure you have backups!'

-- Helper function to mark migration as rolled back
CREATE OR REPLACE FUNCTION mark_migration_rolled_back(
    migration_num TEXT,
    rollback_notes TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE SQL
AS $$
    UPDATE migration_log 
    SET 
        status = 'rolled_back',
        notes = COALESCE(rollback_notes, notes),
        applied_at = NOW()
    WHERE migration_number = migration_num;
$$;

-- Rollback Migration 008: Performance Optimizations
\echo 'Rollback available for Migration 008: Performance Optimizations'
CREATE OR REPLACE FUNCTION rollback_migration_008()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE NOTICE 'Rolling back Migration 008: Performance Optimizations';
    
    -- Drop performance optimization indexes and views
    DROP INDEX IF EXISTS idx_product_matches_unified_category;
    DROP INDEX IF EXISTS idx_product_matches_price_range_max;
    DROP INDEX IF EXISTS idx_product_matches_price_variance_percentage;
    DROP INDEX IF EXISTS idx_product_matches_match_confidence;
    DROP INDEX IF EXISTS idx_product_matches_retailer_count;
    
    -- Drop any materialized views created by this migration
    DROP MATERIALIZED VIEW IF EXISTS mv_price_comparison_summary;
    DROP VIEW IF EXISTS v_top_savings_opportunities;
    
    PERFORM mark_migration_rolled_back('008', 'Performance optimizations rolled back');
    RAISE NOTICE 'Migration 008 rolled back successfully';
END $$;

-- Rollback Migration 007: Match Groups
\echo 'Rollback available for Migration 007: Match Groups'
CREATE OR REPLACE FUNCTION rollback_migration_007()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE NOTICE 'Rolling back Migration 007: Match Groups';
    
    -- Remove foreign key constraints first
    ALTER TABLE product_matches DROP CONSTRAINT IF EXISTS fk_product_matches_match_group;
    
    -- Drop tables created in this migration
    DROP TABLE IF EXISTS match_groups CASCADE;
    
    -- Remove match_group_id column from product_matches if it was added
    ALTER TABLE product_matches DROP COLUMN IF EXISTS match_group_id;
    
    PERFORM mark_migration_rolled_back('007', 'Match groups schema rolled back');
    RAISE NOTICE 'Migration 007 rolled back successfully';
END $$;

-- Rollback Migration 006: Brand Aliases
\echo 'Rollback available for Migration 006: Brand Aliases'
CREATE OR REPLACE FUNCTION rollback_migration_006()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE NOTICE 'Rolling back Migration 006: Brand Aliases';
    
    -- Drop brand aliases table
    DROP TABLE IF EXISTS brand_aliases CASCADE;
    
    PERFORM mark_migration_rolled_back('006', 'Brand aliases table dropped');
    RAISE NOTICE 'Migration 006 rolled back successfully';
END $$;

-- Rollback Migration 005: Monitoring Schedules
\echo 'Rollback available for Migration 005: Monitoring Schedules'
CREATE OR REPLACE FUNCTION rollback_migration_005()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE NOTICE 'Rolling back Migration 005: Monitoring Schedules';
    
    -- Drop monitoring schedules table
    DROP TABLE IF EXISTS monitoring_schedules CASCADE;
    
    PERFORM mark_migration_rolled_back('005', 'Monitoring schedules table dropped');
    RAISE NOTICE 'Migration 005 rolled back successfully';
END $$;

-- Rollback Migration 004: Scrape Jobs Enhancement
\echo 'Rollback available for Migration 004: Scrape Jobs Enhancement'
CREATE OR REPLACE FUNCTION rollback_migration_004()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE NOTICE 'Rolling back Migration 004: Scrape Jobs Enhancement';
    
    -- Drop constraints added by this migration
    ALTER TABLE scrape_jobs DROP CONSTRAINT IF EXISTS check_duration_positive;
    
    -- Drop indexes added by this migration
    DROP INDEX IF EXISTS idx_scrape_jobs_retailer_code;
    DROP INDEX IF EXISTS idx_scrape_jobs_retailer_created;
    
    -- Remove columns added by this migration
    ALTER TABLE scrape_jobs DROP COLUMN IF EXISTS retailer_code;
    ALTER TABLE scrape_jobs DROP COLUMN IF EXISTS duration_seconds;
    
    PERFORM mark_migration_rolled_back('004', 'Scrape jobs enhancements rolled back');
    RAISE NOTICE 'Migration 004 rolled back successfully';
END $$;

-- Rollback Migration 003: Adaptive Scraping
\echo 'Rollback available for Migration 003: Adaptive Scraping'
CREATE OR REPLACE FUNCTION rollback_migration_003()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE NOTICE 'Rolling back Migration 003: Adaptive Scraping';
    
    -- This would need to drop adaptive scraping related tables/columns
    -- The exact rollback depends on what was created in migration 003
    -- Add specific rollback commands based on the actual migration content
    
    RAISE WARNING 'Rollback for migration 003 needs to be customized based on actual schema changes';
    PERFORM mark_migration_rolled_back('003', 'Adaptive scraping rollback - manual verification needed');
    RAISE NOTICE 'Migration 003 rollback prepared - manual verification recommended';
END $$;

-- Rollback Migration 002: Multi-Retailer Support
\echo 'Rollback available for Migration 002: Multi-Retailer Support'
CREATE OR REPLACE FUNCTION rollback_migration_002()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE NOTICE 'Rolling back Migration 002: Multi-Retailer Support';
    
    -- This would need to drop multi-retailer specific tables/columns
    -- The exact rollback depends on what was created in migration 002
    
    RAISE WARNING 'Rollback for migration 002 needs to be customized based on actual schema changes';
    PERFORM mark_migration_rolled_back('002', 'Multi-retailer rollback - manual verification needed');
    RAISE NOTICE 'Migration 002 rollback prepared - manual verification recommended';
END $$;

-- Migration 001 cannot be safely rolled back as it creates the core schema
\echo 'Migration 001 (Initial Schema) cannot be safely rolled back'
CREATE OR REPLACE FUNCTION rollback_migration_001()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Migration 001 (Initial Schema) cannot be rolled back as it would drop all core tables and data';
END $$;

-- Interactive rollback procedures
\echo 'Available rollback functions:'
\echo '  SELECT rollback_migration_008(); -- Roll back performance optimizations'
\echo '  SELECT rollback_migration_007(); -- Roll back match groups'
\echo '  SELECT rollback_migration_006(); -- Roll back brand aliases'
\echo '  SELECT rollback_migration_005(); -- Roll back monitoring schedules'
\echo '  SELECT rollback_migration_004(); -- Roll back scrape jobs enhancements'
\echo '  SELECT rollback_migration_003(); -- Roll back adaptive scraping (needs customization)'
\echo '  SELECT rollback_migration_002(); -- Roll back multi-retailer (needs customization)'
\echo ''
\echo 'To rollback multiple migrations in reverse order:'

CREATE OR REPLACE FUNCTION rollback_to_migration(target_migration TEXT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    current_migration TEXT;
BEGIN
    -- Get the highest applied migration
    SELECT migration_number INTO current_migration
    FROM migration_log 
    WHERE status = 'completed'
    ORDER BY migration_number DESC
    LIMIT 1;
    
    RAISE NOTICE 'Current highest migration: %', current_migration;
    RAISE NOTICE 'Target migration: %', target_migration;
    
    -- Roll back migrations in reverse order
    IF current_migration >= '008' AND target_migration < '008' THEN
        PERFORM rollback_migration_008();
    END IF;
    
    IF current_migration >= '007' AND target_migration < '007' THEN
        PERFORM rollback_migration_007();
    END IF;
    
    IF current_migration >= '006' AND target_migration < '006' THEN
        PERFORM rollback_migration_006();
    END IF;
    
    IF current_migration >= '005' AND target_migration < '005' THEN
        PERFORM rollback_migration_005();
    END IF;
    
    IF current_migration >= '004' AND target_migration < '004' THEN
        PERFORM rollback_migration_004();
    END IF;
    
    IF target_migration < '003' THEN
        RAISE WARNING 'Rollback to migration % requires manual intervention for migrations 001-003', target_migration;
    END IF;
    
    RAISE NOTICE 'Rollback to migration % completed', target_migration;
END $$;

-- Usage examples:
\echo ''
\echo 'Usage Examples:'
\echo '  -- Roll back to migration 005 (will rollback 006, 007, 008)'
\echo '  SELECT rollback_to_migration(''005'');'
\echo ''
\echo '  -- Roll back only the latest migration'
\echo '  SELECT rollback_migration_008();'
\echo ''
\echo '  -- View current migration status'
\echo '  SELECT * FROM migration_status;'
\echo ''

-- Safety checks
CREATE OR REPLACE FUNCTION check_rollback_safety()
RETURNS TABLE (
    table_name TEXT,
    row_count BIGINT,
    risk_level TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE NOTICE 'Checking rollback safety...';
    
    RETURN QUERY
    SELECT 
        t.table_name::TEXT,
        (
            SELECT reltuples::BIGINT 
            FROM pg_class 
            WHERE relname = t.table_name
        ) as row_count,
        CASE 
            WHEN (SELECT reltuples FROM pg_class WHERE relname = t.table_name) > 10000 THEN 'HIGH'
            WHEN (SELECT reltuples FROM pg_class WHERE relname = t.table_name) > 1000 THEN 'MEDIUM'
            ELSE 'LOW'
        END::TEXT as risk_level
    FROM information_schema.tables t
    WHERE t.table_schema = 'public' 
    AND t.table_type = 'BASE TABLE'
    ORDER BY row_count DESC;
END $$;

\echo 'Before performing any rollback, run: SELECT * FROM check_rollback_safety();'
\echo 'This will show you how much data might be affected.'

-- Final warning
\echo ''
\echo '⚠️  IMPORTANT SAFETY WARNINGS:'
\echo '1. Always backup your database before rollback operations'
\echo '2. Test rollbacks on a copy/staging environment first'  
\echo '3. Some rollbacks may cause data loss'
\echo '4. Rollbacks of migrations 001-003 require manual intervention'
\echo '5. Check application compatibility after rollbacks'
\echo ''