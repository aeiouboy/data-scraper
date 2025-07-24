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


class ScrapingMethod(Enum):
    NATIVE = "native"
    FIRECRAWL = "firecrawl"
    HYBRID = "hybrid"


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
    timeout: int = 30
    
    # Native Scraping Method Configuration
    scraping_method: ScrapingMethod = ScrapingMethod.HYBRID
    primary_strategy: str = "native"
    fallback_strategy: str = "firecrawl"
    success_rate_threshold: float = 0.8
    response_time_threshold: float = 10.0
    fallback_after_failures: int = 3
    min_data_quality_score: float = 0.7
    
    # Data Extraction Patterns
    category_mapping: Dict[str, str] = field(default_factory=dict)
    url_patterns: Dict[str, str] = field(default_factory=dict)
    selectors: Dict[str, List[str]] = field(default_factory=dict)
    
    # Search Configuration
    search_patterns: Dict[str, str] = field(default_factory=dict)
    
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
            # ALL 42 HomePro Categories
            "https://www.homepro.co.th/c/APP",  # APP - Appliances
            "https://www.homepro.co.th/c/ATM",  # ATM - Automotive
            "https://www.homepro.co.th/c/BAT",  # BAT - Bathroom
            "https://www.homepro.co.th/c/BEA",  # BEA - Beauty
            "https://www.homepro.co.th/c/BED",  # BED - Bedroom
            "https://www.homepro.co.th/c/CEI",  # CEI - Ceiling
            "https://www.homepro.co.th/c/CLO",  # CLO - Cleaning
            "https://www.homepro.co.th/c/COM",  # COM - Computer/Commercial
            "https://www.homepro.co.th/c/CON",  # CON - Construction
            "https://www.homepro.co.th/c/DEC",  # DEC - Decoration
            "https://www.homepro.co.th/c/DIY",  # DIY - Do It Yourself
            "https://www.homepro.co.th/c/DOW",  # DOW - Doors/Windows
            "https://www.homepro.co.th/c/ELT",  # ELT - Electronics
            "https://www.homepro.co.th/c/FLO",  # FLO - Flooring
            "https://www.homepro.co.th/c/FUR",  # FUR - Furniture
            "https://www.homepro.co.th/c/GAR",  # GAR - Garden
            "https://www.homepro.co.th/c/HEA",  # HEA - Health
            "https://www.homepro.co.th/c/HHP",  # HHP - Household
            "https://www.homepro.co.th/c/HVA",  # HVA - HVAC
            "https://www.homepro.co.th/c/INS",  # INS - Insulation
            "https://www.homepro.co.th/c/KIT",  # KIT - Kitchen
            "https://www.homepro.co.th/c/LIG",  # LIG - Lighting
            "https://www.homepro.co.th/c/MOM",  # MOM - Mom & Baby
            "https://www.homepro.co.th/c/NET",  # NET - Network
            "https://www.homepro.co.th/c/OFF",  # OFF - Office
            "https://www.homepro.co.th/c/OUT",  # OUT - Outdoor
            "https://www.homepro.co.th/c/PAI",  # PAI - Paint
            "https://www.homepro.co.th/c/PET",  # PET - Pet
            "https://www.homepro.co.th/c/PLU",  # PLU - Plumbing
            "https://www.homepro.co.th/c/POW",  # POW - Power Tools
            "https://www.homepro.co.th/c/ROO",  # ROO - Roofing
            "https://www.homepro.co.th/c/SAF",  # SAF - Safety
            "https://www.homepro.co.th/c/SER",  # SER - Services
            "https://www.homepro.co.th/c/SMA",  # SMA - Smart Home
            "https://www.homepro.co.th/c/SPO",  # SPO - Sports
            "https://www.homepro.co.th/c/STA",  # STA - Stationery
            "https://www.homepro.co.th/c/STO",  # STO - Storage
            "https://www.homepro.co.th/c/TEX",  # TEX - Textiles
            "https://www.homepro.co.th/c/TIL",  # TIL - Tiles
            "https://www.homepro.co.th/c/TOO",  # TOO - Tools
            "https://www.homepro.co.th/c/TVA",  # TVA - TV/Audio
            "https://www.homepro.co.th/c/WAL",  # WAL - Wall
        ],
        product_url_patterns=['/p/', '/product/', '/products/'],
        estimated_products=68500,
        rate_limit_delay=1.0,
        max_concurrent=5,
        timeout=30,
        scraping_method=ScrapingMethod.HYBRID,
        primary_strategy="native",
        fallback_strategy="firecrawl",
        success_rate_threshold=0.8,
        response_time_threshold=8.0,
        fallback_after_failures=3,
        min_data_quality_score=0.7,
        category_mapping={
            'APP': 'เครื่องใช้ไฟฟ้า',
            'ATM': 'ยานยนต์',
            'BAT': 'ห้องน้ำ',
            'BEA': 'ความงาม',
            'BED': 'ห้องนอน',
            'CEI': 'ฝ้าเพดาน',
            'CLO': 'ทำความสะอาด',
            'COM': 'คอมพิวเตอร์',
            'CON': 'วัสดุก่อสร้าง',
            'DEC': 'ของตกแต่ง',
            'DIY': 'งานประดิษฐ์',
            'DOW': 'ประตูและหน้าต่าง',
            'ELT': 'อิเล็กทรอนิกส์',
            'FLO': 'พื้น',
            'FUR': 'เฟอร์นิเจอร์',
            'GAR': 'สวน',
            'HEA': 'สุขภาพ',
            'HHP': 'ของใช้ในบ้าน',
            'HVA': 'ระบบปรับอากาศ',
            'INS': 'ฉนวน',
            'KIT': 'ห้องครัว',
            'LIG': 'โคมไฟและหลอดไฟ',
            'MOM': 'แม่และเด็ก',
            'NET': 'เครือข่าย',
            'OFF': 'สำนักงาน',
            'OUT': 'ของใช้กลางแจ้ง',
            'PAI': 'สีและอุปกรณ์ทาสี',
            'PET': 'สัตว์เลี้ยง',
            'PLU': 'ประปา',
            'POW': 'เครื่องมือไฟฟ้า',
            'ROO': 'หลังคา',
            'SAF': 'ความปลอดภัย',
            'SER': 'บริการ',
            'SMA': 'สมาร์ทโฮม',
            'SPO': 'กีฬา',
            'STA': 'เครื่องเขียน',
            'STO': 'จัดเก็บ',
            'TEX': 'สิ่งทอ',
            'TIL': 'กระเบื้อง',
            'TOO': 'เครื่องมือ',
            'TVA': 'ทีวีและเครื่องเสียง',
            'WAL': 'ผนัง',
        },
        search_patterns={
            'url_pattern': '/search?q={query}',
            'query_parameter': 'q',
            'results_per_page': 20
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
            # ALL 151 Thai Watsadu Categories
            "https://www.thaiwatsadu.com/category/เหล็ก-51",  # ID: 51
            "https://www.thaiwatsadu.com/category/ไฟเบอร์ซีเมนต์-ไม้อัด-ยิปซัม-โพลีคาร์บอเนต-52",  # ID: 52
            "https://www.thaiwatsadu.com/category/วัสดุก่อสร้าง-53",  # ID: 53
            "https://www.thaiwatsadu.com/category/งานระบบประปา-และระบบกรองน้ำ-54",  # ID: 54
            "https://www.thaiwatsadu.com/category/ประตู-หน้าต่าง-บันได-รั้ว-วัสดุตกแต่ง-55",  # ID: 55
            "https://www.thaiwatsadu.com/category/กระเบื้อง-|-อุปกรณ์-56",  # ID: 56
            "https://www.thaiwatsadu.com/category/พื้นไม้ลามิเนต-|-พรม-|-วัสดุปูพื้น-57",  # ID: 57
            "https://www.thaiwatsadu.com/category/เครื่องมือช่าง-|-อุปกรณ์ก่อสร้าง-58",  # ID: 58
            "https://www.thaiwatsadu.com/category/ฮาร์ดแวร์-เคมีภัณฑ์-59",  # ID: 59
            "https://www.thaiwatsadu.com/category/สีและอุปกรณ์ทาสี-60",  # ID: 60
            "https://www.thaiwatsadu.com/category/ระบบไฟฟ้า-61",  # ID: 61
            "https://www.thaiwatsadu.com/category/โคมไฟ-|-แสงสว่าง-62",  # ID: 62
            "https://www.thaiwatsadu.com/category/เครื่องใช้ไฟฟ้า-|-อิเล็กทรอนิกส์-63",  # ID: 63
            "https://www.thaiwatsadu.com/category/ห้องน้ำ-|-อุปกรณ์ห้องน้ำ-64",  # ID: 64
            "https://www.thaiwatsadu.com/category/ห้องครัว-|-เครื่องครัว-65",  # ID: 65
            "https://www.thaiwatsadu.com/category/เฟอร์นิเจอร์ในสวน-|-ของตกแต่งนอกบ้าน-66",  # ID: 66
            "https://www.thaiwatsadu.com/category/อุปกรณ์เกษตร-|-งานสวน-|-ระบบน้ำ-67",  # ID: 67
            "https://www.thaiwatsadu.com/category/ที่นอน-|-เครื่องนอน-|-ผ้าขนหนู-68",  # ID: 68
            "https://www.thaiwatsadu.com/category/เฟอร์นิเจอร์ภายในบ้าน-69",  # ID: 69
            "https://www.thaiwatsadu.com/category/ชั้นวางของและอุปกรณ์จัดเก็บทั่วไป-70",  # ID: 70
            "https://www.thaiwatsadu.com/category/ผ้าม่าน-|-พรม-71",  # ID: 71
            "https://www.thaiwatsadu.com/category/ของตกแต่งบ้าน-72",  # ID: 72
            "https://www.thaiwatsadu.com/category/อุปกรณ์ทำความสะอาด-|-ซักล้าง-74",  # ID: 74
            "https://www.thaiwatsadu.com/category/อุปกรณ์ประดับยนต์-75",  # ID: 75
            "https://www.thaiwatsadu.com/category/อุปกรณ์สำหรับการเดินทาง-76",  # ID: 76
            "https://www.thaiwatsadu.com/category/โรงแรม-|-ร้านอาหาร-77",  # ID: 77
            "https://www.thaiwatsadu.com/category/Lifestyle-&-Gadget-78",  # ID: 78
            "https://www.thaiwatsadu.com/category/ไอเท็มอุ่นใจ-ห่างไกลโควิด-79",  # ID: 79
            "https://www.thaiwatsadu.com/category/Shop-by-lifestyles-82",  # ID: 82
            "https://www.thaiwatsadu.com/category/Go-WOW-84",  # ID: 84
            "https://www.thaiwatsadu.com/category/บริการติดตั้ง-vFIX-ช่างมือ-1-96",  # ID: 96
            "https://www.thaiwatsadu.com/category/สินค้าของแถม-97",  # ID: 97
            "https://www.thaiwatsadu.com/category/สินค้าโปรโมชั่น-98",  # ID: 98
            "https://www.thaiwatsadu.com/category/ค่าบริการติดตั้ง-99",  # ID: 99
            "https://www.thaiwatsadu.com/category/เหล็กเพื่องานฐานราก-5101",  # ID: 5101
            "https://www.thaiwatsadu.com/category/เหล็กเพื่องานโครงสร้าง-5102",  # ID: 5102
            "https://www.thaiwatsadu.com/category/เหล็กแป๊บ-5103",  # ID: 5103
            "https://www.thaiwatsadu.com/category/เหล็กอเนกประสงค์-5104",  # ID: 5104
            "https://www.thaiwatsadu.com/category/สินค้าเหล็กใช้งานทั่วไป-5105",  # ID: 5105
            "https://www.thaiwatsadu.com/category/เหล็กสำเร็จรูป-5106",  # ID: 5106
            "https://www.thaiwatsadu.com/category/ไม้ฝา-ไม้พื้น-ไม้เชิงชาย-ไม้ระแนงไฟเบอร์ซีเมนต์-5201",  # ID: 5201
            "https://www.thaiwatsadu.com/category/ไฟเบอร์ซีเมนต์บอร์ด-5202",  # ID: 5202
            "https://www.thaiwatsadu.com/category/ไม้อัดฟิล์มดำ-ไม้อัด-ไม้โครง-5203",  # ID: 5203
            "https://www.thaiwatsadu.com/category/แผ่นยิปซัม-ช่องเซอร์วิส-และหน้ากากแอร์-5204",  # ID: 5204
            "https://www.thaiwatsadu.com/category/แผ่นโพลีคาร์บอเนต-พลาสวูด-ฟิวเจอร์บอร์ด-5205",  # ID: 5205
            "https://www.thaiwatsadu.com/category/ฉนวน-|-อุปกรณ์ติดตั้งฝ้าและผนัง-5206",  # ID: 5206
            "https://www.thaiwatsadu.com/category/ปูน-|-วัสดุเทพื้น-5301",  # ID: 5301
            "https://www.thaiwatsadu.com/category/อิฐ-|-บล็อกปูพื้น-5302",  # ID: 5302
            "https://www.thaiwatsadu.com/category/หลังคา-|-อุปกรณ์หลังคา-5303",  # ID: 5303
            "https://www.thaiwatsadu.com/category/ฉนวน-|-อุปกรณ์ติดตั้งฝ้าและผนัง-5304",  # ID: 5304
            "https://www.thaiwatsadu.com/category/ตู้น็อกดาวน์-5305",  # ID: 5305
            "https://www.thaiwatsadu.com/category/ปั๊มน้ำ-5401",  # ID: 5401
            "https://www.thaiwatsadu.com/category/ถังเก็บน้ำ-|-ถังดักไขมัน-|-ถังบำบัดน้ำเสีย-5402",  # ID: 5402
            "https://www.thaiwatsadu.com/category/อุปกรณ์ประปา-5403",  # ID: 5403
            "https://www.thaiwatsadu.com/category/ท่อน้ำประปา-|-อุปกรณขข้อต่อ-5404",  # ID: 5404
            "https://www.thaiwatsadu.com/category/เครื่องทำน้ำอุ่น-|-น้ำร้อน-5405",  # ID: 5405
            "https://www.thaiwatsadu.com/category/เครื่องกรองน้ำ-5406",  # ID: 5406
            "https://www.thaiwatsadu.com/category/ประตูหน้าต่างบานเลื่อนอะลูมิเนียม-และ-UPVC-5501",  # ID: 5501
            "https://www.thaiwatsadu.com/category/ประตูและวงกบประตู-5502",  # ID: 5502
            "https://www.thaiwatsadu.com/category/หน้าต่างและวงกบหน้าต่าง-5503",  # ID: 5503
            "https://www.thaiwatsadu.com/category/ไม้บัว-แผ่นผนังและวัสดุตกแต่ง-5504",  # ID: 5504
            "https://www.thaiwatsadu.com/category/ไม้บันได-ไม้พื้นและราวระเบียง-5505",  # ID: 5505
            "https://www.thaiwatsadu.com/category/รั้ว-|-หลังคาโรงรถ-|-ประตูรั้ว-5506",  # ID: 5506
            "https://www.thaiwatsadu.com/category/อุปกรณ์ประตูและหน้าต่าง-5507",  # ID: 5507
            "https://www.thaiwatsadu.com/category/เลือกตามสไตล์-5601",  # ID: 5601
            "https://www.thaiwatsadu.com/category/ประเภทสินค้า-5602",  # ID: 5602
            "https://www.thaiwatsadu.com/category/อุปกรณ์ติดตั้งกระเบื้อง-5603",  # ID: 5603
            "https://www.thaiwatsadu.com/category/กระเบื้องยางปูพื้น-|-เสื่อน้ำมัน-5701",  # ID: 5701
            "https://www.thaiwatsadu.com/category/พื้นไม้เอ็นจิเนียร์และลามิเนต-5702",  # ID: 5702
            "https://www.thaiwatsadu.com/category/อุปกรณ์ติดตั้งลามิเนตและกระเบื้องยาง-5703",  # ID: 5703
            "https://www.thaiwatsadu.com/category/พรมปูพื้น-5704",  # ID: 5704
            "https://www.thaiwatsadu.com/category/เครื่องมือช่างไฟฟ้า-5801",  # ID: 5801
            "https://www.thaiwatsadu.com/category/อุปกรณ์เสริมเครื่องมือช่างไฟฟ้า-5802",  # ID: 5802
            "https://www.thaiwatsadu.com/category/เครื่องมือช่าง-|-บันได-|-รถเข็น-5803",  # ID: 5803
            "https://www.thaiwatsadu.com/category/เครื่องมือก่อสร้าง-|-อุปกรณ์ขนย้าย-5804",  # ID: 5804
            "https://www.thaiwatsadu.com/category/เคมีภัณฑ์ก่อสร้าง-5901",  # ID: 5901
            "https://www.thaiwatsadu.com/category/อุปกรณ์เซฟตี้-5902",  # ID: 5902
            "https://www.thaiwatsadu.com/category/อุปกรณ์สำนักงาน-และพัสดุภัณฑ์-5903",  # ID: 5903
            "https://www.thaiwatsadu.com/category/อุปกรณ์ยึดติด-5904",  # ID: 5904
            "https://www.thaiwatsadu.com/category/อุปกรณ์รั้ว-5906",  # ID: 5906
            "https://www.thaiwatsadu.com/category/อุปกรณ์แขวนและยึดท่อ-5907",  # ID: 5907
            "https://www.thaiwatsadu.com/category/เชือก-โซ่-ลวด-สลิง-5908",  # ID: 5908
            "https://www.thaiwatsadu.com/category/ล้อ-5909",  # ID: 5909
            "https://www.thaiwatsadu.com/category/อุปกรณ์เฟอร์นิเจอร์-5910",  # ID: 5910
            "https://www.thaiwatsadu.com/category/แผ่นสักหลาด-ยางรองกันรอย-5911",  # ID: 5911
            "https://www.thaiwatsadu.com/category/ตู้จดหมาย-ตู้กุญแจ-ตู้ยา-5913",  # ID: 5913
            "https://www.thaiwatsadu.com/category/เครื่องชั่ง-5914",  # ID: 5914
            "https://www.thaiwatsadu.com/category/อุปกรณ์ประตูและหน้าต่าง-5915",  # ID: 5915
            "https://www.thaiwatsadu.com/category/สีและอุปกรณ์ทาสี-6000",  # ID: 6000
            "https://www.thaiwatsadu.com/category/สีเบส-6001",  # ID: 6001
            "https://www.thaiwatsadu.com/category/สีเบอร์-6002",  # ID: 6002
            "https://www.thaiwatsadu.com/category/สีรองพื้น-6003",  # ID: 6003
            "https://www.thaiwatsadu.com/category/สีน้ำมัน-สีเคลือบเงาโลหะ-6004",  # ID: 6004
            "https://www.thaiwatsadu.com/category/สีเฉพาะทาง-6005",  # ID: 6005
            "https://www.thaiwatsadu.com/category/ทินเนอร์และตัวทำละลาย-6006",  # ID: 6006
            "https://www.thaiwatsadu.com/category/สีงานไม้-6007",  # ID: 6007
            "https://www.thaiwatsadu.com/category/สีสเปรย์-6008",  # ID: 6008
            "https://www.thaiwatsadu.com/category/อุปกรณ์ทาสี-6009",  # ID: 6009
            "https://www.thaiwatsadu.com/category/สีผสมเครื่องแบบ-Digital-Color-6010",  # ID: 6010
            "https://www.thaiwatsadu.com/category/ระบบไฟฟ้า-6100",  # ID: 6100
            "https://www.thaiwatsadu.com/category/สายไฟ-6101",  # ID: 6101
            "https://www.thaiwatsadu.com/category/สายสัญญาณ-6102",  # ID: 6102
            "https://www.thaiwatsadu.com/category/อุปกรณ์เสริมไฟฟ้า-6103",  # ID: 6103
            "https://www.thaiwatsadu.com/category/ท่อและอุปกรณ์ร้อยสายไฟ-6104",  # ID: 6104
            "https://www.thaiwatsadu.com/category/ระบบตู้ไฟ-6105",  # ID: 6105
            "https://www.thaiwatsadu.com/category/สวิตช์และเต้ารับไฟฟ้า-6106",  # ID: 6106
            "https://www.thaiwatsadu.com/category/ระบบไฟฉุกเฉิน-6107",  # ID: 6107
            "https://www.thaiwatsadu.com/category/ระบบสายล่อฟ้า-สายดิน-6108",  # ID: 6108
            "https://www.thaiwatsadu.com/category/ระบบแสงสว่างภายนอก-6109",  # ID: 6109
            "https://www.thaiwatsadu.com/category/ระบบโซลาร์เซลล์-6110",  # ID: 6110
            "https://www.thaiwatsadu.com/category/เสา-ลิฟท์-ราวเคเบิ้ล-6111",  # ID: 6111
            "https://www.thaiwatsadu.com/category/ระบบประหยัดพลังงาน-6113",  # ID: 6113
            "https://www.thaiwatsadu.com/category/เครื่องชาร์จไฟฟ้า-6114",  # ID: 6114
            "https://www.thaiwatsadu.com/category/อุปกรณ์ไฟฟ้าสำรอง-6115",  # ID: 6115
            "https://www.thaiwatsadu.com/category/หลอดไฟ-6201",  # ID: 6201
            "https://www.thaiwatsadu.com/category/โคมไฟ-6202",  # ID: 6202
            "https://www.thaiwatsadu.com/category/ดาวน์ไลท์-6203",  # ID: 6203
            "https://www.thaiwatsadu.com/category/ไฟฉุกเฉิน-6205",  # ID: 6205
            "https://www.thaiwatsadu.com/category/พัดลมดูด-6206",  # ID: 6206
            "https://www.thaiwatsadu.com/category/เครื่องใช้ไฟฟ้าในบ้าน-6301",  # ID: 6301
            "https://www.thaiwatsadu.com/category/เครื่องใช้ไฟฟ้าในครัว-6302",  # ID: 6302
            "https://www.thaiwatsadu.com/category/อุปกรณ์อิเล็กทรอนิกส์-6303",  # ID: 6303
            "https://www.thaiwatsadu.com/category/วิทยุสื่อสาร-6304",  # ID: 6304
            "https://www.thaiwatsadu.com/category/เครื่องเขียน-อุปกรณ์การเรียน-6305",  # ID: 6305
            "https://www.thaiwatsadu.com/category/เครื่องสุขภาพ-6306",  # ID: 6306
            "https://www.thaiwatsadu.com/category/พัดลม-6307",  # ID: 6307
            "https://www.thaiwatsadu.com/category/สมาร์ทโฮม-6308",  # ID: 6308
            "https://www.thaiwatsadu.com/category/แบตเตอรี่-6309",  # ID: 6309
            "https://www.thaiwatsadu.com/category/สุขภัณฑ์-6401",  # ID: 6401
            "https://www.thaiwatsadu.com/category/อ่างอาบน้ำ-6402",  # ID: 6402
            "https://www.thaiwatsadu.com/category/ก๊อกน้ำ-|-ฝักบัว-6403",  # ID: 6403
            "https://www.thaiwatsadu.com/category/เครื่องใช้ในห้องน้ำ-6404",  # ID: 6404
            "https://www.thaiwatsadu.com/category/อ่างล้างหน้า-6405",  # ID: 6405
            "https://www.thaiwatsadu.com/category/ผ้าม่านห้องน้ำ-6406",  # ID: 6406
            "https://www.thaiwatsadu.com/category/ระบบน้ำดี-น้ำเสีย-6407",  # ID: 6407
            "https://www.thaiwatsadu.com/category/ห้องซาวน่า-6408",  # ID: 6408
            "https://www.thaiwatsadu.com/category/ซิงค์-|-อุปกรณ์ซิงค์-6501",  # ID: 6501
            "https://www.thaiwatsadu.com/category/เครื่องครัว-|-อุปกรณ์ครัว-6502",  # ID: 6502
            "https://www.thaiwatsadu.com/category/เตาแก๊ส-|-เตาไฟฟ้า-6503",  # ID: 6503
            "https://www.thaiwatsadu.com/category/เครื่องดูดควัน-6504",  # ID: 6504
            "https://www.thaiwatsadu.com/category/ตู้ซิงค์-|-ชุดซิงค์-6505",  # ID: 6505
            "https://www.thaiwatsadu.com/category/เฟอร์นิเจอร์ห้องครัว-6506",  # ID: 6506
            "https://www.thaiwatsadu.com/category/อุปกรณ์ก๊อกน้ำห้องครัว-6507",  # ID: 6507
            "https://www.thaiwatsadu.com/category/เตาบาร์บีคิว-6601",  # ID: 6601
            "https://www.thaiwatsadu.com/category/เฟอร์นิเจอร์ในสวน-6602",  # ID: 6602
            "https://www.thaiwatsadu.com/category/Go-WOW-7000",  # ID: 7000
            "https://www.thaiwatsadu.com/category/Go-Wow-|กระเบื้อง-7100",  # ID: 7100
            "https://www.thaiwatsadu.com/category/Go-WOW-700000",  # ID: 700000
            "https://www.thaiwatsadu.com/category/Gadget-701000",  # ID: 701000
            "https://www.thaiwatsadu.com/category/ของขวัญและกิ๊ฟท์เซท-710000",  # ID: 710000
            "https://www.thaiwatsadu.com/category/ผ้าม่านสั่งตัด-719900",  # ID: 719900
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
        base_url="https://globalhouse.co.th",
        category_urls=[
            # ALL 47 Global House Product Categories
            "https://globalhouse.co.th/adhesives",
            "https://globalhouse.co.th/appliances",
            "https://globalhouse.co.th/automotive",
            "https://globalhouse.co.th/bathroom",
            "https://globalhouse.co.th/bedding",
            "https://globalhouse.co.th/bedroom",
            "https://globalhouse.co.th/ceiling",
            "https://globalhouse.co.th/cleaning",
            "https://globalhouse.co.th/construction",
            "https://globalhouse.co.th/curtains",
            "https://globalhouse.co.th/decorative-items",
            "https://globalhouse.co.th/doors-windows",
            "https://globalhouse.co.th/electrical",
            "https://globalhouse.co.th/fasteners",
            "https://globalhouse.co.th/flooring",
            "https://globalhouse.co.th/furniture",
            "https://globalhouse.co.th/furniture-parts",
            "https://globalhouse.co.th/garden",
            "https://globalhouse.co.th/hand-tools",
            "https://globalhouse.co.th/hardware",
            "https://globalhouse.co.th/home-decor",
            "https://globalhouse.co.th/insulation",
            "https://globalhouse.co.th/kitchen-appliances",
            "https://globalhouse.co.th/kitchen-dining",
            "https://globalhouse.co.th/lighting",
            "https://globalhouse.co.th/living-room",
            "https://globalhouse.co.th/measuring-tools",
            "https://globalhouse.co.th/metal-materials",
            "https://globalhouse.co.th/office",
            "https://globalhouse.co.th/outdoor",
            "https://globalhouse.co.th/paint",
            "https://globalhouse.co.th/pet-supplies",
            "https://globalhouse.co.th/plumbing",
            "https://globalhouse.co.th/power-tools",
            "https://globalhouse.co.th/roofing",
            "https://globalhouse.co.th/rugs",
            "https://globalhouse.co.th/safety-equipment",
            "https://globalhouse.co.th/sealants",
            "https://globalhouse.co.th/small-appliances",
            "https://globalhouse.co.th/sports",
            "https://globalhouse.co.th/storage",
            "https://globalhouse.co.th/textiles",
            "https://globalhouse.co.th/tiles",
            "https://globalhouse.co.th/tools",
            "https://globalhouse.co.th/toys",
            "https://globalhouse.co.th/wall-materials",
            "https://globalhouse.co.th/wood-materials",
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
            # ALL 55 DoHome Product Categories
            "https://www.dohome.co.th/adhesives",
            "https://www.dohome.co.th/air-conditioning",
            "https://www.dohome.co.th/appliances",
            "https://www.dohome.co.th/automotive",
            "https://www.dohome.co.th/bathroom",
            "https://www.dohome.co.th/bolts",
            "https://www.dohome.co.th/brackets",
            "https://www.dohome.co.th/bricks",
            "https://www.dohome.co.th/building-materials",
            "https://www.dohome.co.th/cement",
            "https://www.dohome.co.th/cleaning",
            "https://www.dohome.co.th/concrete",
            "https://www.dohome.co.th/coolers",
            "https://www.dohome.co.th/doors-windows",
            "https://www.dohome.co.th/electrical",
            "https://www.dohome.co.th/fans",
            "https://www.dohome.co.th/fasteners",
            "https://www.dohome.co.th/filters",
            "https://www.dohome.co.th/fittings",
            "https://www.dohome.co.th/flooring",
            "https://www.dohome.co.th/furniture",
            "https://www.dohome.co.th/garden",
            "https://www.dohome.co.th/glass",
            "https://www.dohome.co.th/hand-tools",
            "https://www.dohome.co.th/handles",
            "https://www.dohome.co.th/hardware-tools",
            "https://www.dohome.co.th/heaters",
            "https://www.dohome.co.th/hinges",
            "https://www.dohome.co.th/household",
            "https://www.dohome.co.th/insulation",
            "https://www.dohome.co.th/kitchen",
            "https://www.dohome.co.th/lighting",
            "https://www.dohome.co.th/locks",
            "https://www.dohome.co.th/metal-sheets",
            "https://www.dohome.co.th/nails",
            "https://www.dohome.co.th/outdoor-living",
            "https://www.dohome.co.th/paint",
            "https://www.dohome.co.th/pipes",
            "https://www.dohome.co.th/plastic",
            "https://www.dohome.co.th/plumbing",
            "https://www.dohome.co.th/power-tools",
            "https://www.dohome.co.th/pumps",
            "https://www.dohome.co.th/roofing",
            "https://www.dohome.co.th/safety",
            "https://www.dohome.co.th/sand",
            "https://www.dohome.co.th/screws",
            "https://www.dohome.co.th/steel",
            "https://www.dohome.co.th/stone",
            "https://www.dohome.co.th/storage",
            "https://www.dohome.co.th/tanks",
            "https://www.dohome.co.th/tiles",
            "https://www.dohome.co.th/valves",
            "https://www.dohome.co.th/ventilation",
            "https://www.dohome.co.th/wood",
            # Note: /category/ URLs are duplicates of the above, so not included
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
            # Main categories
            "https://www.boonthavorn.com/boonthavorn-wall-floor",  # Tiles main category
            "https://www.boonthavorn.com/bathroom",  # Bathroom main category
            "https://www.boonthavorn.com/kitchen",  # Kitchen main category
            "https://www.boonthavorn.com/surface-covering-decorative",  # Surface covering
            "https://www.boonthavorn.com/lighting",  # Lighting
            "https://www.boonthavorn.com/home-appliances",  # Home appliances
            
            # Tile subcategories
            "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-type/floor-tiles",
            "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-type/wall-tiles",
            "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-style/marble-collection",
            "https://www.boonthavorn.com/boonthavorn-wall-floor/shop-by-style/wood-collection",
            
            # Bathroom subcategories
            "https://www.boonthavorn.com/bathroom/sanitarywares",
            "https://www.boonthavorn.com/bathroom/sanitarywares/toilet-bowls",
            "https://www.boonthavorn.com/bathroom/faucets-showers",
            "https://www.boonthavorn.com/bathroom/basins",
            "https://www.boonthavorn.com/bathroom/bathtubs",
            
            # Kitchen subcategories
            "https://www.boonthavorn.com/kitchen/kitchen-sinks-kitchen-taps-kitchen-accessories",
            "https://www.boonthavorn.com/kitchen/kitchen-appliances",
            
            # Surface covering subcategories
            "https://www.boonthavorn.com/surface-covering-decorative/stone",
            "https://www.boonthavorn.com/surface-covering-decorative/wood-flooring",
            "https://www.boonthavorn.com/surface-covering-decorative/vinyl-flooring",
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
            # ALL MegaHome Product Categories (Descriptive URLs and /c/ codes)
            # Main Category URLs
            "https://www.megahome.co.th/adhesives-sealants",
            "https://www.megahome.co.th/automotive-supplies",
            "https://www.megahome.co.th/building-materials",
            "https://www.megahome.co.th/cleaning-supplies",
            "https://www.megahome.co.th/compressors",
            "https://www.megahome.co.th/concrete-cement",
            "https://www.megahome.co.th/concrete-tools",
            "https://www.megahome.co.th/construction-equipment",
            "https://www.megahome.co.th/decking",
            "https://www.megahome.co.th/doors-windows",
            "https://www.megahome.co.th/drywall-tools",
            "https://www.megahome.co.th/electrical-plumbing",
            "https://www.megahome.co.th/electrical-supplies",
            "https://www.megahome.co.th/electrical-tools",
            "https://www.megahome.co.th/fasteners",
            "https://www.megahome.co.th/fencing",
            "https://www.megahome.co.th/flooring",
            "https://www.megahome.co.th/flooring-tools",
            "https://www.megahome.co.th/garden-outdoor",
            "https://www.megahome.co.th/generators",
            "https://www.megahome.co.th/grills-bbq",
            "https://www.megahome.co.th/hand-tools",
            "https://www.megahome.co.th/hvac",
            "https://www.megahome.co.th/industrial-supplies",
            "https://www.megahome.co.th/insulation",
            "https://www.megahome.co.th/irrigation",
            "https://www.megahome.co.th/ladders",
            "https://www.megahome.co.th/landscaping",
            "https://www.megahome.co.th/lighting",
            "https://www.megahome.co.th/masonry-tools",
            "https://www.megahome.co.th/measuring-tools",
            "https://www.megahome.co.th/outdoor-furniture",
            "https://www.megahome.co.th/packaging-materials",
            "https://www.megahome.co.th/paint-coating",
            "https://www.megahome.co.th/painting-supplies",
            "https://www.megahome.co.th/plumbing-fixtures",
            "https://www.megahome.co.th/plumbing-tools",
            "https://www.megahome.co.th/power-tools",
            "https://www.megahome.co.th/roofing",
            "https://www.megahome.co.th/roofing-tools",
            "https://www.megahome.co.th/safety-equipment",
            "https://www.megahome.co.th/safety-gear",
            "https://www.megahome.co.th/scaffolding",
            "https://www.megahome.co.th/steel-metal",
            "https://www.megahome.co.th/storage-solutions",
            "https://www.megahome.co.th/tiles-ceramic",
            "https://www.megahome.co.th/tools-hardware",
            "https://www.megahome.co.th/welding-supplies",
            "https://www.megahome.co.th/wheelbarrows",
            "https://www.megahome.co.th/wood-lumber",
            "https://www.megahome.co.th/workshop-equipment",
            # Category Code URLs
            "https://www.megahome.co.th/c/APP030101",  # Appliances subcategory
            "https://www.megahome.co.th/c/BAT",  # Bathroom
            "https://www.megahome.co.th/c/CON",  # Construction
            "https://www.megahome.co.th/c/DOW",  # Doors/Windows
            "https://www.megahome.co.th/c/ELT",  # Electrical
            "https://www.megahome.co.th/c/FLO",  # Flooring
            "https://www.megahome.co.th/c/LIG",  # Lighting
            "https://www.megahome.co.th/c/OUT",  # Outdoor
            "https://www.megahome.co.th/c/PAI",  # Paint
            "https://www.megahome.co.th/c/PLU",  # Plumbing
            "https://www.megahome.co.th/c/STE",  # Steel
            "https://www.megahome.co.th/c/TOO",  # Tools
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