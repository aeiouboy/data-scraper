"""Product-related fixtures for testing."""

import pytest
from datetime import datetime
from src.models.product import Product


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return [
        {
            "retailer_code": "homepro",
            "sku": "HP001",
            "name": "Bosch Professional Drill GBM 13 RE",
            "current_price": 2990.0,
            "original_price": 3590.0,
            "brand": "Bosch",
            "category": "Power Tools/Drills",
            "specifications": {
                "power": "600W",
                "chuck_size": "13mm",
                "speed": "0-2800 rpm"
            },
            "image_url": "https://example.com/bosch-drill.jpg",
            "product_url": "https://homepro.co.th/p/1234567",
            "in_stock": True,
            "is_promotion": True
        },
        {
            "retailer_code": "megahome",
            "sku": "MH001",
            "name": "บ๊อช สว่านไฟฟ้า รุ่น GBM 13 RE",
            "current_price": 3150.0,
            "original_price": 3590.0,
            "brand": "Bosch",
            "category": "เครื่องมือไฟฟ้า/สว่าน",
            "specifications": {
                "กำลังไฟ": "600 วัตต์",
                "ขนาดหัวจับ": "13 มม.",
                "ความเร็ว": "0-2800 รอบ/นาที"
            },
            "image_url": "https://example.com/bosch-drill-th.jpg",
            "product_url": "https://megahome.co.th/product/bosch-drill",
            "in_stock": True,
            "is_promotion": False
        },
        {
            "retailer_code": "thaiwatsadu",
            "sku": "TWD001",
            "name": "STANLEY Hammer 16oz Fiberglass",
            "current_price": 299.0,
            "original_price": 399.0,
            "brand": "Stanley",
            "category": "Hand Tools/Hammers",
            "specifications": {
                "weight": "16 oz",
                "handle_material": "Fiberglass",
                "head_material": "Steel"
            },
            "image_url": "https://example.com/stanley-hammer.jpg",
            "product_url": "https://thaiwatsadu.com/th/product/stanley-hammer",
            "in_stock": False,
            "is_promotion": True
        }
    ]


@pytest.fixture
def matching_product_pairs():
    """Product pairs for matching tests."""
    return [
        {
            "product1": {
                "name": "Bosch GBM 13 RE Professional Drill 600W",
                "brand": "Bosch",
                "sku": "GBM13RE",
                "specifications": {"power": "600W", "speed": "2800rpm"}
            },
            "product2": {
                "name": "บ๊อช สว่านไฟฟ้า โปร GBM 13 RE 600 วัตต์",
                "brand": "BOSCH",
                "sku": "GBM-13-RE",
                "specifications": {"กำลัง": "600 วัตต์", "ความเร็ว": "2800 รอบ/นาที"}
            },
            "expected_score": 0.95,
            "should_match": True
        },
        {
            "product1": {
                "name": "Makita Cordless Drill DF457D",
                "brand": "Makita",
                "sku": "DF457D",
                "specifications": {"voltage": "18V", "torque": "42Nm"}
            },
            "product2": {
                "name": "DeWalt Cordless Drill DCD777",
                "brand": "DeWalt",
                "sku": "DCD777",
                "specifications": {"voltage": "20V", "torque": "65Nm"}
            },
            "expected_score": 0.3,
            "should_match": False
        }
    ]


@pytest.fixture
def price_history_data():
    """Sample price history data."""
    return [
        {"price": 2990.0, "days_ago": 0},
        {"price": 3190.0, "days_ago": 1},
        {"price": 3190.0, "days_ago": 2},
        {"price": 3590.0, "days_ago": 3},
        {"price": 3590.0, "days_ago": 7},
        {"price": 3590.0, "days_ago": 14},
        {"price": 2990.0, "days_ago": 30},
    ]


@pytest.fixture
def category_mapping():
    """Category mapping for different retailers."""
    return {
        "homepro": {
            "power_tools": "เครื่องมือไฟฟ้า",
            "hand_tools": "เครื่องมือช่าง",
            "bathroom": "ห้องน้ำ",
            "tiles": "กระเบื้อง"
        },
        "megahome": {
            "เครื่องมือไฟฟ้า": "power-tools",
            "เครื่องมือช่าง": "hand-tools",
            "สุขภัณฑ์": "bathroom",
            "กระเบื้อง": "tiles"
        }
    }


@pytest.fixture
def brand_aliases():
    """Common brand aliases for testing."""
    return {
        "bosch": ["BOSCH", "บ๊อช", "บ๊อซ", "โบ๊ช"],
        "makita": ["MAKITA", "มากิต้า", "มาคิต้า"],
        "stanley": ["STANLEY", "สแตนเล่ย์", "สแตนลีย์"],
        "3m": ["3M", "ทรีเอ็ม", "สามเอ็ม"],
        "dewalt": ["DEWALT", "ดีวอลท์", "ดีวอลต์"]
    }