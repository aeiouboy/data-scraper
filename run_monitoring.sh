#!/bin/bash
# Script to run category monitoring

echo "🔍 Running Category Monitoring..."

# Monitor all retailers
echo "Monitoring all retailers..."
curl -X POST "http://localhost:8000/api/categories/monitor" -H "Content-Type: application/json"

# Or monitor specific retailer
# curl -X POST "http://localhost:8000/api/categories/monitor?retailer_code=HP"

echo -e "\n\n📊 Checking monitoring results..."
sleep 2

# Get recent changes
echo "Recent category changes (last 7 days):"
curl -X GET "http://localhost:8000/api/categories/changes?days=7" | python3 -m json.tool

echo -e "\n\n💚 Category health for HomePro:"
curl -X GET "http://localhost:8000/api/categories/health/HP" | python3 -m json.tool

echo -e "\n\n✅ Monitoring complete!"