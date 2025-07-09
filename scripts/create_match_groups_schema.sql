-- Enhanced schema for improved product matching and price comparison
-- Run this after the existing schema

-- Match groups table for canonical product representation
CREATE TABLE IF NOT EXISTS match_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name TEXT NOT NULL,
    canonical_brand TEXT,
    category TEXT NOT NULL,
    subcategory TEXT,
    product_type TEXT NOT NULL,
    model_number TEXT,
    key_features JSONB DEFAULT '[]'::jsonb,
    specifications JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for searching
CREATE INDEX idx_match_groups_category ON match_groups(category);
CREATE INDEX idx_match_groups_brand ON match_groups(canonical_brand);
CREATE INDEX idx_match_groups_type ON match_groups(product_type);
CREATE INDEX idx_match_groups_features ON match_groups USING gin(key_features);

-- Match confidence tracking
CREATE TABLE IF NOT EXISTS match_confidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_group_id UUID REFERENCES match_groups(id) ON DELETE CASCADE,
    overall_score DECIMAL(3,2) NOT NULL CHECK (overall_score >= 0 AND overall_score <= 1),
    name_match_score DECIMAL(3,2) CHECK (name_match_score >= 0 AND name_match_score <= 1),
    brand_match_score DECIMAL(3,2) CHECK (brand_match_score >= 0 AND brand_match_score <= 1),
    spec_match_score DECIMAL(3,2) CHECK (spec_match_score >= 0 AND spec_match_score <= 1),
    price_consistency_score DECIMAL(3,2) CHECK (price_consistency_score >= 0 AND price_consistency_score <= 1),
    user_validation_score DECIMAL(3,2) CHECK (user_validation_score >= 0 AND user_validation_score <= 1),
    confidence_level TEXT CHECK (confidence_level IN ('exact', 'high', 'medium', 'low', 'none')),
    factors JSONB DEFAULT '[]'::jsonb,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(match_group_id)
);

-- Product to match group mapping
CREATE TABLE IF NOT EXISTS product_match_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    match_group_id UUID REFERENCES match_groups(id) ON DELETE CASCADE,
    retailer_code TEXT NOT NULL,
    variant_type TEXT,
    variant_value TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    mapped_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(product_id),
    FOREIGN KEY (retailer_code) REFERENCES retailers(code)
);

-- Index for efficient lookups
CREATE INDEX idx_product_match_mapping_group ON product_match_mapping(match_group_id);
CREATE INDEX idx_product_match_mapping_retailer ON product_match_mapping(retailer_code);

-- Match metadata for algorithm tracking
CREATE TABLE IF NOT EXISTS match_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_group_id UUID REFERENCES match_groups(id) ON DELETE CASCADE,
    algorithm_version TEXT NOT NULL,
    match_features JSONB NOT NULL DEFAULT '[]'::jsonb,
    mismatched_features TEXT[] DEFAULT '{}',
    processing_time_ms INTEGER,
    data_sources TEXT[] DEFAULT '{}',
    ml_model_used TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_validated TIMESTAMPTZ
);

-- Price analysis cache
CREATE TABLE IF NOT EXISTS price_analysis_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_group_id UUID REFERENCES match_groups(id) ON DELETE CASCADE,
    analysis_type TEXT NOT NULL CHECK (analysis_type IN ('current', 'historical', 'volatility', 'forecast')),
    current_best_price DECIMAL(10,2),
    current_best_retailer TEXT,
    savings_amount DECIMAL(10,2),
    savings_percentage DECIMAL(5,2),
    volatility_level TEXT CHECK (volatility_level IN ('stable', 'low', 'moderate', 'high', 'extreme')),
    volatility_score DECIMAL(3,2) CHECK (volatility_score >= 0 AND volatility_score <= 1),
    price_trends JSONB,
    anomalies JSONB,
    data JSONB NOT NULL,
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    UNIQUE(match_group_id, analysis_type)
);

-- Index for cache lookups (without WHERE clause due to PostgreSQL IMMUTABLE requirement)
CREATE INDEX idx_price_analysis_cache_lookup 
    ON price_analysis_cache(match_group_id, analysis_type, expires_at);

-- Price monitoring subscriptions
CREATE TABLE IF NOT EXISTS price_monitoring_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    email TEXT,
    match_group_id UUID REFERENCES match_groups(id) ON DELETE CASCADE,
    threshold_percentage DECIMAL(5,2) DEFAULT 5.0,
    threshold_amount DECIMAL(10,2),
    monitor_type TEXT DEFAULT 'drop' CHECK (monitor_type IN ('drop', 'increase', 'any')),
    notification_channels JSONB DEFAULT '["email"]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    last_notified TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Index for active subscriptions (simplified to avoid IMMUTABLE requirement)
CREATE INDEX idx_price_monitoring_active 
    ON price_monitoring_subscriptions(match_group_id, is_active, expires_at);

-- User match feedback for improving algorithm
CREATE TABLE IF NOT EXISTS user_match_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_group_id UUID REFERENCES match_groups(id) ON DELETE CASCADE,
    product1_id UUID REFERENCES products(id),
    product2_id UUID REFERENCES products(id),
    is_correct_match BOOLEAN NOT NULL,
    confidence_override DECIMAL(3,2) CHECK (confidence_override >= 0 AND confidence_override <= 1),
    feedback_reason TEXT,
    user_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Match group statistics
CREATE TABLE IF NOT EXISTS match_group_stats (
    match_group_id UUID PRIMARY KEY REFERENCES match_groups(id) ON DELETE CASCADE,
    retailer_count INTEGER DEFAULT 0,
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    avg_price DECIMAL(10,2),
    price_variance DECIMAL(10,2),
    total_views INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Create function to update match group stats
CREATE OR REPLACE FUNCTION update_match_group_stats(p_match_group_id UUID)
RETURNS VOID AS $$
DECLARE
    v_stats RECORD;
BEGIN
    -- Calculate statistics
    WITH price_stats AS (
        SELECT 
            COUNT(DISTINCT pmm.retailer_code) as retailer_count,
            MIN(p.current_price) as min_price,
            MAX(p.current_price) as max_price,
            AVG(p.current_price) as avg_price,
            VARIANCE(p.current_price) as price_variance
        FROM product_match_mapping pmm
        JOIN products p ON pmm.product_id = p.id
        WHERE pmm.match_group_id = p_match_group_id
            AND p.current_price > 0
    )
    SELECT * INTO v_stats FROM price_stats;
    
    -- Update or insert stats
    INSERT INTO match_group_stats (
        match_group_id, retailer_count, min_price, max_price, 
        avg_price, price_variance, last_updated
    ) VALUES (
        p_match_group_id, v_stats.retailer_count, v_stats.min_price,
        v_stats.max_price, v_stats.avg_price, v_stats.price_variance, NOW()
    )
    ON CONFLICT (match_group_id) DO UPDATE
    SET 
        retailer_count = EXCLUDED.retailer_count,
        min_price = EXCLUDED.min_price,
        max_price = EXCLUDED.max_price,
        avg_price = EXCLUDED.avg_price,
        price_variance = EXCLUDED.price_variance,
        last_updated = NOW();
END;
$$ LANGUAGE plpgsql;

-- Trigger to update match group timestamp
CREATE OR REPLACE FUNCTION update_match_group_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE match_groups 
    SET updated_at = NOW() 
    WHERE id = NEW.match_group_id;
    
    -- Also update stats
    PERFORM update_match_group_stats(NEW.match_group_id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_match_group_on_mapping
AFTER INSERT OR UPDATE OR DELETE ON product_match_mapping
FOR EACH ROW EXECUTE FUNCTION update_match_group_timestamp();

-- Create view for easy match group querying
CREATE OR REPLACE VIEW match_group_details AS
SELECT 
    mg.id,
    mg.canonical_name,
    mg.canonical_brand,
    mg.category,
    mg.product_type,
    mg.key_features,
    mc.overall_score as confidence_score,
    mc.confidence_level,
    mgs.retailer_count,
    mgs.min_price,
    mgs.max_price,
    mgs.avg_price,
    CASE 
        WHEN mgs.min_price > 0 AND mgs.max_price > mgs.min_price 
        THEN ((mgs.max_price - mgs.min_price) / mgs.min_price * 100)
        ELSE 0 
    END as price_variance_percentage,
    pac.current_best_price,
    pac.current_best_retailer,
    pac.savings_amount,
    pac.savings_percentage,
    pac.volatility_level,
    mg.created_at,
    mg.updated_at
FROM match_groups mg
LEFT JOIN match_confidence mc ON mg.id = mc.match_group_id
LEFT JOIN match_group_stats mgs ON mg.id = mgs.match_group_id
LEFT JOIN price_analysis_cache pac ON mg.id = pac.match_group_id 
    AND pac.analysis_type = 'current';

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO authenticated;