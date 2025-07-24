-- HomePro Scraper Database Schema for Supabase

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    name_en TEXT,
    parent_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    path TEXT,
    level INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    brand TEXT,
    category TEXT,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    current_price DECIMAL(12,2),
    original_price DECIMAL(12,2),
    discount_percentage DECIMAL(5,2),
    description TEXT,
    features JSONB DEFAULT '[]'::jsonb,
    specifications JSONB DEFAULT '{}'::jsonb,
    availability TEXT DEFAULT 'unknown',
    images JSONB DEFAULT '[]'::jsonb,
    url TEXT NOT NULL,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Price history table
CREATE TABLE IF NOT EXISTS price_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    price DECIMAL(12,2) NOT NULL,
    original_price DECIMAL(12,2),
    discount_percentage DECIMAL(5,2),
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scrape jobs table
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    job_type TEXT NOT NULL CHECK (job_type IN ('discovery', 'product', 'category')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    target_url TEXT,
    total_items INT DEFAULT 0,
    processed_items INT DEFAULT 0,
    success_items INT DEFAULT 0,
    failed_items INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_scraped_at ON products(scraped_at);
CREATE INDEX idx_price_history_product_id ON price_history(product_id);
CREATE INDEX idx_price_history_recorded_at ON price_history(recorded_at);
CREATE INDEX idx_scrape_jobs_status ON scrape_jobs(status);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS)
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_jobs ENABLE ROW LEVEL SECURITY;

-- Policies for public read access
CREATE POLICY "Products are viewable by everyone" ON products
    FOR SELECT USING (true);

CREATE POLICY "Categories are viewable by everyone" ON categories
    FOR SELECT USING (true);

CREATE POLICY "Price history is viewable by everyone" ON price_history
    FOR SELECT USING (true);

-- Policies for authenticated write access
CREATE POLICY "Authenticated users can insert products" ON products
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can update products" ON products
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can manage scrape jobs" ON scrape_jobs
    FOR ALL USING (auth.role() = 'authenticated');

-- Views for analytics
CREATE OR REPLACE VIEW product_stats AS
SELECT 
    COUNT(*) as total_products,
    COUNT(DISTINCT brand) as total_brands,
    COUNT(DISTINCT category) as total_categories,
    AVG(current_price) as avg_price,
    MIN(current_price) as min_price,
    MAX(current_price) as max_price,
    COUNT(CASE WHEN discount_percentage > 0 THEN 1 END) as products_on_sale,
    AVG(discount_percentage) FILTER (WHERE discount_percentage > 0) as avg_discount
FROM products;

CREATE OR REPLACE VIEW daily_scrape_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as jobs_run,
    SUM(success_items) as total_success,
    SUM(failed_items) as total_failed,
    AVG(CASE WHEN processed_items > 0 THEN success_items::float / processed_items * 100 ELSE 0 END) as avg_success_rate
FROM scrape_jobs
WHERE status = 'completed'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Grant access to views
GRANT SELECT ON product_stats TO anon;
GRANT SELECT ON daily_scrape_stats TO anon;