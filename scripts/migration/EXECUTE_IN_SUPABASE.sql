-- ===============================================
-- SUPABASE MIGRATION SCRIPT
-- ===============================================
-- Execute this script in Supabase SQL Editor
-- Dashboard > SQL Editor > New Query > Paste this script
-- Date: 2025-08-25
-- ===============================================

-- Step 1: Create matching_results table
-- ===============================================
CREATE TABLE IF NOT EXISTS matching_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    matched_product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    matching_method VARCHAR(20) NOT NULL CHECK (matching_method IN ('name', 'sku', 'brand', 'specifications', 'hybrid')),
    status VARCHAR(10) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'rejected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_product_id, matched_product_id)
);

-- Step 2: Create matching_metadata table
-- ===============================================
CREATE TABLE IF NOT EXISTS matching_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matching_result_id UUID NOT NULL REFERENCES matching_results(id) ON DELETE CASCADE,
    metadata_key VARCHAR(100) NOT NULL,
    metadata_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 3: Create trigger function for updated_at
-- ===============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 4: Create trigger for matching_results
-- ===============================================
CREATE TRIGGER update_matching_results_updated_at 
    BEFORE UPDATE ON matching_results 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Step 5: Create performance indexes
-- ===============================================
CREATE INDEX IF NOT EXISTS idx_matching_results_source_product 
    ON matching_results(source_product_id);

CREATE INDEX IF NOT EXISTS idx_matching_results_matched_product 
    ON matching_results(matched_product_id);

CREATE INDEX IF NOT EXISTS idx_matching_results_confidence_status 
    ON matching_results(confidence_score DESC, status);

CREATE INDEX IF NOT EXISTS idx_matching_results_method_status 
    ON matching_results(matching_method, status);

CREATE INDEX IF NOT EXISTS idx_matching_results_created_at 
    ON matching_results(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_matching_results_status 
    ON matching_results(status) WHERE status != 'rejected';

CREATE INDEX IF NOT EXISTS idx_matching_results_high_confidence 
    ON matching_results(source_product_id, confidence_score DESC) 
    WHERE confidence_score >= 0.8 AND status != 'rejected';

-- Metadata table indexes
CREATE INDEX IF NOT EXISTS idx_matching_metadata_result_id 
    ON matching_metadata(matching_result_id);

CREATE INDEX IF NOT EXISTS idx_matching_metadata_key 
    ON matching_metadata(metadata_key);

CREATE INDEX IF NOT EXISTS idx_matching_metadata_value_gin 
    ON matching_metadata USING GIN (metadata_value);

CREATE INDEX IF NOT EXISTS idx_matching_metadata_algorithm_info 
    ON matching_metadata(matching_result_id, (metadata_value->>'algorithm')) 
    WHERE metadata_key = 'algorithm_info';

-- Step 6: Create statistics functions
-- ===============================================
CREATE OR REPLACE FUNCTION get_match_status_counts()
RETURNS TABLE(status VARCHAR(10), count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mr.status,
        COUNT(*) as count
    FROM matching_results mr
    GROUP BY mr.status;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_match_method_counts()
RETURNS TABLE(method VARCHAR(20), count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mr.matching_method as method,
        COUNT(*) as count
    FROM matching_results mr
    GROUP BY mr.matching_method;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_average_confidence()
RETURNS TABLE(avg DECIMAL(5,3)) AS $$
BEGIN
    RETURN QUERY
    SELECT COALESCE(AVG(confidence_score), 0.0)::DECIMAL(5,3) as avg
    FROM matching_results
    WHERE status != 'rejected';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_match_quality_metrics()
RETURNS TABLE(
    total_matches BIGINT,
    high_confidence_count BIGINT,
    medium_confidence_count BIGINT,
    low_confidence_count BIGINT,
    avg_confidence DECIMAL(5,3),
    confirmed_percentage DECIMAL(5,2),
    rejected_percentage DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_matches,
        COUNT(*) FILTER (WHERE confidence_score >= 0.8) as high_confidence_count,
        COUNT(*) FILTER (WHERE confidence_score >= 0.6 AND confidence_score < 0.8) as medium_confidence_count,
        COUNT(*) FILTER (WHERE confidence_score < 0.6) as low_confidence_count,
        COALESCE(AVG(confidence_score), 0.0)::DECIMAL(5,3) as avg_confidence,
        COALESCE(
            (COUNT(*) FILTER (WHERE status = 'confirmed') * 100.0 / COUNT(*)), 0.0
        )::DECIMAL(5,2) as confirmed_percentage,
        COALESCE(
            (COUNT(*) FILTER (WHERE status = 'rejected') * 100.0 / COUNT(*)), 0.0
        )::DECIMAL(5,2) as rejected_percentage
    FROM matching_results;
END;
$$ LANGUAGE plpgsql;

-- Step 7: Create utility functions
-- ===============================================
CREATE OR REPLACE FUNCTION cleanup_old_rejected_matches(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
    cutoff_date TIMESTAMP;
BEGIN
    cutoff_date := NOW() - (days_to_keep || ' days')::INTERVAL;
    
    DELETE FROM matching_results
    WHERE status = 'rejected' 
      AND created_at < cutoff_date;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION find_matching_candidates(
    source_product_uuid UUID,
    min_confidence DECIMAL(3,2) DEFAULT 0.5,
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    candidate_id UUID,
    candidate_name TEXT,
    candidate_brand TEXT,
    candidate_retailer TEXT,
    existing_confidence DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        p.id as candidate_id,
        p.name as candidate_name,
        p.brand as candidate_brand,
        p.retailer_code as candidate_retailer,
        COALESCE(mr.confidence_score, 0.0) as existing_confidence
    FROM products p
    LEFT JOIN matching_results mr ON (
        mr.source_product_id = source_product_uuid AND mr.matched_product_id = p.id
    )
    WHERE p.id != source_product_uuid
      AND p.retailer_code != (
          SELECT retailer_code FROM products WHERE id = source_product_uuid
      )
      AND (mr.confidence_score IS NULL OR mr.confidence_score >= min_confidence)
    ORDER BY existing_confidence DESC, p.name
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION validate_matching_integrity()
RETURNS TABLE(
    issue_type TEXT,
    issue_count BIGINT,
    description TEXT
) AS $$
BEGIN
    -- Check for self-references
    RETURN QUERY
    SELECT 
        'self_reference' as issue_type,
        COUNT(*) as issue_count,
        'Matches where source and target are the same product' as description
    FROM matching_results
    WHERE source_product_id = matched_product_id;
    
    -- Check for missing products
    RETURN QUERY
    SELECT 
        'missing_source_product' as issue_type,
        COUNT(*) as issue_count,
        'Matches with non-existent source products' as description
    FROM matching_results mr
    LEFT JOIN products p ON mr.source_product_id = p.id
    WHERE p.id IS NULL;
    
    RETURN QUERY
    SELECT 
        'missing_target_product' as issue_type,
        COUNT(*) as issue_count,
        'Matches with non-existent target products' as description
    FROM matching_results mr
    LEFT JOIN products p ON mr.matched_product_id = p.id
    WHERE p.id IS NULL;
    
    -- Check for same-retailer matches
    RETURN QUERY
    SELECT 
        'same_retailer_match' as issue_type,
        COUNT(*) as issue_count,
        'Matches between products from the same retailer' as description
    FROM matching_results mr
    JOIN products p1 ON mr.source_product_id = p1.id
    JOIN products p2 ON mr.matched_product_id = p2.id
    WHERE p1.retailer_code = p2.retailer_code;
    
    -- Check for orphaned metadata
    RETURN QUERY
    SELECT 
        'orphaned_metadata' as issue_type,
        COUNT(*) as issue_count,
        'Metadata entries without corresponding match results' as description
    FROM matching_metadata mm
    LEFT JOIN matching_results mr ON mm.matching_result_id = mr.id
    WHERE mr.id IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Step 8: Create analytics view
-- ===============================================
CREATE OR REPLACE VIEW match_analytics_view AS
SELECT 
    mr.id,
    mr.source_product_id,
    mr.matched_product_id,
    mr.confidence_score,
    mr.matching_method,
    mr.status,
    mr.created_at,
    mr.updated_at,
    p1.name as source_product_name,
    p1.brand as source_product_brand,
    p1.retailer_code as source_retailer,
    p1.category as source_category,
    p1.price as source_price,
    p2.name as matched_product_name,
    p2.brand as matched_product_brand,
    p2.retailer_code as matched_retailer,
    p2.category as matched_category,
    p2.price as matched_price,
    ABS(COALESCE(p1.price, 0) - COALESCE(p2.price, 0)) as price_difference,
    CASE 
        WHEN p1.category = p2.category THEN true 
        ELSE false 
    END as same_category,
    CASE 
        WHEN LOWER(p1.brand) = LOWER(p2.brand) THEN true 
        ELSE false 
    END as same_brand
FROM matching_results mr
JOIN products p1 ON mr.source_product_id = p1.id
JOIN products p2 ON mr.matched_product_id = p2.id;

-- Step 9: Add comments for documentation
-- ===============================================
COMMENT ON TABLE matching_results IS 'Stores product matching relationships with confidence scores';
COMMENT ON TABLE matching_metadata IS 'Stores additional metadata for matching results (algorithms, scores, debug info)';
COMMENT ON VIEW match_analytics_view IS 'Comprehensive view for match analytics with product details';

-- Step 10: Test the migration
-- ===============================================
-- Verify tables exist
SELECT 'matching_results' as table_name, count(*) as row_count FROM matching_results
UNION ALL
SELECT 'matching_metadata' as table_name, count(*) as row_count FROM matching_metadata;

-- Test functions
SELECT * FROM get_match_quality_metrics();

-- ===============================================
-- MIGRATION COMPLETE!
-- ===============================================
-- Tables created: matching_results, matching_metadata
-- Functions created: 6 utility functions
-- Indexes created: 11 performance indexes
-- Views created: match_analytics_view
-- 
-- Next steps after executing this script:
-- 1. Verify tables exist (query above should show results)
-- 2. Run data export: python scripts/migration/01_export_brave_matches.py
-- 3. Import data: python scripts/migration/03_import_to_database.py
-- ===============================================