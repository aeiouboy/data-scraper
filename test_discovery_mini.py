"""
Mini test for category discovery - limited scope
"""
import asyncio
from app.core.category_explorer import CategoryExplorer

async def test_mini_discovery():
    """Test discovery with very limited scope"""
    print("🔍 Testing Category Discovery (Mini)...")
    
    explorer = CategoryExplorer()
    
    # Test with minimal parameters
    result = await explorer.discover_all_categories(
        retailer_code='HP',
        max_depth=1,      # Only root level
        max_categories=5  # Only 5 categories
    )
    
    print(f"\n✅ Discovery Results:")
    print(f"   - Categories found: {result['discovered_count']}")
    print(f"   - Categories saved: {result['saved_count']}")
    print(f"   - Duration: {result['duration_seconds']:.2f}s")
    
    if result['category_tree']:
        print(f"\n📂 Discovered Categories:")
        for cat in result['category_tree'][:5]:
            print(f"   - {cat['name']} ({cat['code']})")

if __name__ == "__main__":
    asyncio.run(test_mini_discovery())