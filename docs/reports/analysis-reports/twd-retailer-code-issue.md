# Thai Watsadu "Only 1 Product" Issue - SOLVED

## Root Cause
The issue is **NOT** with the Thai Watsadu scraper itself. The scraper works perfectly. The problem is that the **wrong scraper (HomePro) is being used** for Thai Watsadu URLs.

## Evidence from Logs
```
2025-07-09 17:59:28,753 | INFO | src.scrapers.homepro_scraper | Discovered 1 product URLs
2025-07-09 17:59:28,753 | INFO | src.scrapers.homepro_scraper | Found 1 products to scrape
```

Notice it says `homepro_scraper` not `thaiwatsadu_scraper`!

## Why This Happens

When creating a scraping job via the API without specifying `retailer_code`, the system defaults to HomePro scraper:

```python
# From src/api/routers/scraping.py
if retailer_code:
    scraper = get_scraper_for_retailer(retailer_code)
else:
    # Default to HomePro for backward compatibility
    scraper = HomeProScraper()  # ← This is the problem!
```

## The Solution

### ✅ When Using the API

Always include `retailer_code` in your request:

```json
POST /api/scraping/jobs
{
    "job_type": "category",
    "target_url": "https://www.thaiwatsadu.com/en/category/เครื่องปรับอากาศติดผนัง-630201",
    "retailer_code": "TWD",  // ← REQUIRED!
    "max_pages": 1
}
```

### ✅ When Using Scripts Directly

```python
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper

# Use the Thai Watsadu scraper directly
scraper = ThaiWatsaduScraper()
result = await scraper.scrape_category(category_url)
```

## Retailer Codes Reference

| Retailer | Code | Scraper Class |
|----------|------|---------------|
| HomePro | HP | HomeProScraper |
| Thai Watsadu | TWD | ThaiWatsaduScraper |
| Global House | GH | GlobalHouseScraper |
| DoHome | DH | DoHomeScraper |
| Boonthavorn | BT | BoonthavornScraper |
| MegaHome | MH | MegaHomeScraper |

## Quick Test

To verify Thai Watsadu scraping works:

```bash
# Run the proper scraping script
python scripts/scraping/scrape_twd_category_properly.py
```

## Common Mistakes

### ❌ Wrong: Missing retailer_code
```json
{
    "job_type": "category",
    "target_url": "https://www.thaiwatsadu.com/..."
    // Missing retailer_code - will use HomePro scraper!
}
```

### ❌ Wrong: Using Thai language URL
```json
{
    "job_type": "category",
    "target_url": "https://www.thaiwatsadu.com/th/category/...",
    "retailer_code": "TWD"
}
```

### ✅ Correct: English URL + retailer_code
```json
{
    "job_type": "category",
    "target_url": "https://www.thaiwatsadu.com/en/category/...",
    "retailer_code": "TWD"
}
```

## Summary

1. **The Thai Watsadu scraper works perfectly** - It discovers 48 products correctly
2. **The issue was using the wrong scraper** - HomePro scraper was being used instead
3. **Solution: Always specify `retailer_code: "TWD"`** when scraping Thai Watsadu
4. **Use English URLs** (`/en/category/...`) not Thai URLs (`/th/category/...`)

The "only 1 product found" was because HomePro's scraper doesn't understand Thai Watsadu's HTML structure!