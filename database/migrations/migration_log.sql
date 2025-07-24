-- Migration tracking system
-- This table tracks which migrations have been applied to the database

CREATE TABLE IF NOT EXISTS migration_log (
    id SERIAL PRIMARY KEY,
    migration_number TEXT NOT NULL UNIQUE,
    migration_name TEXT NOT NULL,
    description TEXT,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    applied_by TEXT DEFAULT current_user,
    execution_time_seconds INTEGER,
    status TEXT DEFAULT 'completed' CHECK (status IN ('completed', 'failed', 'rolled_back')),
    rollback_script TEXT,
    notes TEXT
);

-- Create index for quick lookups
CREATE INDEX IF NOT EXISTS idx_migration_log_migration_number ON migration_log(migration_number);
CREATE INDEX IF NOT EXISTS idx_migration_log_applied_at ON migration_log(applied_at DESC);

-- Insert initial migration records (if running this on existing database)
-- Comment out these inserts if running on a fresh database

INSERT INTO migration_log (migration_number, migration_name, description, notes) 
VALUES 
    ('001', 'initial_schema', 'Initial database schema creation', 'Creates core tables: categories, products, retailers, scrape_jobs, price_history'),
    ('002', 'multi_retailer', 'Multi-retailer support enhancement', 'Enhances schema for multiple retailer support'),
    ('003', 'adaptive_scraping', 'Adaptive scraping features', 'Adds adaptive scraping capabilities and related tables'),
    ('004', 'scrape_jobs', 'Scrape jobs enhancements', 'Adds retailer_code and duration_seconds columns to scrape_jobs'),
    ('005', 'monitoring', 'Monitoring schedules', 'Creates monitoring_schedules table for automated scraping'),
    ('006', 'brand_aliases', 'Brand aliases system', 'Implements brand aliases for improved product matching'),
    ('007', 'match_groups', 'Product match groups', 'Creates match_groups and related product matching tables'),
    ('008', 'performance_optimizations', 'Performance optimizations', 'Applies performance indexes and optimizations')
ON CONFLICT (migration_number) DO NOTHING;

-- Function to check if a migration has been applied
CREATE OR REPLACE FUNCTION migration_applied(migration_num TEXT)
RETURNS BOOLEAN
LANGUAGE SQL
AS $$
    SELECT EXISTS (
        SELECT 1 FROM migration_log 
        WHERE migration_number = migration_num 
        AND status = 'completed'
    );
$$;

-- Function to record a migration
CREATE OR REPLACE FUNCTION record_migration(
    migration_num TEXT,
    migration_name TEXT,
    description TEXT DEFAULT NULL,
    execution_seconds INTEGER DEFAULT NULL,
    notes TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE SQL
AS $$
    INSERT INTO migration_log (
        migration_number, 
        migration_name, 
        description, 
        execution_time_seconds, 
        notes
    ) VALUES (
        migration_num, 
        migration_name, 
        description, 
        execution_seconds, 
        notes
    )
    ON CONFLICT (migration_number) DO UPDATE SET
        applied_at = NOW(),
        applied_by = current_user,
        execution_time_seconds = EXCLUDED.execution_time_seconds,
        notes = EXCLUDED.notes,
        status = 'completed';
$$;

-- Function to mark a migration as failed
CREATE OR REPLACE FUNCTION mark_migration_failed(
    migration_num TEXT,
    error_message TEXT
)
RETURNS VOID  
LANGUAGE SQL
AS $$
    INSERT INTO migration_log (migration_number, migration_name, status, notes)
    VALUES (migration_num, 'FAILED', 'failed', error_message)
    ON CONFLICT (migration_number) DO UPDATE SET
        status = 'failed',
        notes = EXCLUDED.notes,
        applied_at = NOW();
$$;

-- View to show migration status
CREATE OR REPLACE VIEW migration_status AS
SELECT 
    migration_number,
    migration_name,
    description,
    status,
    applied_at,
    applied_by,
    execution_time_seconds,
    CASE 
        WHEN execution_time_seconds IS NOT NULL 
        THEN execution_time_seconds || ' seconds'
        ELSE 'N/A'
    END as execution_time,
    notes
FROM migration_log
ORDER BY migration_number;

-- Validation query to check current migration state
SELECT 'Migration tracking system initialized successfully!' as message;
SELECT * FROM migration_status;