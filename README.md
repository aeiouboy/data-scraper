# HomePro Scraper

Web scraping system for HomePro products using Firecrawl API and Supabase.

## Features

- 🚀 High-performance scraping with Firecrawl API
- 📊 Real-time data storage in Supabase
- 🔄 Automatic price tracking and history
- 🎯 Smart rate limiting and retry logic
- 📈 Built-in analytics and monitoring
- 🇹🇭 Thai language support

## Quick Start

### 1. Setup

```bash
# Install dependencies
python3 setup.py

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Configure

1. Copy `.env.example` to `.env`
2. Add your credentials:
   - Supabase URL and keys
   - Firecrawl API key

### 3. Initialize Database

Run the SQL script in your Supabase SQL Editor:
```sql
-- Copy contents from scripts/create_schema.sql
```

### 4. Test Connection

```bash
python3 -m app.test_connection
```

## Usage

### CLI Commands

**Important**: Always activate the virtual environment first:
```bash
cd "/Users/chongraktanaka/Documents/Project/ris data scrap"
source venv/bin/activate
```

Then run commands using `python3`:
```bash
# Scrape a single product
python3 scrape.py product https://www.homepro.co.th/p/12345

# Scrape an entire category
python3 scrape.py category https://www.homepro.co.th/c/electrical --max-pages 5

# Discover product URLs
python3 scrape.py discover https://www.homepro.co.th/c/tools

# Show statistics
python3 scrape.py stats

# Search products
python3 scrape.py search "drill" --limit 20
```

### Python API

```python
from app.core.scraper import HomeProScraper

# Initialize scraper
scraper = HomeProScraper()

# Scrape single product
product = await scraper.scrape_single_product("https://www.homepro.co.th/p/12345")

# Scrape category
results = await scraper.scrape_category("https://www.homepro.co.th/c/electrical")
```

## Architecture

```
app/
├── core/
│   ├── scraper.py         # Main orchestrator
│   └── data_processor.py  # Data validation
├── services/
│   ├── firecrawl_client.py  # Firecrawl API
│   └── supabase_service.py  # Database operations
└── models/
    └── product.py         # Data models
```

## Performance

- **Scraping Speed**: 500+ products/hour
- **Success Rate**: >95% with retry logic
- **Rate Limiting**: 30 requests/minute (configurable)
- **Concurrent Scraping**: Up to 5 parallel requests

## Database Schema

### Products Table
- Product details (SKU, name, brand, category)
- Pricing information with history tracking
- Features and specifications (JSONB)
- Availability status

### Analytics Views
- `product_stats`: Overview statistics
- `daily_scrape_stats`: Daily performance metrics

## Monitoring

Track scraping performance with built-in analytics:
- Total products scraped
- Success/failure rates
- Price change alerts
- Category distribution

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
black app/
flake8 app/
mypy app/
```

## Deployment

### Docker
```bash
docker build -t homepro-scraper .
docker run -d --env-file .env homepro-scraper
```

### Production Checklist
- [ ] Set up Supabase RLS policies
- [ ] Configure monitoring alerts
- [ ] Set up backup schedules
- [ ] Deploy with proper secrets management

## License

MIT
