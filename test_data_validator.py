"""
Test script for data quality validation
"""
from decimal import Decimal
from app.core.data_validator import ProductValidator
from app.models.product import Product


def create_test_products():
    """Create test products with various quality issues"""
    return [
        # Good product
        Product(
            sku="HP-TV001",
            name="Samsung Smart TV 55 นิ้ว รุ่น UA55AU7700",
            brand="Samsung",
            category="TV & Audio",
            current_price=Decimal("19900"),
            original_price=Decimal("25900"),
            description="Smart TV with 4K resolution",
            features=["4K UHD", "Smart Hub", "HDR10+"],
            specifications={"Screen Size": "55 inches", "Resolution": "3840x2160"},
            availability="in_stock",
            images=[
                "https://www.homepro.co.th/images/tv1.jpg",
                "https://www.homepro.co.th/images/tv2.jpg"
            ],
            url="https://www.homepro.co.th/product/tv-samsung-ua55au7700",
            retailer_code="HP",
            retailer_name="HomePro",
            unified_category="electronics"
        ),
        
        # Missing required fields
        Product(
            sku="",  # Empty SKU
            name="Unknown Product",
            current_price=Decimal("1000"),
            url="",  # Empty URL
            retailer_code="TWD",
            retailer_name="Thai Watsadu",
            unified_category="other"
        ),
        
        # Invalid prices
        Product(
            sku="GH-INVALID1",
            name="Test Product with Bad Price",
            current_price=Decimal("-100"),  # Negative price
            original_price=Decimal("50"),   # Original less than current
            url="https://www.globalhouse.co.th/product/test",
            retailer_code="GH",
            retailer_name="Global House",
            unified_category="furniture"
        ),
        
        # Poor quality data
        Product(
            sku="123",  # Too short SKU
            name="TV",  # Too short name
            brand="S",  # Too short brand
            current_price=Decimal("5"),  # Suspiciously low price
            url="not-a-valid-url",  # Invalid URL
            retailer_code="MH",
            retailer_name="MegaHome",
            unified_category="invalid_category"  # Invalid category
        ),
        
        # Name with price
        Product(
            sku="DH-PRICE123",
            name="โต๊ะทำงาน ราคา 1,590 บาท ลดพิเศษ",  # Price in name
            current_price=Decimal("1590"),
            original_price=Decimal("2000"),
            url="https://www.dohome.co.th/product/table",
            retailer_code="DH",
            retailer_name="DoHome",
            unified_category="furniture",
            availability="invalid_status"  # Invalid availability
        ),
        
        # Suspicious discount
        Product(
            sku="BT-DISCOUNT99",
            name="Kohler Faucet Premium Model",
            brand="kohler",  # Not normalized
            current_price=Decimal("1000"),
            original_price=Decimal("50000"),  # 98% discount!
            url="https://www.boonthavorn.com/product/faucet",
            retailer_code="BT",
            retailer_name="Boonthavorn",
            unified_category="bathroom",
            images=["invalid-image-url", "also-invalid"]  # Invalid image URLs
        ),
        
        # Auto-generated SKU
        Product(
            sku="HP-generated-12345",  # Looks auto-generated
            name="Product with repeated charactersssssss",  # Repeated chars
            current_price=Decimal("999999999"),  # Very high price
            url="https://example.com/wrong-domain",  # Wrong domain
            retailer_code="HP",
            retailer_name="HomePro",
            unified_category="tools",
            specifications={"ราคา": "999", "": "empty"}  # Price in specs, empty value
        ),
    ]


def test_validation():
    """Test product validation"""
    print("\n" + "="*80)
    print("Data Quality Validation Test")
    print("="*80)
    
    validator = ProductValidator()
    products = create_test_products()
    
    # Validate individual products
    print("\n--- Individual Product Validation ---")
    for i, product in enumerate(products):
        result = validator.validate_product(product)
        
        print(f"\n[Product {i+1}] {product.name[:50]}...")
        print(f"  SKU: {product.sku}")
        print(f"  Valid: {result.is_valid}")
        print(f"  Quality Score: {result.quality_score:.2f}")
        print(f"  Issues: {result.get_error_count()} errors, {result.get_warning_count()} warnings")
        
        # Show errors
        errors = result.get_issues_by_severity('error')
        if errors:
            print("  Errors:")
            for error in errors[:3]:  # Show first 3
                print(f"    - {error.field}: {error.message}")
        
        # Show warnings
        warnings = result.get_issues_by_severity('warning')
        if warnings:
            print("  Warnings:")
            for warning in warnings[:3]:  # Show first 3
                print(f"    - {warning.field}: {warning.message}")
    
    # Batch validation
    print("\n\n--- Batch Validation Summary ---")
    batch_result = validator.validate_batch(products)
    
    summary = batch_result['summary']
    print(f"\nTotal Products: {summary['total_products']}")
    print(f"Valid Products: {summary['valid_products']} ({summary['validation_rate']:.1f}%)")
    print(f"Total Errors: {summary['total_errors']}")
    print(f"Total Warnings: {summary['total_warnings']}")
    print(f"Average Quality Score: {summary['average_quality_score']:.2f}")
    
    # Top issues
    print("\n--- Most Common Issues ---")
    for issue in batch_result['issue_breakdown'][:10]:
        print(f"\n{issue['field']}.{issue['type']} ({issue['severity']}): {issue['count']} occurrences")
        if issue['examples']:
            print("  Examples:")
            for ex in issue['examples']:
                print(f"    - {ex['product_sku']}: {ex['message']}")
    
    # Worst products
    print("\n--- Products with Lowest Quality ---")
    for prod in batch_result['worst_products'][:5]:
        print(f"  {prod['sku']} ({prod['retailer']}): Score {prod['quality_score']:.2f}, "
              f"{prod['errors']} errors, {prod['warnings']} warnings")
    
    print("\n" + "="*80)
    print("Validation test completed!")
    print("="*80)


def test_brand_normalization():
    """Test brand normalization suggestions"""
    print("\n--- Brand Normalization Test ---")
    
    validator = ProductValidator()
    
    test_brands = [
        "samsung", "SAMSUNG", "Samsung",
        "lg", "LG", "Lg",
        "kohler", "KOHLER", "Kohler",
        "american standard", "AMERICAN STANDARD", "American Standard"
    ]
    
    for brand in test_brands:
        product = Product(
            sku="TEST-BRAND",
            name="Test Product",
            brand=brand,
            current_price=Decimal("1000"),
            url="https://example.com/test",
            retailer_code="HP",
            retailer_name="HomePro",
            unified_category="other"
        )
        
        result = validator.validate_product(product)
        brand_issues = [i for i in result.issues if i.field == 'brand']
        
        if brand_issues:
            for issue in brand_issues:
                if issue.suggestion:
                    print(f"  '{brand}' -> {issue.suggestion}")


if __name__ == "__main__":
    test_validation()
    test_brand_normalization()