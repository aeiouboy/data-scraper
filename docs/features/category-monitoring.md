# Category Monitoring System

## Overview

The Category Monitoring System is an adaptive scraping solution that automatically discovers, tracks, and maintains product categories across multiple Thai retailers (HomePro, Thai Watsadu, Global House, etc.). It ensures your scraping system stays current with website changes without manual intervention.

## Key Features

### 🔍 Auto-Discovery
- Automatically discovers categories from retailer websites
- Builds hierarchical category trees (parent/child relationships)
- Identifies new categories as retailers add them

### 📊 Health Monitoring
- Real-time health scores (0-100) for each retailer's categories
- Tracks active vs. inactive categories
- Monitors selector performance and success rates

### 🔄 Change Detection
- Detects new categories added by retailers
- Identifies removed or relocated categories
- Tracks URL changes and structure modifications
- Creates alerts for critical changes

### 🛠️ Self-Healing
- Automatically updates CSS/XPath selectors when websites change
- Deactivates failing selectors to prevent errors
- Maintains scraping continuity without code changes

## Quick Start

### 1. Start the API Server
```bash
cd "/Users/chongraktanaka/Documents/Project/ris data scrap"
source venv/bin/activate
python3 run_api.py
```

### 2. Access the Monitoring Dashboard
Open your browser to: `http://localhost:3000/monitoring`

### 3. Run Category Monitoring

#### Option A: Via Web UI
1. Navigate to the Monitoring page
2. Find the "Category Monitoring" section
3. Click the **"Start Monitor"** button

#### Option B: Via API
```bash
# Monitor all retailers
curl -X POST "http://localhost:8000/api/categories/monitor"

# Monitor specific retailer
curl -X POST "http://localhost:8000/api/categories/monitor?retailer_code=HP"
```

#### Option C: Via Python Script
```bash
python3 quick_monitor.py
```

## Understanding the Dashboard

### Category Health Overview
- **Total Categories**: Number of categories per retailer
- **Category Changes**: Recent additions/removals (7-day window)
- **Auto-Discovered**: Percentage found automatically vs. manually added
- **Categories with Issues**: Count needing attention

### Category Health by Retailer Table
| Column | Description |
|--------|-------------|
| Retailer | Retailer name and code |
| Health Score | Overall health (0-100%, color-coded) |
| Total Categories | Total category count |
| Categories with Issues | Number of problematic categories |
| Auto-Discovered | Percentage discovered automatically |
| Last Update | When categories were last verified |

### Recent Category Changes
Shows the latest category modifications:
- 📈 Price increases
- 📉 Price decreases  
- 🆕 New products added
- ❌ Products discontinued

## API Endpoints

### Monitoring Operations
```bash
# Trigger monitoring
POST /api/categories/monitor
Query params: retailer_code (optional)

# Get category health
GET /api/categories/health/{retailer_code}

# Get recent changes
GET /api/categories/changes
Query params: days (default: 7), retailer_code (optional)

# Get category tree
GET /api/categories/tree/{retailer_code}
```

### Category Management
```bash
# Verify specific category
POST /api/categories/verify/{category_id}

# Trigger discovery
POST /api/categories/discover
Body: { "retailer_code": "HP", "max_depth": 3 }

# Get statistics
GET /api/categories/stats
```

## How It Works

### 1. Discovery Phase
```python
# The system visits retailer homepage
# Extracts category links using configured selectors
# Follows links recursively to build category tree
# Saves discovered categories to database
```

### 2. Monitoring Phase
```python
# Compares current website structure with database
# Identifies changes (new/removed/modified)
# Calculates health scores
# Generates alerts for critical issues
```

### 3. Adaptation Phase
```python
# Updates selectors based on success rates
# Deactivates failing selectors
# Learns new patterns from successful scrapes
# Maintains scraping continuity
```

## Configuration

### Monitoring Schedule
Default: Runs every 6 hours
```python
# Customize in app/config/settings.py
CATEGORY_MONITOR_SCHEDULE = "0 */6 * * *"  # Cron format
```

### Alert Thresholds
```python
# Health score below this triggers alerts
HEALTH_SCORE_WARNING_THRESHOLD = 70
HEALTH_SCORE_CRITICAL_THRESHOLD = 50

# Category change thresholds
MAX_CATEGORIES_REMOVED_WARNING = 5
MAX_CATEGORIES_REMOVED_CRITICAL = 10
```

### Retailer Configuration
Each retailer has specific selectors in `app/config/retailers.py`:
```python
RETAILER_CONFIGS = {
    "HP": {
        "name": "HomePro",
        "base_url": "https://www.homepro.co.th",
        "category_selectors": {
            "menu": "nav.menu a.category-link",
            "sidebar": "div.category-list a"
        }
    }
}
```

## Troubleshooting

### Common Issues

#### No categories found
- Check if retailer website is accessible
- Verify selectors in retailer configuration
- Check rate limiting settings

#### Low health scores
- Review recent category changes
- Check selector performance metrics
- Verify website hasn't undergone major redesign

#### API errors
- Ensure database migrations are applied
- Check API server logs: `tail -f logs/api.log`
- Verify Supabase connection

### Useful Commands

```bash
# Check monitoring status
curl http://localhost:8000/api/monitoring/health

# View recent alerts
curl http://localhost:8000/api/categories/alerts

# Force full scan
curl -X POST "http://localhost:8000/api/categories/monitor?force_full_scan=true"

# Export category tree
curl http://localhost:8000/api/categories/tree/HP > hp_categories.json
```

## Advanced Usage

### Custom Monitoring Rules
Create custom monitoring rules for specific categories:
```python
from app.services.category_monitor import CategoryMonitor

monitor = CategoryMonitor()
monitor.add_rule({
    "category_path": "home-improvement/tiles",
    "min_products": 100,
    "max_price_change": 0.2,  # 20%
    "alert_email": "admin@example.com"
})
```

### Webhook Integration
Configure webhooks for real-time alerts:
```python
# In app/config/settings.py
WEBHOOK_ENDPOINTS = {
    "category_changes": "https://your-webhook.com/categories",
    "health_alerts": "https://your-webhook.com/alerts"
}
```

### Performance Optimization
For large retailers with many categories:
```python
# Increase parallel discovery workers
CATEGORY_DISCOVERY_WORKERS = 5

# Adjust rate limiting
REQUESTS_PER_MINUTE = 30

# Enable caching
CATEGORY_CACHE_TTL = 3600  # 1 hour
```

## Best Practices

1. **Regular Monitoring**: Run at least every 6-12 hours
2. **Review Alerts**: Check critical alerts daily
3. **Update Selectors**: When health scores drop, review and update selectors
4. **Backup Categories**: Export category trees periodically
5. **Monitor Performance**: Track response times and success rates

## Database Schema

Key tables used by the monitoring system:
- `retailer_categories`: Stores category hierarchy
- `category_changes`: Tracks all modifications
- `scraper_selectors`: Dynamic selector configuration
- `selector_performance`: Success rate metrics
- `scraper_alerts`: Generated alerts

## Integration with Scraping

The monitoring system integrates seamlessly with product scraping:
1. Discovers categories → Provides URLs for scraping
2. Monitors health → Ensures scraping reliability
3. Detects changes → Updates scraping configuration
4. Generates alerts → Notifies about issues

## Future Enhancements

- Machine learning for pattern recognition
- Automatic selector generation
- Cross-retailer category matching
- Historical trend analysis
- Mobile app notifications

---

For technical implementation details, see:
- [Architecture Documentation](ARCHITECTURE.md)
- [API Documentation](docs/api/categories.md)
- [Database Schema](scripts/create_adaptive_scraping_schema.sql)