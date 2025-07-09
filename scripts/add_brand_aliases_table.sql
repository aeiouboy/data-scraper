-- Add brand aliases table for improved product matching
-- This table maps various brand name representations to a canonical brand name

-- ====================================================================
-- 1. CREATE BRAND ALIASES TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS brand_aliases (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    canonical_brand VARCHAR(100) NOT NULL,
    alias VARCHAR(100) NOT NULL,
    language VARCHAR(10) DEFAULT 'th',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(alias)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_brand_aliases_canonical ON brand_aliases(canonical_brand);
CREATE INDEX IF NOT EXISTS idx_brand_aliases_alias ON brand_aliases(alias);
CREATE INDEX IF NOT EXISTS idx_brand_aliases_language ON brand_aliases(language);

-- ====================================================================
-- 2. INSERT COMMON BRAND ALIASES
-- ====================================================================

INSERT INTO brand_aliases (canonical_brand, alias, language) VALUES
-- Electronics brands
('MITSUBISHI', 'มิตซูบิชิ', 'th'),
('MITSUBISHI', 'mitsubishi', 'en'),
('MITSUBISHI', 'มิตซู', 'th'),
('MITSUBISHI', 'MITSU', 'en'),

('SAMSUNG', 'ซัมซุง', 'th'),
('SAMSUNG', 'samsung', 'en'),
('SAMSUNG', 'แซมซุง', 'th'),

('LG', 'แอลจี', 'th'),
('LG', 'lg', 'en'),
('LG', 'แอล จี', 'th'),

('PANASONIC', 'พานาโซนิค', 'th'),
('PANASONIC', 'panasonic', 'en'),
('PANASONIC', 'พานาโซนิก', 'th'),

('TOSHIBA', 'โตชิบา', 'th'),
('TOSHIBA', 'toshiba', 'en'),
('TOSHIBA', 'โตชิบ้า', 'th'),

('SHARP', 'ชาร์ป', 'th'),
('SHARP', 'sharp', 'en'),
('SHARP', 'ชาร์ฟ', 'th'),

('DAIKIN', 'ไดกิ้น', 'th'),
('DAIKIN', 'daikin', 'en'),

('FUJITSU', 'ฟูจิตสึ', 'th'),
('FUJITSU', 'fujitsu', 'en'),
('FUJITSU', 'ฟูจิ', 'th'),

('HAIER', 'ไฮเออร์', 'th'),
('HAIER', 'haier', 'en'),

('ELECTROLUX', 'อีเลคโทรลักซ์', 'th'),
('ELECTROLUX', 'electrolux', 'en'),
('ELECTROLUX', 'อีเล็กโทรลักซ์', 'th'),

('PHILIPS', 'ฟิลิปส์', 'th'),
('PHILIPS', 'philips', 'en'),
('PHILIPS', 'ฟิลลิปส์', 'th'),

('SONY', 'โซนี่', 'th'),
('SONY', 'sony', 'en'),
('SONY', 'โซนี', 'th'),

-- Construction/Paint brands
('SCG', 'เอสซีจี', 'th'),
('SCG', 'scg', 'en'),
('SCG', 'เอส ซี จี', 'th'),

('TOA', 'ทีโอเอ', 'th'),
('TOA', 'toa', 'en'),
('TOA', 'ที โอ เอ', 'th'),

('CROCODILE', 'จระเข้', 'th'),
('CROCODILE', 'crocodile', 'en'),
('CROCODILE', 'ตราจระเข้', 'th'),

('ELEPHANT', 'ตราช้าง', 'th'),
('ELEPHANT', 'elephant', 'en'),
('ELEPHANT', 'ช้าง', 'th'),

-- Furniture brands
('INDEX LIVING MALL', 'อินเด็กซ์', 'th'),
('INDEX LIVING MALL', 'index', 'en'),
('INDEX LIVING MALL', 'อินเด็กซ์ ลิฟวิ่งมอลล์', 'th'),

('SB FURNITURE', 'เอสบี', 'th'),
('SB FURNITURE', 'sb', 'en'),
('SB FURNITURE', 'เอสบี เฟอร์นิเจอร์', 'th'),

-- Tools brands
('BOSCH', 'บ๊อช', 'th'),
('BOSCH', 'bosch', 'en'),
('BOSCH', 'บอช', 'th'),

('MAKITA', 'มากิต้า', 'th'),
('MAKITA', 'makita', 'en'),
('MAKITA', 'มาคิตะ', 'th'),

('STANLEY', 'สแตนเลย์', 'th'),
('STANLEY', 'stanley', 'en'),
('STANLEY', 'แสตนเล่ย์', 'th')

ON CONFLICT (alias) DO UPDATE SET
    canonical_brand = EXCLUDED.canonical_brand,
    language = EXCLUDED.language;

-- ====================================================================
-- 3. CREATE FUNCTION TO GET CANONICAL BRAND
-- ====================================================================

CREATE OR REPLACE FUNCTION get_canonical_brand(brand_name TEXT)
RETURNS TEXT AS $$
DECLARE
    canonical TEXT;
BEGIN
    -- First check if it's already a canonical brand
    SELECT canonical_brand INTO canonical
    FROM brand_aliases
    WHERE UPPER(alias) = UPPER(brand_name)
    LIMIT 1;
    
    IF canonical IS NOT NULL THEN
        RETURN canonical;
    END IF;
    
    -- If not found, return the original brand name in uppercase
    RETURN UPPER(TRIM(brand_name));
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- 4. CREATE PRODUCT MODELS TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS product_models (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    model_number VARCHAR(100) NOT NULL,
    canonical_brand VARCHAR(100),
    product_type VARCHAR(100),
    specifications JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(model_number, canonical_brand)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_product_models_model ON product_models(model_number);
CREATE INDEX IF NOT EXISTS idx_product_models_brand ON product_models(canonical_brand);
CREATE INDEX IF NOT EXISTS idx_product_models_type ON product_models(product_type);

-- ====================================================================
-- 5. CREATE MATCH HISTORY TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS match_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    product1_id UUID NOT NULL REFERENCES products(id),
    product2_id UUID NOT NULL REFERENCES products(id),
    match_score DECIMAL(3,2) NOT NULL,
    match_details JSONB DEFAULT '{}',
    match_status VARCHAR(20) DEFAULT 'pending', -- pending, confirmed, rejected
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_match_history_product1 ON match_history(product1_id);
CREATE INDEX IF NOT EXISTS idx_match_history_product2 ON match_history(product2_id);
CREATE INDEX IF NOT EXISTS idx_match_history_status ON match_history(match_status);
CREATE INDEX IF NOT EXISTS idx_match_history_score ON match_history(match_score);

-- ====================================================================
-- 6. UPDATE EXISTING PRODUCTS WITH CANONICAL BRANDS
-- ====================================================================

UPDATE products 
SET brand = get_canonical_brand(brand)
WHERE brand IS NOT NULL;

-- ====================================================================
-- 7. CREATE VIEW FOR BRAND DISTRIBUTION
-- ====================================================================

CREATE OR REPLACE VIEW brand_distribution AS
SELECT 
    get_canonical_brand(p.brand) as canonical_brand,
    p.retailer_code,
    p.retailer_name,
    COUNT(*) as product_count,
    COUNT(DISTINCT p.unified_category) as category_count,
    AVG(p.current_price) as avg_price,
    MIN(p.current_price) as min_price,
    MAX(p.current_price) as max_price
FROM products p
WHERE p.brand IS NOT NULL
GROUP BY canonical_brand, p.retailer_code, p.retailer_name
ORDER BY canonical_brand, product_count DESC;

-- ====================================================================
-- 8. GRANT PERMISSIONS
-- ====================================================================

GRANT SELECT ON brand_aliases TO authenticated;
GRANT SELECT ON product_models TO authenticated;
GRANT SELECT, INSERT, UPDATE ON match_history TO authenticated;
GRANT SELECT ON brand_distribution TO authenticated;

-- ====================================================================
-- VERIFICATION
-- ====================================================================

SELECT 
    'Brand aliases created: ' || COUNT(*)::TEXT as status
FROM brand_aliases;

SELECT 
    'Sample canonical brands:' as description,
    canonical_brand,
    COUNT(*) as alias_count
FROM brand_aliases
GROUP BY canonical_brand
ORDER BY alias_count DESC
LIMIT 10;