-- Migration: Create database functions and migrate Brave API data
-- Purpose: Add helper functions and prepare for data migration
-- Author: Claude Code Migration System
-- Date: 2025-08-25

-- Create helper functions for match statistics
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

-- Function to find duplicate matches (same products, different confidence)
CREATE OR REPLACE FUNCTION find_duplicate_matches()
RETURNS TABLE(
    source_product_id UUID,
    matched_product_id UUID,
    match_count BIGINT,
    confidence_scores DECIMAL(3,2)[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mr.source_product_id,
        mr.matched_product_id,
        COUNT(*) as match_count,
        ARRAY_AGG(mr.confidence_score ORDER BY mr.confidence_score DESC) as confidence_scores
    FROM matching_results mr
    GROUP BY mr.source_product_id, mr.matched_product_id
    HAVING COUNT(*) > 1;
END;
$$ LANGUAGE plpgsql;

-- Function to get match quality metrics
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

-- Function to cleanup old rejected matches
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

-- Function to find potential matching candidates for a product
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

-- Function to validate matching results integrity
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

-- Create view for match analytics
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

-- Create index on the view for performance
CREATE INDEX IF NOT EXISTS idx_match_analytics_source_retailer 
    ON matching_results(source_product_id, (
        SELECT retailer_code FROM products WHERE id = source_product_id
    ));

-- Add comments for documentation
COMMENT ON FUNCTION get_match_status_counts() IS 'Returns count of matches by status';
COMMENT ON FUNCTION get_match_method_counts() IS 'Returns count of matches by matching method';
COMMENT ON FUNCTION get_average_confidence() IS 'Returns average confidence score excluding rejected matches';
COMMENT ON FUNCTION find_duplicate_matches() IS 'Finds duplicate matches between same products';
COMMENT ON FUNCTION get_match_quality_metrics() IS 'Returns comprehensive match quality metrics';
COMMENT ON FUNCTION cleanup_old_rejected_matches(INTEGER) IS 'Cleans up rejected matches older than specified days';
COMMENT ON FUNCTION find_matching_candidates(UUID, DECIMAL, INTEGER) IS 'Finds potential matching candidates for a product';
COMMENT ON FUNCTION validate_matching_integrity() IS 'Validates integrity of matching results and reports issues';
COMMENT ON VIEW match_analytics_view IS 'Comprehensive view for match analytics with product details';