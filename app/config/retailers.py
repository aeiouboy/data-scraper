"""
Multi-retailer configuration system for Thai home improvement stores
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field


class RetailerType(Enum):
    HOMEPRO = "homepro"
    TWD = "twd"
    GLOBAL_HOUSE = "global_house"
    DOHOME = "dohome"
    BOONTHAVORN = "boonthavorn"
    MEGAHOME = "megahome"


@dataclass
class RetailerConfig:
    """Configuration for each retailer"""
    
    # Basic Info
    name: str
    code: str
    type: RetailerType
    base_url: str
    
    # Product Discovery
    category_urls: List[str] = field(default_factory=list)
    product_url_patterns: List[str] = field(default_factory=list)
    estimated_products: int = 0
    
    # Scraping Configuration
    rate_limit_delay: float = 1.0
    max_concurrent: int = 5
    retry_attempts: int = 3
    
    # Data Extraction Patterns
    category_mapping: Dict[str, str] = field(default_factory=dict)
    url_patterns: Dict[str, str] = field(default_factory=dict)
    selectors: Dict[str, str] = field(default_factory=dict)
    
    # Market Info
    market_position: str = ""
    focus_categories: List[str] = field(default_factory=list)
    price_volatility: str = "medium"  # low, medium, high
    
    def get_monitoring_tier(self, product_price: float, category: str) -> str:
        """Determine monitoring tier based on retailer-specific criteria"""
        if self.type == RetailerType.HOMEPRO:
            if product_price > 10000: return "ultra_critical"
            elif product_price > 3000: return "high_value"
            elif product_price > 1000: return "standard"
            else: return "low_priority"
        elif self.type == RetailerType.GLOBAL_HOUSE:
            # Higher thresholds due to premium positioning
            if product_price > 15000: return "ultra_critical"
            elif product_price > 5000: return "high_value"
            elif product_price > 2000: return "standard"
            else: return "low_priority"
        else:
            # Standard thresholds for other retailers
            if product_price > 8000: return "ultra_critical"
            elif product_price > 2500: return "high_value"
            elif product_price > 800: return "standard"
            else: return "low_priority"


# Retailer Configurations
RETAILER_CONFIGS = {
    RetailerType.HOMEPRO: RetailerConfig(
        name="HomePro",
        code="HP",
        type=RetailerType.HOMEPRO,
        base_url="https://www.homepro.co.th",
        category_urls=[
            "https://www.homepro.co.th/c/LIG",  # Lighting
            "https://www.homepro.co.th/c/PAI",  # Paint
            "https://www.homepro.co.th/c/FUR",  # Furniture
            "https://www.homepro.co.th/c/APP",  # Appliances
            "https://www.homepro.co.th/c/TVA",  # TV/Audio
            "https://www.homepro.co.th/c/KIT",  # Kitchen
            "https://www.homepro.co.th/c/BAT",  # Bathroom
            "https://www.homepro.co.th/c/HHP",  # Household
            "https://www.homepro.co.th/c/CON",  # Construction
            "https://www.homepro.co.th/c/ELT",  # Electronics
            "https://www.homepro.co.th/c/DOW",  # Doors/Windows
            "https://www.homepro.co.th/c/TOO",  # Tools
            "https://www.homepro.co.th/c/OUT",  # Outdoor
            "https://www.homepro.co.th/c/BED",  # Bedroom
            "https://www.homepro.co.th/c/SPO",  # Sports
            "https://www.homepro.co.th/c/BEA",  # Beauty
            "https://www.homepro.co.th/c/MOM",  # Mom & Baby
            "https://www.homepro.co.th/c/HEA",  # Health
            "https://www.homepro.co.th/c/PET",  # Pet
            "https://www.homepro.co.th/c/ATM",  # Automotive
            "https://www.homepro.co.th/c/GAR",  # Garden
            "https://www.homepro.co.th/c/OFF",  # Office
            "https://www.homepro.co.th/c/CLO",  # Cleaning
        ],
        estimated_products=68500,
        rate_limit_delay=1.0,
        max_concurrent=5,
        category_mapping={
            'LIG': 'โคมไฟและหลอดไฟ',
            'PAI': 'สีและอุปกรณ์ทาสี',
            'FUR': 'เฟอร์นิเจอร์',
            'APP': 'เครื่องใช้ไฟฟ้า',
            'TVA': 'ทีวีและเครื่องเสียง',
            'KIT': 'ห้องครัว',
            'BAT': 'ห้องน้ำ',
            'HHP': 'ของใช้ในบ้าน',
            'CON': 'วัสดุก่อสร้าง',
            'ELT': 'อิเล็กทรอนิกส์',
            'DOW': 'ประตูและหน้าต่าง',
            'TOO': 'เครื่องมือ',
            'OUT': 'ของใช้กลางแจ้ง',
            'BED': 'ห้องนอน',
            'SPO': 'กีฬา',
            'BEA': 'ความงาม',
            'MOM': 'แม่และเด็ก',
            'HEA': 'สุขภาพ',
            'PET': 'สัตว์เลี้ยง',
            'ATM': 'ยานยนต์',
            'GAR': 'สวน',
            'OFF': 'สำนักงาน',
            'CLO': 'ทำความสะอาด',
        },
        market_position="Market Leader",
        focus_categories=["Appliances", "Furniture", "Construction"],
        price_volatility="medium"
    ),
    
    RetailerType.TWD: RetailerConfig(
        name="Thai Watsadu",
        code="TWD",
        type=RetailerType.TWD,
        base_url="https://www.thaiwatsadu.com",
        category_urls=[
            "https://www.thaiwatsadu.com/th/c/construction-materials",
            "https://www.thaiwatsadu.com/th/c/tools-hardware",
            "https://www.thaiwatsadu.com/th/c/electrical-lighting",
            "https://www.thaiwatsadu.com/th/c/plumbing-bathroom",
            "https://www.thaiwatsadu.com/th/c/paint-coating",
            "https://www.thaiwatsadu.com/th/c/flooring-tile",
            "https://www.thaiwatsadu.com/th/c/roofing",
            "https://www.thaiwatsadu.com/th/c/doors-windows",
            "https://www.thaiwatsadu.com/th/c/garden-outdoor",
            "https://www.thaiwatsadu.com/th/c/safety-security",
        ],
        estimated_products=100000,
        rate_limit_delay=1.5,
        max_concurrent=3,
        market_position="Construction Specialist",
        focus_categories=["Construction", "Tools", "Electrical"],
        price_volatility="low"
    ),
    
    RetailerType.GLOBAL_HOUSE: RetailerConfig(
        name="Global House",
        code="GH",
        type=RetailerType.GLOBAL_HOUSE,
        base_url="https://www.globalhouse.co.th",
        category_urls=[
            "https://www.globalhouse.co.th/furniture",
            "https://www.globalhouse.co.th/home-decor",
            "https://www.globalhouse.co.th/lighting",
            "https://www.globalhouse.co.th/kitchen-dining",
            "https://www.globalhouse.co.th/bathroom",
            "https://www.globalhouse.co.th/bedroom",
            "https://www.globalhouse.co.th/living-room",
            "https://www.globalhouse.co.th/outdoor",
            "https://www.globalhouse.co.th/office",
            "https://www.globalhouse.co.th/storage",
        ],
        estimated_products=300000,
        rate_limit_delay=2.0,
        max_concurrent=4,
        market_position="Premium Home & Living",
        focus_categories=["Furniture", "Home Decor", "Premium Living"],
        price_volatility="high"
    ),
    
    RetailerType.DOHOME: RetailerConfig(
        name="DoHome",
        code="DH",
        type=RetailerType.DOHOME,
        base_url="https://www.dohome.co.th",
        category_urls=[
            "https://www.dohome.co.th/hardware-tools",
            "https://www.dohome.co.th/electrical",
            "https://www.dohome.co.th/plumbing",
            "https://www.dohome.co.th/paint",
            "https://www.dohome.co.th/building-materials",
            "https://www.dohome.co.th/garden",
            "https://www.dohome.co.th/automotive",
            "https://www.dohome.co.th/household",
        ],
        estimated_products=200000,
        rate_limit_delay=1.0,
        max_concurrent=5,
        market_position="Value Hardware Store",
        focus_categories=["Hardware", "Tools", "DIY"],
        price_volatility="low"
    ),
    
    RetailerType.BOONTHAVORN: RetailerConfig(
        name="Boonthavorn",
        code="BT",
        type=RetailerType.BOONTHAVORN,
        base_url="https://www.boonthavorn.com",
        category_urls=[
            "https://www.boonthavorn.com/ceramic-tile",
            "https://www.boonthavorn.com/sanitary-ware",
            "https://www.boonthavorn.com/kitchen",
            "https://www.boonthavorn.com/bathroom",
            "https://www.boonthavorn.com/flooring",
            "https://www.boonthavorn.com/doors-windows",
            "https://www.boonthavorn.com/lighting",
        ],
        estimated_products=50000,
        rate_limit_delay=1.5,
        max_concurrent=3,
        market_position="Ceramic & Sanitary Specialist",
        focus_categories=["Tiles", "Bathroom", "Kitchen"],
        price_volatility="medium"
    ),
    
    RetailerType.MEGAHOME: RetailerConfig(
        name="MegaHome",
        code="MH",
        type=RetailerType.MEGAHOME,
        base_url="https://www.megahome.co.th",
        category_urls=[
            "https://www.megahome.co.th/building-materials",
            "https://www.megahome.co.th/tools-hardware",
            "https://www.megahome.co.th/electrical-plumbing",
            "https://www.megahome.co.th/paint-coating",
            "https://www.megahome.co.th/roofing",
            "https://www.megahome.co.th/flooring",
            "https://www.megahome.co.th/garden-outdoor",
            "https://www.megahome.co.th/safety-equipment",
        ],
        estimated_products=100000,
        rate_limit_delay=1.2,
        max_concurrent=4,
        market_position="Building Materials Specialist",
        focus_categories=["Construction", "Hardware", "Industrial"],
        price_volatility="low"
    )
}


class RetailerManager:
    """Manages multiple retailer configurations and operations"""
    
    def __init__(self):
        self.retailers = RETAILER_CONFIGS
    
    def get_retailer(self, retailer_type: RetailerType) -> RetailerConfig:
        """Get retailer configuration"""
        return self.retailers[retailer_type]
    
    def get_retailer_by_code(self, code: str) -> Optional[RetailerConfig]:
        """Get retailer configuration by code"""
        for retailer in self.retailers.values():
            if retailer.code == code:
                return retailer
        return None
    
    def get_all_retailers(self) -> List[RetailerConfig]:
        """Get all retailer configurations"""
        return list(self.retailers.values())
    
    def get_retailer_by_url(self, url: str) -> Optional[RetailerConfig]:
        """Identify retailer from URL"""
        for retailer in self.retailers.values():
            if retailer.base_url in url:
                return retailer
        return None
    
    def get_total_estimated_products(self) -> int:
        """Get total estimated products across all retailers"""
        return sum(retailer.estimated_products for retailer in self.retailers.values())
    
    def get_retailers_by_focus(self, category: str) -> List[RetailerConfig]:
        """Get retailers that focus on specific category"""
        return [
            retailer for retailer in self.retailers.values()
            if category in retailer.focus_categories
        ]
    
    def calculate_monitoring_distribution(self) -> Dict[str, Dict[str, int]]:
        """Calculate monitoring tier distribution across all retailers"""
        distribution = {}
        
        for retailer in self.retailers.values():
            # Estimate tier distribution based on product count and market position
            total = retailer.estimated_products
            
            if "Premium" in retailer.market_position:
                ultra_critical = int(total * 0.15)  # 15% ultra-critical
                high_value = int(total * 0.25)      # 25% high-value
                standard = int(total * 0.35)        # 35% standard
                low_priority = total - (ultra_critical + high_value + standard)
            elif "Specialist" in retailer.market_position:
                ultra_critical = int(total * 0.05)  # 5% ultra-critical
                high_value = int(total * 0.20)      # 20% high-value
                standard = int(total * 0.45)        # 45% standard
                low_priority = total - (ultra_critical + high_value + standard)
            else:  # Market Leader or Value
                ultra_critical = int(total * 0.08)  # 8% ultra-critical
                high_value = int(total * 0.22)      # 22% high-value
                standard = int(total * 0.40)        # 40% standard
                low_priority = total - (ultra_critical + high_value + standard)
            
            distribution[retailer.code] = {
                "ultra_critical": ultra_critical,
                "high_value": high_value,
                "standard": standard,
                "low_priority": low_priority,
                "total": total
            }
        
        return distribution


# Global retailer manager instance
retailer_manager = RetailerManager()


def get_unified_category_mapping() -> Dict[str, str]:
    """Create unified category mapping across all retailers"""
    unified_categories = {
        # Core Categories
        "appliances": "เครื่องใช้ไฟฟ้า",
        "furniture": "เฟอร์นิเจอร์", 
        "lighting": "โคมไฟและหลอดไฟ",
        "paint": "สีและอุปกรณ์ทาสี",
        "construction": "วัสดุก่อสร้าง",
        "tools": "เครื่องมือ",
        "electrical": "อิเล็กทรอนิกส์",
        "plumbing": "ห้องน้ำและประปา",
        "kitchen": "ห้องครัว",
        "bathroom": "ห้องน้ำ",
        "bedroom": "ห้องนอน",
        "living_room": "ห้องรับแขก",
        "outdoor": "ของใช้กลางแจ้ง",
        "garden": "สวน",
        "flooring": "พื้นผิว",
        "doors_windows": "ประตูและหน้าต่าง",
        "roofing": "หลังคา",
        "tiles": "กระเบื้อง",
        "sanitary": "สุขภัณฑ์",
        "hardware": "ฮาร์ดแวร์",
        "safety": "ความปลอดภัย",
        "automotive": "ยานยนต์",
        "office": "สำนักงาน",
        "storage": "จัดเก็บ",
        "home_decor": "ของตั้งแต่ง",
        "household": "ของใช้ในบ้าน",
        
        # Specialty Categories
        "ceramic": "เซรามิก",
        "coating": "เคลือบผิว",
        "industrial": "อุตสาหกรรม",
        "diy": "ทำเอง",
        "premium_living": "การใช้ชีวิตระดับพรีเมียม",
    }
    
    return unified_categories