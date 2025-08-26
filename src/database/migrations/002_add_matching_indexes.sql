-- Migration: Add performance indexes for matching tables
-- Purpose: Optimize query performance for common matching operations
-- Author: Claude Code Migration System
-- Date: 2025-08-25

-- Indexes for matching_results table
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

-- Compound index for finding high-confidence matches
CREATE INDEX IF NOT EXISTS idx_matching_results_high_confidence 
    ON matching_results(source_product_id, confidence_score DESC) 
    WHERE confidence_score >= 0.8 AND status != 'rejected';

-- Indexes for matching_metadata table
CREATE INDEX IF NOT EXISTS idx_matching_metadata_result_id 
    ON matching_metadata(matching_result_id);

CREATE INDEX IF NOT EXISTS idx_matching_metadata_key 
    ON matching_metadata(metadata_key);

-- GIN index for JSONB metadata searching
CREATE INDEX IF NOT EXISTS idx_matching_metadata_value_gin 
    ON matching_metadata USING GIN (metadata_value);

-- Partial index for specific metadata keys
CREATE INDEX IF NOT EXISTS idx_matching_metadata_algorithm_info 
    ON matching_metadata(matching_result_id, (metadata_value->>'algorithm')) 
    WHERE metadata_key = 'algorithm_info';

-- Add performance statistics
COMMENT ON INDEX idx_matching_results_source_product IS 'Primary lookup index for finding matches by source product';
COMMENT ON INDEX idx_matching_results_confidence_status IS 'Compound index for high-confidence match queries';
COMMENT ON INDEX idx_matching_metadata_value_gin IS 'GIN index for flexible JSON metadata searches';