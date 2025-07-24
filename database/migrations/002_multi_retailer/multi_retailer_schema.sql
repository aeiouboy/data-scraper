-- Multi-Retailer Database Schema Updates
-- Adds support for 6 Thai home improvement retailers
-- Execute in Supabase SQL Editor

-- ====================================================================
-- 1. UPDATE EXISTING PRODUCTS TABLE
-- ====================================================================

-- Add multi-retailer columns to existing products table
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS retailer_code VARCHAR(5) DEFAULT 'HP',
ADD COLUMN IF NOT EXISTS retailer_name VARCHAR(50) DEFAULT 'HomePro',
ADD COLUMN IF NOT EXISTS retailer_sku VARCHAR(100),
ADD COLUMN IF NOT EXISTS unified_category VARCHAR(100),
ADD COLUMN IF NOT EXISTS product_hash VARCHAR(32),
ADD COLUMN IF NOT EXISTS monitoring_tier VARCHAR(20) DEFAULT 'standard';

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_retailer_code ON products(retailer_code);
CREATE INDEX IF NOT EXISTS idx_products_unified_category ON products(unified_category);
CREATE INDEX IF NOT EXISTS idx_products_product_hash ON products(product_hash);
CREATE INDEX IF NOT EXISTS idx_products_monitoring_tier ON products(monitoring_tier);
CREATE INDEX IF NOT EXISTS idx_products_retailer_sku ON products(retailer_sku);

-- Update SKU constraint to be unique per retailer
ALTER TABLE products DROP CONSTRAINT IF EXISTS products_sku_key;
ALTER TABLE products 
ADD CONSTRAINT products_retailer_sku_unique UNIQUE (retailer_code, sku);

-- ====================================================================
-- 2. CREATE PRODUCT MATCHES TABLE
-- ====================================================================

-- Table for cross-retailer product matching
CREATE TABLE IF NOT EXISTS product_matches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    master_product_id UUID NOT NULL REFERENCES products(id),
    matched_product_ids UUID[] DEFAULT '{}',
    match_confidence DECIMAL(3,2) DEFAULT 0.0,
    match_criteria JSONB DEFAULT '{}',
    
    -- Product attributes for matching
    normalized_name TEXT NOT NULL,
    normalized_brand TEXT,
    unified_category VARCHAR(100) NOT NULL,
    key_specifications JSONB DEFAULT '{}',
    
    -- Price comparison data
    price_range_min DECIMAL(10,2),
    price_range_max DECIMAL(10,2),
    best_price_retailer VARCHAR(5),
    price_variance_percentage DECIMAL(5,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for product matches
CREATE INDEX IF NOT EXISTS idx_product_matches_master_id ON product_matches(master_product_id);
CREATE INDEX IF NOT EXISTS idx_product_matches_unified_category ON product_matches(unified_category);
CREATE INDEX IF NOT EXISTS idx_product_matches_normalized_name ON product_matches(normalized_name);
CREATE INDEX IF NOT EXISTS idx_product_matches_confidence ON product_matches(match_confidence);
CREATE INDEX IF NOT EXISTS idx_product_matches_best_price ON product_matches(best_price_retailer);

-- ====================================================================
-- 3. CREATE RETAILERS TABLE
-- ====================================================================

-- Master table for retailer configurations
CREATE TABLE IF NOT EXISTS retailers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    code VARCHAR(5) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    base_url TEXT NOT NULL,
    market_position VARCHAR(100),
    estimated_products INTEGER DEFAULT 0,
    
    -- Scraping configuration
    rate_limit_delay DECIMAL(3,1) DEFAULT 1.0,
    max_concurrent INTEGER DEFAULT 5,
    
    -- Market data
    focus_categories TEXT[],
    price_volatility VARCHAR(20) DEFAULT 'medium',
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert retailer configurations
INSERT INTO retailers (code, name, base_url, market_position, estimated_products, rate_limit_delay, max_concurrent, focus_categories, price_volatility) VALUES
('HP', 'HomePro', 'https://www.homepro.co.th', 'Market Leader', 68500, 1.0, 5, ARRAY['Appliances', 'Furniture', 'Construction'], 'medium'),
('TWD', 'Thai Watsadu', 'https://www.thaiwatsadu.com', 'Construction Specialist', 100000, 1.5, 3, ARRAY['Construction', 'Tools', 'Electrical'], 'low'),
('GH', 'Global House', 'https://www.globalhouse.co.th', 'Premium Home & Living', 300000, 2.0, 4, ARRAY['Furniture', 'Home Decor', 'Premium Living'], 'high'),
('DH', 'DoHome', 'https://www.dohome.co.th', 'Value Hardware Store', 200000, 1.0, 5, ARRAY['Hardware', 'Tools', 'DIY'], 'low'),
('BT', 'Boonthavorn', 'https://www.boonthavorn.com', 'Ceramic & Sanitary Specialist', 50000, 1.5, 3, ARRAY['Tiles', 'Bathroom', 'Kitchen'], 'medium'),
('MH', 'MegaHome', 'https://www.megahome.co.th', 'Building Materials Specialist', 100000, 1.2, 4, ARRAY['Construction', 'Hardware', 'Industrial'], 'low')
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    base_url = EXCLUDED.base_url,
    market_position = EXCLUDED.market_position,
    estimated_products = EXCLUDED.estimated_products,
    updated_at = NOW();

-- ====================================================================
-- 4. CREATE MONITORING TIERS TABLE
-- ====================================================================

-- Table for monitoring tier configurations
CREATE TABLE IF NOT EXISTS monitoring_tiers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tier_name VARCHAR(20) UNIQUE NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    target_success_rate DECIMAL(3,2) DEFAULT 0.95,
    priority_order INTEGER NOT NULL,
    description TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert monitoring tier configurations
INSERT INTO monitoring_tiers (tier_name, frequency, target_success_rate, priority_order, description) VALUES
('ultra_critical', 'daily', 0.995, 1, 'Daily monitoring for high-value products >฿10,000'),
('high_value', '3x_weekly', 0.99, 2, '3x weekly monitoring for products ฿3,000-10,000'),
('standard', 'weekly', 0.95, 3, 'Weekly monitoring for products ฿1,000-3,000'),
('low_priority', 'bi_weekly', 0.90, 4, 'Bi-weekly monitoring for products <฿1,000')
ON CONFLICT (tier_name) DO UPDATE SET
    frequency = EXCLUDED.frequency,
    target_success_rate = EXCLUDED.target_success_rate,
    description = EXCLUDED.description;

-- ====================================================================
-- 5. CREATE PRICE COMPARISONS VIEW
-- ====================================================================

-- View for cross-retailer price comparisons
CREATE OR REPLACE VIEW price_comparisons AS
SELECT 
    pm.id as match_id,
    pm.normalized_name,
    pm.unified_category,
    pm.price_range_min,
    pm.price_range_max,
    pm.best_price_retailer,
    pm.price_variance_percentage,
    
    -- Master product details
    p_master.id as master_product_id,
    p_master.name as master_product_name,
    p_master.current_price as master_price,
    p_master.retailer_name as master_retailer,
    
    -- Array of competitor prices
    ARRAY(
        SELECT json_build_object(
            'retailer_code', p_comp.retailer_code,
            'retailer_name', p_comp.retailer_name,
            'price', p_comp.current_price,
            'url', p_comp.url
        )
        FROM products p_comp 
        WHERE p_comp.product_hash = pm.master_product_id::text
        AND p_comp.id != pm.master_product_id
        AND p_comp.current_price IS NOT NULL
    ) as competitor_prices,
    
    pm.match_confidence,
    pm.updated_at
    
FROM product_matches pm
JOIN products p_master ON pm.master_product_id = p_master.id
WHERE pm.match_confidence > 0.7
ORDER BY pm.price_variance_percentage DESC;

-- ====================================================================
-- 6. CREATE RETAILER SUMMARY VIEW
-- ====================================================================

-- View for retailer performance summary
CREATE OR REPLACE VIEW retailer_summary AS
SELECT 
    r.code,
    r.name,
    r.market_position,
    r.estimated_products,
    
    -- Actual product counts
    COUNT(p.id) as actual_products,
    COUNT(CASE WHEN p.availability = 'in_stock' THEN 1 END) as in_stock_products,
    COUNT(CASE WHEN p.current_price IS NOT NULL THEN 1 END) as priced_products,
    
    -- Price statistics
    AVG(p.current_price) as avg_price,
    MIN(p.current_price) as min_price,
    MAX(p.current_price) as max_price,
    
    -- Monitoring tier distribution
    COUNT(CASE WHEN p.monitoring_tier = 'ultra_critical' THEN 1 END) as ultra_critical_count,
    COUNT(CASE WHEN p.monitoring_tier = 'high_value' THEN 1 END) as high_value_count,
    COUNT(CASE WHEN p.monitoring_tier = 'standard' THEN 1 END) as standard_count,
    COUNT(CASE WHEN p.monitoring_tier = 'low_priority' THEN 1 END) as low_priority_count,
    
    -- Data quality metrics
    ROUND(
        COUNT(CASE WHEN p.category IS NOT NULL THEN 1 END)::DECIMAL / 
        NULLIF(COUNT(p.id), 0) * 100, 2
    ) as category_coverage_percentage,
    
    ROUND(
        COUNT(CASE WHEN p.brand IS NOT NULL THEN 1 END)::DECIMAL / 
        NULLIF(COUNT(p.id), 0) * 100, 2
    ) as brand_coverage_percentage,
    
    MAX(p.scraped_at) as last_scraped_at
    
FROM retailers r
LEFT JOIN products p ON r.code = p.retailer_code
WHERE r.is_active = TRUE
GROUP BY r.code, r.name, r.market_position, r.estimated_products
ORDER BY actual_products DESC;

-- ====================================================================
-- 7. UPDATE EXISTING DATA
-- ====================================================================

-- Set retailer information for existing HomePro products
UPDATE products 
SET 
    retailer_code = 'HP',
    retailer_name = 'HomePro',
    monitoring_tier = CASE 
        WHEN current_price > 10000 THEN 'ultra_critical'
        WHEN current_price > 3000 THEN 'high_value'
        WHEN current_price > 1000 THEN 'standard'
        ELSE 'low_priority'
    END,
    unified_category = CASE 
        WHEN category LIKE '%เฟอร์นิเจอร์%' THEN 'furniture'
        WHEN category LIKE '%เครื่องใช้ไฟฟ้า%' THEN 'appliances'
        WHEN category LIKE '%ห้องครัว%' THEN 'kitchen'
        WHEN category LIKE '%ห้องน้ำ%' THEN 'bathroom'
        WHEN category LIKE '%สี%' THEN 'paint'
        WHEN category LIKE '%โคมไฟ%' OR category LIKE '%หลอดไฟ%' THEN 'lighting'
        WHEN category LIKE '%วัสดุก่อสร้าง%' THEN 'construction'
        WHEN category LIKE '%เครื่องมือ%' THEN 'tools'
        WHEN category LIKE '%ของใช้กลางแจ้ง%' THEN 'outdoor'
        WHEN category LIKE '%ห้องนอน%' THEN 'bedroom'
        ELSE 'household'
    END
WHERE retailer_code IS NULL OR retailer_code = 'HP';

-- Generate product hashes for existing products
UPDATE products 
SET product_hash = MD5(
    LOWER(REGEXP_REPLACE(name, '[^\w\s]', '', 'g')) || '_' ||
    LOWER(REGEXP_REPLACE(COALESCE(brand, ''), '[^\w\s]', '', 'g')) || '_' ||
    COALESCE(unified_category, '')
)
WHERE product_hash IS NULL;

-- ====================================================================
-- 8. CREATE TRIGGERS
-- ====================================================================

-- Trigger to automatically update product_hash when relevant fields change
CREATE OR REPLACE FUNCTION update_product_hash()
RETURNS TRIGGER AS $$
BEGIN
    NEW.product_hash = MD5(
        LOWER(REGEXP_REPLACE(NEW.name, '[^\w\s]', '', 'g')) || '_' ||
        LOWER(REGEXP_REPLACE(COALESCE(NEW.brand, ''), '[^\w\s]', '', 'g')) || '_' ||
        COALESCE(NEW.unified_category, '')
    );
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_product_hash
    BEFORE UPDATE OF name, brand, unified_category ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_product_hash();

-- Trigger to update monitoring tier based on price changes
CREATE OR REPLACE FUNCTION update_monitoring_tier()
RETURNS TRIGGER AS $$
BEGIN
    -- Get retailer-specific tier logic (simplified version)
    IF NEW.retailer_code = 'GH' THEN
        -- Global House: Higher thresholds due to premium positioning
        NEW.monitoring_tier = CASE 
            WHEN NEW.current_price > 15000 THEN 'ultra_critical'
            WHEN NEW.current_price > 5000 THEN 'high_value'
            WHEN NEW.current_price > 2000 THEN 'standard'
            ELSE 'low_priority'
        END;
    ELSIF NEW.retailer_code = 'HP' THEN
        -- HomePro: Standard market leader thresholds
        NEW.monitoring_tier = CASE 
            WHEN NEW.current_price > 10000 THEN 'ultra_critical'
            WHEN NEW.current_price > 3000 THEN 'high_value'
            WHEN NEW.current_price > 1000 THEN 'standard'
            ELSE 'low_priority'
        END;
    ELSE
        -- Other retailers: Conservative thresholds
        NEW.monitoring_tier = CASE 
            WHEN NEW.current_price > 8000 THEN 'ultra_critical'
            WHEN NEW.current_price > 2500 THEN 'high_value'
            WHEN NEW.current_price > 800 THEN 'standard'
            ELSE 'low_priority'
        END;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_monitoring_tier
    BEFORE INSERT OR UPDATE OF current_price, retailer_code ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_monitoring_tier();

-- ====================================================================
-- 9. PERFORMANCE OPTIMIZATIONS
-- ====================================================================

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_products_retailer_category ON products(retailer_code, unified_category);
CREATE INDEX IF NOT EXISTS idx_products_retailer_tier ON products(retailer_code, monitoring_tier);
CREATE INDEX IF NOT EXISTS idx_products_price_range ON products(current_price) WHERE current_price IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_availability_price ON products(availability, current_price) WHERE availability = 'in_stock';

-- Partial indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_active_monitoring ON products(monitoring_tier, scraped_at) 
WHERE availability != 'out_of_stock';

-- ====================================================================
-- 10. SECURITY & PERMISSIONS
-- ====================================================================

-- Grant appropriate permissions to authenticated users
GRANT SELECT ON retailers TO authenticated;
GRANT SELECT ON monitoring_tiers TO authenticated;
GRANT SELECT ON price_comparisons TO authenticated;
GRANT SELECT ON retailer_summary TO authenticated;

-- Grant select and insert on product_matches for the application
GRANT SELECT, INSERT, UPDATE ON product_matches TO authenticated;

-- ====================================================================
-- VERIFICATION QUERIES
-- ====================================================================

-- Verify schema updates
DO $$
BEGIN
    RAISE NOTICE 'Multi-retailer schema update completed successfully!';
    RAISE NOTICE 'Total retailers configured: %', (SELECT COUNT(*) FROM retailers);
    RAISE NOTICE 'Total products: %', (SELECT COUNT(*) FROM products);
    RAISE NOTICE 'Products with retailer info: %', (SELECT COUNT(*) FROM products WHERE retailer_code IS NOT NULL);
    RAISE NOTICE 'Monitoring tiers configured: %', (SELECT COUNT(*) FROM monitoring_tiers);
END
$$;

-- Test query to show retailer distribution
SELECT 
    retailer_code,
    retailer_name,
    COUNT(*) as product_count,
    COUNT(CASE WHEN monitoring_tier = 'ultra_critical' THEN 1 END) as ultra_critical,
    COUNT(CASE WHEN monitoring_tier = 'high_value' THEN 1 END) as high_value,
    COUNT(CASE WHEN monitoring_tier = 'standard' THEN 1 END) as standard,
    COUNT(CASE WHEN monitoring_tier = 'low_priority' THEN 1 END) as low_priority
FROM products 
GROUP BY retailer_code, retailer_name
ORDER BY product_count DESC;

-- ====================================================================
-- COMPLETION NOTICE
-- ====================================================================

COMMENT ON TABLE retailers IS 'Master configuration table for all supported retailers';
COMMENT ON TABLE product_matches IS 'Cross-retailer product matching for price comparison';
COMMENT ON TABLE monitoring_tiers IS 'Configuration for monitoring frequency tiers';
COMMENT ON VIEW price_comparisons IS 'Unified view for cross-retailer price analysis';
COMMENT ON VIEW retailer_summary IS 'Performance and coverage summary by retailer';

-- Schema update completed
SELECT 'Multi-retailer schema successfully updated! 🎉' as status;