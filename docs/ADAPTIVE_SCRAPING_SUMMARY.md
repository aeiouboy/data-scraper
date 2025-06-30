# Adaptive Scraping System - Implementation Summary

## What We Built

We've created a comprehensive adaptive scraping system that automatically discovers categories and adapts to website structure changes. This system makes your scrapers resilient and reduces manual maintenance.

## Key Components Implemented

### 1. Database Schema (`scripts/create_adaptive_scraping_schema.sql`)
- **retailer_categories** - Stores discovered categories with hierarchy
- **scraper_selectors** - Dynamic CSS/XPath selectors for each element
- **website_structures** - Tracks website structure changes
- **selector_performance** - Performance metrics for each selector
- **category_changes** - Log of detected changes
- **scraper_alerts** - Alerts for issues requiring attention

### 2. Category Explorer (`app/core/category_explorer.py`)
- Automatically discovers category structures from retailer websites
- Builds hierarchical category trees
- Detects new categories and subcategories
- Saves discovered categories to database

### 3. Category Monitor (`app/services/category_monitor.py`)
- Monitors categories for changes (removed, URL changed, new)
- Calculates category health metrics
- Creates alerts for critical changes
- Runs scheduled checks on category validity

### 4. Scraper Configuration Manager (`app/core/scraper_config_manager.py`)
- Manages dynamic selectors without code changes
- Tracks selector performance and success rates
- Automatically deactivates failing selectors
- Supports multiple selector types (CSS, XPath, Regex, JSON)

### 5. API Endpoints (`app/api/routers/categories.py`)
- `/api/categories/discover` - Trigger category discovery
- `/api/categories/tree/{retailer}` - Get category hierarchy
- `/api/categories/changes` - View recent changes
- `/api/categories/monitor` - Start monitoring
- `/api/categories/health/{retailer}` - Get health metrics

### 6. Adaptive Scraper Mixin (`app/scrapers/adaptive_scraper_mixin.py`)
- Adds adaptive capabilities to existing scrapers
- Automatic fallback through multiple selectors
- Performance tracking for each extraction
- Self-healing selector discovery

## How It Works

### 1. Initial Setup
```python
# Discover all categories for a retailer
POST /api/categories/discover?retailer_code=HP&max_depth=3

# This will:
# - Crawl the website starting from homepage
# - Find all category links
# - Explore subcategories up to max_depth
# - Save to database with hierarchy
```

### 2. Continuous Monitoring
```python
# Run daily/weekly monitoring
POST /api/categories/monitor

# This will:
# - Check sample of categories for each retailer
# - Detect removed categories (404s)
# - Find URL changes (redirects)
# - Discover new categories
# - Create alerts for issues
```

### 3. Adaptive Scraping
```python
# Scrapers use dynamic selectors
value = await extract_with_fallback(
    html, 
    page_type='product',
    element_type='price'
)

# This will:
# - Get all configured selectors for price
# - Try each selector by priority
# - Track performance of each attempt
# - Return first successful extraction
# - Update selector statistics
```

### 4. Self-Healing
When selectors fail:
- System tracks failure rates
- Automatically deactivates poor performers
- Alerts created for manual review
- Can attempt to discover new selectors

## Benefits

### 1. **Reduced Maintenance**
- No code changes needed when websites update
- Automatic detection of broken scrapers
- Dynamic selector management through database

### 2. **Better Reliability**
- Multiple fallback selectors for each element
- Performance-based selector prioritization
- Automatic adaptation to minor changes

### 3. **Improved Visibility**
- Real-time monitoring of scraper health
- Category change tracking
- Performance metrics for optimization

### 4. **Scalability**
- Easy to add new retailers
- Share selectors across similar sites
- Centralized configuration management

## Usage Examples

### Adding a New Retailer
```python
# 1. Add retailer configuration
retailer_config = RetailerConfig(
    name="New Store",
    code="NS",
    base_url="https://newstore.com"
)

# 2. Discover categories
POST /api/categories/discover?retailer_code=NS

# 3. Configure selectors (or copy from similar retailer)
await config_manager.copy_selectors(
    from_retailer='HP',  # Copy from HomePro
    to_retailer='NS'
)

# 4. Start scraping with adaptive system
scraper = NewStoreScraper()  # Inherits AdaptiveScraperMixin
products = await scraper.scrape_category(category_url)
```

### Handling Website Changes
```python
# When a website updates their structure:

# 1. Monitor detects changes automatically
changes = GET /api/categories/changes?retailer_code=HP

# 2. Update selectors through API/database
new_selector = {
    "selector_type": "css",
    "selector_value": "span.new-price-class",
    "priority": 1
}

# 3. Old selectors automatically deprioritized
# 4. Scraping continues with new selectors
```

## Next Steps

### Immediate Actions
1. Run the database migration script
2. Start category discovery for each retailer
3. Configure initial selectors
4. Set up monitoring schedule

### Future Enhancements
1. **Machine Learning** - Train models to recognize elements
2. **Visual Selectors** - Use computer vision for resilient extraction
3. **Cross-Retailer Learning** - Apply patterns across sites
4. **A/B Testing** - Gradually test new selectors
5. **Community Selectors** - Share working selectors

## Monitoring Dashboard Integration

The monitoring dashboard at `/monitoring` now includes:
- Category health metrics
- Recent category changes
- Selector performance stats
- Active alerts

## Conclusion

This adaptive scraping system transforms brittle, maintenance-heavy scrapers into resilient, self-healing data collection pipelines. By separating configuration from code and adding intelligent monitoring, we've created a system that can handle the dynamic nature of modern websites while maintaining data quality and completeness.