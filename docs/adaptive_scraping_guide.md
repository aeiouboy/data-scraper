# Adaptive Scraping System Guide

This guide explains how to use the new adaptive scraping system that automatically discovers categories and adapts to website changes.

## Overview

The adaptive scraping system consists of several key components:

1. **Category Explorer** - Automatically discovers and maps category structures
2. **Category Monitor** - Detects changes in categories and website structure
3. **Scraper Configuration Manager** - Manages dynamic selectors for scraping
4. **API Endpoints** - RESTful API for managing the system

## Getting Started

### 1. Apply Database Schema

First, apply the new database schema to support adaptive scraping:

```bash
# Run the SQL script in Supabase
psql -h your-supabase-host -U postgres -d postgres -f scripts/create_adaptive_scraping_schema.sql
```

### 2. Discover Categories

Use the Category Explorer to automatically discover categories for a retailer:

```python
from app.core.category_explorer import CategoryExplorer

# Discover categories for HomePro
explorer = CategoryExplorer()
result = await explorer.discover_all_categories(
    retailer_code='HP',
    max_depth=3,
    max_categories=500
)

print(f"Discovered {result['discovered_count']} categories")
print(f"Category tree: {result['category_tree']}")
```

Or use the API endpoint:

```bash
# Trigger category discovery
curl -X GET "http://localhost:8000/api/categories/discover?retailer_code=HP&max_depth=3"

# Get category tree
curl -X GET "http://localhost:8000/api/categories/tree/HP"
```

### 3. Monitor for Changes

Set up monitoring to detect category changes:

```python
from app.services.category_monitor import CategoryMonitor

# Monitor all retailers
monitor = CategoryMonitor()
results = await monitor.monitor_all_retailers()

# Check specific retailer
retailer_results = await monitor.monitor_retailer('HP')
print(f"Found {retailer_results['change_count']} changes")
```

Or use the API:

```bash
# Trigger monitoring
curl -X POST "http://localhost:8000/api/categories/monitor"

# Get recent changes
curl -X GET "http://localhost:8000/api/categories/changes?days=7"
```

### 4. Configure Dynamic Selectors

The system uses dynamic selectors that can be updated without code changes:

```python
from app.core.scraper_config_manager import ScraperConfigManager

config_manager = ScraperConfigManager()

# Add a new selector
selector_id = await config_manager.add_selector(
    retailer_code='HP',
    page_type='product',
    element_type='product_name',
    selector_type='css',
    selector_value='h1.product-title',
    priority=1,
    validation_regex=r'^.{3,200}$',  # Name should be 3-200 chars
    transformation_rule='strip'
)

# Get selectors for scraping
selectors = await config_manager.get_selectors(
    retailer_code='HP',
    page_type='product',
    element_type='product_name'
)

# Try selectors in order of priority
for selector in selectors:
    try:
        value = extract_with_selector(html, selector)
        if value and selector.validate_value(value):
            final_value = selector.transform_value(value)
            # Record success
            await config_manager.record_selector_performance(
                selector.id, url, True, 
                execution_time_ms=10,
                extracted_value=final_value
            )
            break
    except Exception as e:
        # Record failure
        await config_manager.record_selector_performance(
            selector.id, url, False,
            error_message=str(e),
            error_type='extraction_failed'
        )
```

## Adaptive Scraping Flow

Here's how the complete adaptive scraping process works:

```python
import asyncio
from app.core.category_explorer import CategoryExplorer
from app.services.category_monitor import CategoryMonitor
from app.core.scraper_config_manager import ScraperConfigManager
from app.scrapers import get_scraper

async def adaptive_scraping_example():
    # 1. Discover categories
    explorer = CategoryExplorer()
    discovery = await explorer.discover_all_categories('HP')
    
    # 2. Get active categories
    db = SupabaseService()
    categories = db.client.table('retailer_categories')\
        .select('*')\
        .eq('retailer_code', 'HP')\
        .eq('is_active', True)\
        .execute()
    
    # 3. Get scraper with dynamic configuration
    scraper = get_scraper('HP')
    config_manager = ScraperConfigManager()
    
    # 4. Scrape each category with adaptive selectors
    for category in categories.data:
        print(f"Scraping category: {category['category_name']}")
        
        # Get product links using dynamic selectors
        selectors = await config_manager.get_selectors(
            'HP', 'category', 'product_link'
        )
        
        # Extract products
        products = []
        for selector in selectors:
            try:
                links = await scraper.extract_with_selector(
                    category['category_url'],
                    selector
                )
                if links:
                    products.extend(links)
                    break
            except:
                continue
        
        # Scrape each product with adaptive extraction
        for product_url in products[:10]:  # Sample
            product_data = {}
            
            # Extract each element with fallback selectors
            for element_type in ['product_name', 'price', 'image']:
                selectors = await config_manager.get_selectors(
                    'HP', 'product', element_type
                )
                
                for selector in selectors:
                    try:
                        value = await scraper.extract_with_selector(
                            product_url, selector
                        )
                        if value:
                            product_data[element_type] = value
                            break
                    except:
                        continue
            
            # Save product
            if product_data.get('product_name'):
                await db.upsert_product(product_data)
    
    # 5. Monitor for changes
    monitor = CategoryMonitor()
    changes = await monitor.monitor_retailer('HP')
    
    if changes['critical_changes'] > 0:
        print(f"WARNING: {changes['critical_changes']} critical changes detected!")

# Run the example
asyncio.run(adaptive_scraping_example())
```

## Handling Website Changes

When a website changes its structure, the system adapts automatically:

### 1. Automatic Detection

The Category Monitor runs periodically to detect:
- Removed categories (404 errors)
- Changed URLs (redirects)
- New categories
- Structure changes

### 2. Selector Fallback

When a selector fails:
1. The system tries the next selector by priority
2. Performance is tracked for each selector
3. Failing selectors are automatically deactivated
4. Alerts are created for manual review

### 3. Self-Healing

The system can attempt to find new selectors:
```python
# When all selectors fail
if not extracted_value:
    # Try to discover new selector
    from app.core.structure_analyzer import StructureAnalyzer
    analyzer = StructureAnalyzer()
    
    new_selector = await analyzer.discover_selector(
        html_content,
        element_type='product_name',
        example_values=['iPhone 14', 'Samsung Galaxy']  # Known product names
    )
    
    if new_selector:
        # Add as low-priority selector for testing
        await config_manager.add_selector(
            retailer_code='HP',
            page_type='product',
            element_type='product_name',
            selector_type=new_selector['type'],
            selector_value=new_selector['value'],
            priority=99,  # Low priority for testing
            is_auto_discovered=True,
            discovered_method='pattern_matching'
        )
```

## API Endpoints

### Category Management

```bash
# Discover categories
GET /api/categories/discover?retailer_code=HP&max_depth=3

# Get category tree
GET /api/categories/tree/HP

# Monitor for changes
POST /api/categories/monitor?retailer_code=HP

# Get recent changes
GET /api/categories/changes?days=7

# Verify specific category
POST /api/categories/verify/{category_id}

# Get category health metrics
GET /api/categories/health/HP

# Import categories manually
POST /api/categories/import
{
  "retailer_code": "HP",
  "categories": [
    {"code": "LIG", "name": "Lighting", "url": "https://..."},
    {"code": "PAI", "name": "Paint", "url": "https://..."}
  ]
}
```

### Monitoring Dashboard

View category health and changes in the monitoring dashboard:

1. Navigate to `/monitoring` in the frontend
2. Click on "Category Health" tab
3. View:
   - Active categories per retailer
   - Recent changes and alerts
   - Success rates by category
   - Categories needing verification

## Best Practices

1. **Regular Monitoring**
   - Run category discovery weekly
   - Monitor for changes daily
   - Review alerts promptly

2. **Selector Management**
   - Keep multiple selectors for critical elements
   - Test selectors regularly
   - Document selector patterns

3. **Change Response**
   - Investigate critical alerts immediately
   - Update selectors when websites change
   - Keep historical data for analysis

4. **Performance Optimization**
   - Use CSS selectors when possible (fastest)
   - Cache selector configurations
   - Batch category verifications

## Troubleshooting

### Common Issues

1. **Category Discovery Fails**
   ```python
   # Check retailer configuration
   config = retailer_manager.get_retailer('HP')
   print(f"Base URL: {config.base_url}")
   
   # Test with single category
   result = await explorer.discover_single_category('HP', category_url)
   ```

2. **Selectors Not Working**
   ```python
   # Check selector performance
   stats = await config_manager.get_selector_stats(selector_id, days=1)
   print(f"Success rate: {stats['success_rate']}%")
   
   # View recent failures
   failures = [p for p in stats['performances'] if not p['success']]
   ```

3. **Too Many Changes Detected**
   ```python
   # Adjust monitoring sensitivity
   monitor.check_for_changes(
       min_product_count_change=100,  # Ignore small changes
       url_change_threshold=0.9        # Allow minor URL variations
   )
   ```

## Future Enhancements

The adaptive scraping system can be extended with:

1. **Machine Learning** - Train models to recognize product elements
2. **Visual Recognition** - Use computer vision for element detection  
3. **Crowd Sourcing** - Allow users to submit working selectors
4. **A/B Testing** - Test new selectors gradually
5. **Cross-Retailer Learning** - Apply patterns learned from one site to others

## Conclusion

The adaptive scraping system makes your scrapers resilient to website changes while reducing manual maintenance. By automatically discovering categories, monitoring for changes, and managing dynamic selectors, you can maintain high-quality data collection even as websites evolve.