# Troubleshooting Guide

## Common Issues

### 1. ModuleNotFoundError: No module named 'httpx'

**Problem**: Running commands without activating the virtual environment.

**Solution**:
```bash
cd "/Users/chongraktanaka/Documents/Project/ris data scrap"
source venv/bin/activate
python3 scrape.py [command]
```

### 2. zsh: command not found: python

**Problem**: macOS uses `python3` instead of `python`.

**Solution**: Always use `python3` command:
```bash
python3 setup.py
python3 scrape.py stats
python3 -m app.test_connection
```

### 3. Firecrawl API Errors

**Problem**: `extractorOptions.extractionSchema must be an object`

**Solution**: This has been fixed in the latest code. Make sure you're using the updated version.

### 4. Connection Errors

**Problem**: Cannot connect to Supabase or Firecrawl.

**Solution**:
1. Check your `.env` file has correct credentials
2. Test connections: `python3 -m app.test_connection`
3. Verify your API keys are valid

### 5. Crawl Timeout

**Problem**: URL discovery takes too long and times out.

**Solution**:
- Reduce `--max-pages` parameter
- Start with smaller categories
- Example: `python3 scrape.py discover [URL] --max-pages 2`

### 6. No Products Found

**Problem**: Discover command returns 0 URLs.

**Possible Causes**:
- The category page has no products
- The URL pattern changed
- Rate limiting

**Solution**:
- Try a different category URL
- Check if HomePro website structure changed
- Wait a few minutes if rate limited

## Quick Checklist

Before running any command:
- [ ] Navigate to project directory: `cd "/Users/chongraktanaka/Documents/Project/ris data scrap"`
- [ ] Activate virtual environment: `source venv/bin/activate`
- [ ] Use `python3` not `python`
- [ ] Check `.env` file exists with credentials
- [ ] Test connections first: `python3 -m app.test_connection`

## Getting Help

1. Check logs for detailed error messages
2. Run with smaller batches first
3. Verify HomePro website is accessible
4. Check Firecrawl API status