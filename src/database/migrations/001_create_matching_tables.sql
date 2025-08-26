-- Migration: Create matching results and metadata tables
-- Purpose: Store product matching relationships and metadata for database-driven matching
-- Author: Claude Code Migration System
-- Date: 2025-08-25

-- Create matching results table
CREATE TABLE IF NOT EXISTS matching_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    matched_product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    matching_method VARCHAR(20) NOT NULL CHECK (matching_method IN ('name', 'sku', 'brand', 'specifications', 'hybrid')),
    status VARCHAR(10) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'rejected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Prevent duplicate matches between same products
    UNIQUE(source_product_id, matched_product_id)
);

-- Create matching metadata table
CREATE TABLE IF NOT EXISTS matching_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    matching_result_id UUID NOT NULL REFERENCES matching_results(id) ON DELETE CASCADE,
    metadata_key VARCHAR(100) NOT NULL,
    metadata_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE matching_results IS 'Stores product matching relationships with confidence scores';
COMMENT ON COLUMN matching_results.confidence_score IS 'Confidence score from 0.00 to 1.00 indicating match quality';
COMMENT ON COLUMN matching_results.matching_method IS 'Algorithm used: name, sku, brand, specifications, or hybrid';
COMMENT ON COLUMN matching_results.status IS 'Match status: pending (auto-generated), confirmed (manually verified), rejected (marked as incorrect)';

COMMENT ON TABLE matching_metadata IS 'Stores additional metadata for matching results (algorithms, scores, debug info)';
COMMENT ON COLUMN matching_metadata.metadata_value IS 'JSON data containing matching details, algorithm parameters, etc.';

-- Create updated_at trigger for matching_results
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_matching_results_updated_at 
    BEFORE UPDATE ON matching_results 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();