-- Database indexes for price comparison performance optimization
-- Run these commands in Supabase SQL editor

-- Index for product_matches table
-- These indexes support the most common query patterns in price_comparisons_v2_optimized.py

-- 1. Index for unified_category (category filtering)
CREATE INDEX IF NOT EXISTS idx_product_matches_unified_category 
ON product_matches (unified_category);

-- 2. Index for price_range_max (savings filtering and sorting)
CREATE INDEX IF NOT EXISTS idx_product_matches_price_range_max 
ON product_matches (price_range_max);

-- 3. Index for price_variance_percentage (filtering and sorting)
CREATE INDEX IF NOT EXISTS idx_product_matches_price_variance_percentage 
ON product_matches (price_variance_percentage);

-- 4. Index for match_confidence (filtering)
CREATE INDEX IF NOT EXISTS idx_product_matches_match_confidence 
ON product_matches (match_confidence);

-- 5. Index for updated_at (sorting)
CREATE INDEX IF NOT EXISTS idx_product_matches_updated_at 
ON product_matches (updated_at DESC);

-- 6. Composite index for common filter combinations
CREATE INDEX IF NOT EXISTS idx_product_matches_category_confidence 
ON product_matches (unified_category, match_confidence);

-- 7. Composite index for price filtering
CREATE INDEX IF NOT EXISTS idx_product_matches_price_range 
ON product_matches (price_range_max, price_variance_percentage);

-- Index for products table (used in detailed comparisons)
-- These support the product detail queries

-- 8. Index for retailer_code (filtering by retailer)
CREATE INDEX IF NOT EXISTS idx_products_retailer_code 
ON products (retailer_code);

-- 9. Index for current_price (price calculations)
CREATE INDEX IF NOT EXISTS idx_products_current_price 
ON products (current_price);

-- 10. Index for availability (filtering in-stock products)
CREATE INDEX IF NOT EXISTS idx_products_availability 
ON products (availability);

-- 11. Composite index for retailer and price queries
CREATE INDEX IF NOT EXISTS idx_products_retailer_price 
ON products (retailer_code, current_price);

-- 12. Index for updated_at (sorting and freshness)
CREATE INDEX IF NOT EXISTS idx_products_updated_at 
ON products (updated_at DESC);

-- Performance monitoring queries
-- Use these to check if indexes are being used

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename IN ('product_matches', 'products')
ORDER BY idx_tup_read DESC;

-- Check query performance
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
WHERE query LIKE '%product_matches%' OR query LIKE '%products%'
ORDER BY total_time DESC
LIMIT 10;