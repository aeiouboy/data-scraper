"""
Test script for product matching algorithm
"""
import asyncio
from datetime import datetime
from decimal import Decimal
from app.core.product_matcher import ProductMatcher
from app.models.product import Product


async def test_product_matching():
    """Test the product matching algorithm with sample products"""
    
    # Create sample products from different retailers
    sample_products = [
        # Samsung TV - should match across retailers
        Product(
            sku="HP-TV001",
            name="Samsung Smart TV 55 นิ้ว รุ่น UA55AU7700",
            brand="Samsung",
            category="TV & Audio",
            current_price=Decimal("19900"),
            retailer_code="HP",
            retailer_name="HomePro",
            unified_category="electronics"
        ),
        Product(
            sku="TWD-1234",
            name="ทีวี Samsung 55\" UA55AU7700 Smart TV",
            brand="ซัมซุง",
            category="เครื่องใช้ไฟฟ้า",
            current_price=Decimal("18990"),
            retailer_code="TWD",
            retailer_name="Thai Watsadu",
            unified_category="electronics"
        ),
        Product(
            sku="GH-SAM55",
            name="SAMSUNG UA55AU7700 Smart TV 55 inch",
            brand="SAMSUNG",
            category="Electronics",
            current_price=Decimal("19500"),
            retailer_code="GH",
            retailer_name="Global House",
            unified_category="electronics"
        ),
        
        # LG Air Conditioner - should match
        Product(
            sku="HP-AC001",
            name="LG แอร์ Inverter 12000 BTU รุ่น IG13R.N10",
            brand="LG",
            category="Air Conditioner",
            current_price=Decimal("15900"),
            retailer_code="HP",
            retailer_name="HomePro",
            unified_category="cooling"
        ),
        Product(
            sku="MH-LG12K",
            name="เครื่องปรับอากาศ LG Inverter IG13R.N10 12000BTU",
            brand="แอลจี",
            category="เครื่องปรับอากาศ",
            current_price=Decimal("15500"),
            retailer_code="MH",
            retailer_name="MegaHome",
            unified_category="cooling"
        ),
        
        # Kohler faucet - should match
        Product(
            sku="BT-KOH123",
            name="KOHLER ก๊อกอ่างล้างหน้า รุ่น K-5241T-4-CP",
            brand="KOHLER",
            category="สุขภัณฑ์",
            current_price=Decimal("3290"),
            retailer_code="BT",
            retailer_name="Boonthavorn",
            unified_category="bathroom"
        ),
        Product(
            sku="HP-BATH99",
            name="ก๊อกน้ำ Kohler K-5241T-4-CP สำหรับอ่างล้างหน้า",
            brand="Kohler",
            category="Bathroom",
            current_price=Decimal("3350"),
            retailer_code="HP",
            retailer_name="HomePro",
            unified_category="bathroom"
        ),
        
        # Unmatched products
        Product(
            sku="DH-TOOL1",
            name="Bosch สว่านไร้สาย 18V",
            brand="Bosch",
            category="Tools",
            current_price=Decimal("2990"),
            retailer_code="DH",
            retailer_name="DoHome",
            unified_category="tools"
        ),
        Product(
            sku="TWD-FUR99",
            name="โต๊ะทำงาน ไม้ MDF 120x60",
            brand=None,
            category="Furniture",
            current_price=Decimal("1590"),
            retailer_code="TWD",
            retailer_name="Thai Watsadu",
            unified_category="furniture"
        ),
    ]
    
    # Initialize matcher
    matcher = ProductMatcher()
    
    print("\n" + "="*80)
    print("Product Matching Test")
    print("="*80)
    print(f"\nTesting with {len(sample_products)} products from different retailers\n")
    
    # Find matches
    result = await matcher.find_matches(sample_products)
    
    print(f"Match Results:")
    print(f"- Total products: {result.total_products}")
    print(f"- Match groups found: {len(result.matched_groups)}")
    print(f"- Unmatched products: {len(result.unmatched_products)}")
    print(f"- Match rate: {result.match_rate:.1%}")
    
    # Display match groups
    print("\n" + "-"*80)
    print("Matched Product Groups:")
    print("-"*80)
    
    for i, group in enumerate(result.matched_groups, 1):
        print(f"\nGroup {i} ({len(group)} products):")
        for product in group:
            print(f"  - [{product.retailer_code}] {product.name}")
            print(f"    Brand: {product.brand}, Price: ฿{product.current_price}")
        
        # Show match analysis for first pair
        if len(group) >= 2:
            match_score = matcher._calculate_match_score(group[0], group[1])
            print(f"\n  Match Analysis (first pair):")
            print(f"    - Name similarity: {match_score.name_similarity:.2f}")
            print(f"    - SKU similarity: {match_score.sku_similarity:.2f}")
            print(f"    - Brand similarity: {match_score.brand_similarity:.2f}")
            print(f"    - Price similarity: {match_score.price_similarity:.2f}")
            print(f"    - Overall score: {match_score.overall_score:.2f}")
            print(f"    - Confidence: {match_score.match_confidence}")
    
    # Display unmatched products
    if result.unmatched_products:
        print("\n" + "-"*80)
        print("Unmatched Products:")
        print("-"*80)
        for product in result.unmatched_products:
            print(f"  - [{product.retailer_code}] {product.name}")
    
    print("\n" + "="*80)
    print("Test completed!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_product_matching())