-- Optimize price comparisons performance
-- Run this script in Supabase SQL editor

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_product_matches_category 
ON product_matches(unified_category);

CREATE INDEX IF NOT EXISTS idx_product_matches_savings 
ON product_matches(price_variance_percentage DESC, price_range_max DESC);

CREATE INDEX IF NOT EXISTS idx_product_matches_updated 
ON product_matches(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_products_retailer_price 
ON products(retailer_code, current_price);

-- Create materialized view for product match details with pre-joined data
CREATE MATERIALIZED VIEW IF NOT EXISTS product_match_details AS
SELECT 
    pm.id,
    pm.normalized_name,
    pm.normalized_brand,
    pm.unified_category,
    pm.price_range_min,
    pm.price_range_max,
    pm.price_variance_percentage,
    pm.best_price_retailer,
    pm.match_confidence,
    pm.key_specifications,
    pm.updated_at,
    pm.master_product_id,
    pm.matched_product_ids,
    COALESCE(pm.price_range_max - pm.price_range_min, 0) AS savings_amount,
    -- Pre-aggregate matched products data as JSON
    (
        SELECT json_agg(
            json_build_object(
                'id', p.id,
                'retailer_code', p.retailer_code,
                'retailer_name', p.retailer_name,
                'name', p.name,
                'current_price', p.current_price,
                'original_price', p.original_price,
                'discount_percentage', p.discount_percentage,
                'url', p.url,
                'images', p.images,
                'availability', p.availability,
                'updated_at', p.updated_at
            )
        )
        FROM products p
        WHERE p.id = pm.master_product_id 
           OR p.id = ANY(pm.matched_product_ids)
    ) AS matched_products
FROM product_matches pm
WHERE pm.price_variance_percentage > 0;

-- Create index on the materialized view
CREATE INDEX IF NOT EXISTS idx_match_details_category 
ON product_match_details(unified_category);

CREATE INDEX IF NOT EXISTS idx_match_details_savings 
ON product_match_details(savings_amount DESC);

-- Create view for category savings summary
CREATE OR REPLACE VIEW category_savings_summary AS
SELECT 
    unified_category AS category,
    COUNT(*) AS product_count,
    AVG(COALESCE(price_range_max - price_range_min, 0)) AS avg_savings,
    MAX(COALESCE(price_range_max - price_range_min, 0)) AS max_savings,
    SUM(COALESCE(price_range_max - price_range_min, 0)) AS total_savings
FROM product_matches
WHERE price_variance_percentage > 0
GROUP BY unified_category;

-- Create table for pre-aggregated stats (updated periodically)
CREATE TABLE IF NOT EXISTS price_comparison_stats (
    id SERIAL PRIMARY KEY,
    category VARCHAR(255),
    total_savings DECIMAL(10,2),
    products_with_savings INTEGER,
    avg_price_variance DECIMAL(5,2),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(category)
);

-- Function to refresh stats
CREATE OR REPLACE FUNCTION refresh_price_comparison_stats()
RETURNS void AS $$
BEGIN
    -- Clear existing stats
    TRUNCATE price_comparison_stats;
    
    -- Insert overall stats
    INSERT INTO price_comparison_stats (
        category, 
        total_savings, 
        products_with_savings, 
        avg_price_variance
    )
    SELECT 
        NULL as category,
        SUM(COALESCE(price_range_max - price_range_min, 0)),
        COUNT(*),
        AVG(price_variance_percentage)
    FROM product_matches
    WHERE price_variance_percentage > 0;
    
    -- Insert category-specific stats
    INSERT INTO price_comparison_stats (
        category, 
        total_savings, 
        products_with_savings, 
        avg_price_variance
    )
    SELECT 
        unified_category,
        SUM(COALESCE(price_range_max - price_range_min, 0)),
        COUNT(*),
        AVG(price_variance_percentage)
    FROM product_matches
    WHERE price_variance_percentage > 0
    GROUP BY unified_category;
END;
$$ LANGUAGE plpgsql;

-- Refresh stats initially
SELECT refresh_price_comparison_stats();

-- Create a function to refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_product_match_details()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY product_match_details;
END;
$$ LANGUAGE plpgsql;

-- Schedule periodic refresh (if using pg_cron extension)
-- SELECT cron.schedule('refresh-match-details', '*/15 * * * *', 'SELECT refresh_product_match_details()');
-- SELECT cron.schedule('refresh-price-stats', '*/30 * * * *', 'SELECT refresh_price_comparison_stats()');

-- Grant permissions
GRANT SELECT ON product_match_details TO authenticated;
GRANT SELECT ON category_savings_summary TO authenticated;
GRANT SELECT ON price_comparison_stats TO authenticated;