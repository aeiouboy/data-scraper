#!/bin/bash
# Quick activation script for HomePro scraper

echo "🚀 Activating HomePro Scraper environment..."
cd "/Users/chongraktanaka/Documents/Project/ris data scrap"
source venv/bin/activate
echo "✅ Environment activated!"
echo ""
echo "📋 Available commands:"
echo "  python3 scrape.py stats              - Show statistics"
echo "  python3 scrape.py discover [URL]     - Discover product URLs"
echo "  python3 scrape.py product [URL]      - Scrape single product"
echo "  python3 scrape.py search 'keyword'   - Search products"
echo ""
echo "💡 Tip: Always use python3, not python"