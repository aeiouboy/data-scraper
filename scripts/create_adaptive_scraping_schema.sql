-- Category Discovery and Adaptive Scraping Schema
-- This schema supports automatic category discovery, structure monitoring,
-- and adaptive scraping with dynamic selector management

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: retailer_categories
-- Tracks discovered categories and their hierarchy for each retailer
CREATE TABLE IF NOT EXISTS retailer_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    retailer_code VARCHAR(10) NOT NULL,
    category_code VARCHAR(50) NOT NULL,
    category_name VARCHAR(255) NOT NULL,
    category_name_th VARCHAR(255), -- Thai name
    parent_category_id UUID REFERENCES retailer_categories(id) ON DELETE CASCADE,
    category_url TEXT NOT NULL,
    url_pattern TEXT, -- Regex pattern for this category's URLs
    level INTEGER NOT NULL DEFAULT 0, -- 0 = root, 1 = main category, 2 = subcategory, etc.
    position INTEGER, -- Display order within parent
    is_active BOOLEAN DEFAULT true,
    is_auto_discovered BOOLEAN DEFAULT false,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_verified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_scraped TIMESTAMP WITH TIME ZONE,
    product_count INTEGER DEFAULT 0,
    avg_success_rate DECIMAL(5,2) DEFAULT 0.00,
    scrape_frequency_hours INTEGER DEFAULT 24, -- How often to scrape this category
    metadata JSONB DEFAULT '{}', -- Additional category-specific data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(retailer_code, category_code)
);

-- Indexes for retailer_categories
CREATE INDEX idx_retailer_categories_retailer ON retailer_categories(retailer_code);
CREATE INDEX idx_retailer_categories_parent ON retailer_categories(parent_category_id);
CREATE INDEX idx_retailer_categories_active ON retailer_categories(is_active) WHERE is_active = true;
CREATE INDEX idx_retailer_categories_url ON retailer_categories(category_url);

-- Table: scraper_selectors
-- Stores CSS/XPath selectors for each retailer and element type
CREATE TABLE IF NOT EXISTS scraper_selectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    retailer_code VARCHAR(10) NOT NULL,
    page_type VARCHAR(50) NOT NULL, -- 'category', 'product', 'search'
    element_type VARCHAR(50) NOT NULL, -- 'product_name', 'price', 'image', etc.
    selector_type VARCHAR(20) NOT NULL, -- 'css', 'xpath', 'regex', 'json_path'
    selector_value TEXT NOT NULL,
    selector_context TEXT, -- Parent selector if needed
    priority INTEGER DEFAULT 1, -- Lower number = higher priority
    confidence_score DECIMAL(5,2) DEFAULT 1.00, -- 0-1 score based on success rate
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_success TIMESTAMP WITH TIME ZONE,
    last_failure TIMESTAMP WITH TIME ZONE,
    last_used TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    is_auto_discovered BOOLEAN DEFAULT false,
    discovered_method VARCHAR(50), -- 'manual', 'ai', 'pattern', 'similarity'
    validation_regex TEXT, -- Optional regex to validate extracted value
    transformation_rule TEXT, -- Optional transformation (e.g., 'strip', 'replace:x:y')
    fallback_value TEXT, -- Default value if extraction fails
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system',
    UNIQUE(retailer_code, page_type, element_type, selector_type, selector_value)
);

-- Indexes for scraper_selectors
CREATE INDEX idx_scraper_selectors_retailer ON scraper_selectors(retailer_code);
CREATE INDEX idx_scraper_selectors_element ON scraper_selectors(retailer_code, page_type, element_type);
CREATE INDEX idx_scraper_selectors_active ON scraper_selectors(is_active) WHERE is_active = true;
CREATE INDEX idx_scraper_selectors_confidence ON scraper_selectors(confidence_score DESC);

-- Table: website_structures
-- Tracks website structure changes over time
CREATE TABLE IF NOT EXISTS website_structures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    retailer_code VARCHAR(10) NOT NULL,
    page_type VARCHAR(50) NOT NULL,
    page_url TEXT NOT NULL,
    structure_hash VARCHAR(64) NOT NULL, -- Hash of the DOM structure
    dom_snapshot JSONB, -- Simplified DOM tree
    css_rules TEXT, -- Important CSS rules
    javascript_vars JSONB, -- Detected JS variables that might contain data
    detected_patterns JSONB, -- Patterns found in the structure
    element_signatures JSONB, -- Signatures of important elements
    change_type VARCHAR(50), -- 'initial', 'minor', 'major', 'breaking'
    changes_detected JSONB, -- Specific changes from previous version
    previous_structure_id UUID REFERENCES website_structures(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    analyzed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(retailer_code, page_type, structure_hash)
);

-- Indexes for website_structures
CREATE INDEX idx_website_structures_retailer ON website_structures(retailer_code, page_type);
CREATE INDEX idx_website_structures_created ON website_structures(created_at DESC);
CREATE INDEX idx_website_structures_hash ON website_structures(structure_hash);

-- Table: selector_performance
-- Tracks detailed performance metrics for selectors
CREATE TABLE IF NOT EXISTS selector_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    selector_id UUID NOT NULL REFERENCES scraper_selectors(id) ON DELETE CASCADE,
    job_id UUID, -- Reference to scrape_jobs if available
    url TEXT NOT NULL,
    execution_time_ms INTEGER,
    success BOOLEAN NOT NULL,
    extracted_value TEXT,
    error_message TEXT,
    error_type VARCHAR(50), -- 'not_found', 'timeout', 'invalid_value', etc.
    structure_hash VARCHAR(64), -- Hash of page structure when executed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for selector_performance
CREATE INDEX idx_selector_performance_selector ON selector_performance(selector_id);
CREATE INDEX idx_selector_performance_created ON selector_performance(created_at DESC);
CREATE INDEX idx_selector_performance_success ON selector_performance(success);

-- Table: category_changes
-- Log of detected category changes
CREATE TABLE IF NOT EXISTS category_changes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    retailer_code VARCHAR(10) NOT NULL,
    change_type VARCHAR(50) NOT NULL, -- 'new_category', 'removed_category', 'url_changed', 'name_changed'
    category_id UUID REFERENCES retailer_categories(id),
    old_value JSONB,
    new_value JSONB,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    confirmed_by VARCHAR(100),
    is_processed BOOLEAN DEFAULT false,
    notes TEXT
);

-- Indexes for category_changes
CREATE INDEX idx_category_changes_retailer ON category_changes(retailer_code);
CREATE INDEX idx_category_changes_detected ON category_changes(detected_at DESC);
CREATE INDEX idx_category_changes_unprocessed ON category_changes(is_processed) WHERE is_processed = false;

-- Table: scraper_rules
-- Business rules for scraping behavior
CREATE TABLE IF NOT EXISTS scraper_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    retailer_code VARCHAR(10),
    rule_type VARCHAR(50) NOT NULL, -- 'rate_limit', 'retry', 'validation', 'transformation'
    rule_name VARCHAR(100) NOT NULL,
    rule_config JSONB NOT NULL,
    priority INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(retailer_code, rule_type, rule_name)
);

-- Table: scraper_alerts
-- Alerts for scraping issues
CREATE TABLE IF NOT EXISTS scraper_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(50) NOT NULL, -- 'structure_change', 'high_failure_rate', 'new_category', etc.
    severity VARCHAR(20) NOT NULL, -- 'info', 'warning', 'error', 'critical'
    retailer_code VARCHAR(10),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(100),
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for scraper_alerts
CREATE INDEX idx_scraper_alerts_unresolved ON scraper_alerts(is_resolved) WHERE is_resolved = false;
CREATE INDEX idx_scraper_alerts_retailer ON scraper_alerts(retailer_code);
CREATE INDEX idx_scraper_alerts_created ON scraper_alerts(created_at DESC);

-- Functions and Triggers

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_retailer_categories_updated_at BEFORE UPDATE ON retailer_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scraper_selectors_updated_at BEFORE UPDATE ON scraper_selectors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scraper_rules_updated_at BEFORE UPDATE ON scraper_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate selector confidence score
CREATE OR REPLACE FUNCTION calculate_selector_confidence(success_count INTEGER, failure_count INTEGER)
RETURNS DECIMAL AS $$
BEGIN
    IF success_count + failure_count = 0 THEN
        RETURN 1.00;
    END IF;
    RETURN ROUND(success_count::DECIMAL / (success_count + failure_count), 2);
END;
$$ language 'plpgsql';

-- Function to update selector performance
CREATE OR REPLACE FUNCTION update_selector_performance()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the selector's statistics
    UPDATE scraper_selectors
    SET 
        success_count = CASE WHEN NEW.success THEN success_count + 1 ELSE success_count END,
        failure_count = CASE WHEN NOT NEW.success THEN failure_count + 1 ELSE failure_count END,
        last_success = CASE WHEN NEW.success THEN NEW.created_at ELSE last_success END,
        last_failure = CASE WHEN NOT NEW.success THEN NEW.created_at ELSE last_failure END,
        last_used = NEW.created_at,
        confidence_score = calculate_selector_confidence(
            CASE WHEN NEW.success THEN success_count + 1 ELSE success_count END,
            CASE WHEN NOT NEW.success THEN failure_count + 1 ELSE failure_count END
        )
    WHERE id = NEW.selector_id;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for selector performance updates
CREATE TRIGGER update_selector_stats_on_performance
    AFTER INSERT ON selector_performance
    FOR EACH ROW EXECUTE FUNCTION update_selector_performance();

-- Views for easier querying

-- View: active_categories_by_retailer
CREATE OR REPLACE VIEW active_categories_by_retailer AS
SELECT 
    rc.retailer_code,
    rc.id,
    rc.category_code,
    rc.category_name,
    rc.category_name_th,
    rc.level,
    rc.category_url,
    rc.product_count,
    rc.avg_success_rate,
    rc.last_scraped,
    pc.category_name as parent_category_name
FROM retailer_categories rc
LEFT JOIN retailer_categories pc ON rc.parent_category_id = pc.id
WHERE rc.is_active = true
ORDER BY rc.retailer_code, rc.level, rc.position;

-- View: selector_effectiveness
CREATE OR REPLACE VIEW selector_effectiveness AS
SELECT 
    ss.retailer_code,
    ss.page_type,
    ss.element_type,
    ss.selector_type,
    ss.selector_value,
    ss.confidence_score,
    ss.success_count,
    ss.failure_count,
    ss.last_success,
    ss.last_failure,
    CASE 
        WHEN ss.last_failure > ss.last_success OR ss.last_success IS NULL THEN 'failing'
        WHEN ss.confidence_score < 0.5 THEN 'unreliable'
        WHEN ss.confidence_score < 0.8 THEN 'degraded'
        ELSE 'healthy'
    END as status
FROM scraper_selectors ss
WHERE ss.is_active = true
ORDER BY ss.retailer_code, ss.page_type, ss.element_type, ss.priority;

-- View: recent_structure_changes
CREATE OR REPLACE VIEW recent_structure_changes AS
SELECT 
    ws.retailer_code,
    ws.page_type,
    ws.change_type,
    ws.created_at,
    ws.changes_detected,
    COUNT(DISTINCT ws2.id) as total_versions
FROM website_structures ws
LEFT JOIN website_structures ws2 ON ws.retailer_code = ws2.retailer_code 
    AND ws.page_type = ws2.page_type
WHERE ws.created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
GROUP BY ws.id, ws.retailer_code, ws.page_type, ws.change_type, ws.created_at, ws.changes_detected
ORDER BY ws.created_at DESC;

-- Initial data: Default selectors for common patterns
INSERT INTO scraper_selectors (retailer_code, page_type, element_type, selector_type, selector_value, priority, notes)
VALUES 
    -- Common patterns that work across many sites
    ('DEFAULT', 'product', 'product_name', 'css', 'h1', 1, 'Most common product title selector'),
    ('DEFAULT', 'product', 'price', 'css', '[class*="price"]', 1, 'Common price class pattern'),
    ('DEFAULT', 'product', 'image', 'css', 'img[src*="product"]', 1, 'Product image pattern'),
    ('DEFAULT', 'category', 'product_link', 'css', 'a[href*="/p/"]', 1, 'Common product URL pattern'),
    ('DEFAULT', 'category', 'pagination', 'css', 'a[href*="page="]', 1, 'Common pagination pattern')
ON CONFLICT DO NOTHING;

-- Grant permissions (adjust based on your user roles)
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;