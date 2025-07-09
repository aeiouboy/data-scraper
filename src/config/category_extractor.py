"""
Category information extractor for all retailers
"""
import re
from typing import List, Dict, Tuple
from urllib.parse import urlparse, unquote


def extract_category_info(retailer_code: str, url: str) -> Dict[str, str]:
    """
    Extract category information from URL based on retailer
    Returns dict with code, name, and name_th
    """
    
    if retailer_code == "HP":  # HomePro
        return extract_homepro_category(url)
    elif retailer_code == "TWD":  # Thai Watsadu
        return extract_twd_category(url)
    elif retailer_code == "GH":  # Global House
        return extract_globalhouse_category(url)
    elif retailer_code == "DH":  # DoHome
        return extract_dohome_category(url)
    elif retailer_code == "BT":  # Boonthavorn
        return extract_boonthavorn_category(url)
    elif retailer_code == "MH":  # MegaHome
        return extract_megahome_category(url)
    else:
        # Generic extraction
        parts = url.split('/')
        code = parts[-1] if parts else "UNKNOWN"
        return {
            "code": code.upper()[:10],
            "name": code.replace('-', ' ').replace('_', ' ').title(),
            "name_th": "หมวดหมู่"
        }


def extract_homepro_category(url: str) -> Dict[str, str]:
    """Extract HomePro category info from URL like https://www.homepro.co.th/c/LIG"""
    code_mapping = {
        'APP': ('Appliances', 'เครื่องใช้ไฟฟ้า'),
        'ATM': ('Automotive', 'ยานยนต์'),
        'BAT': ('Bathroom', 'ห้องน้ำ'),
        'BEA': ('Beauty', 'ความงาม'),
        'BED': ('Bedroom', 'ห้องนอน'),
        'CEI': ('Ceiling', 'ฝ้าเพดาน'),
        'CLO': ('Cleaning', 'ทำความสะอาด'),
        'COM': ('Computer/Commercial', 'คอมพิวเตอร์/เชิงพาณิชย์'),
        'CON': ('Construction', 'วัสดุก่อสร้าง'),
        'DEC': ('Decoration', 'ของตกแต่ง'),
        'DIY': ('Do It Yourself', 'งานประดิษฐ์'),
        'DOW': ('Doors & Windows', 'ประตูและหน้าต่าง'),
        'ELT': ('Electronics', 'อิเล็กทรอนิกส์'),
        'FLO': ('Flooring', 'พื้น'),
        'FUR': ('Furniture', 'เฟอร์นิเจอร์'),
        'GAR': ('Garden', 'สวน'),
        'HEA': ('Health', 'สุขภาพ'),
        'HHP': ('Household', 'ของใช้ในบ้าน'),
        'HVA': ('HVAC', 'ระบบปรับอากาศ'),
        'INS': ('Insulation', 'ฉนวน'),
        'KIT': ('Kitchen', 'ห้องครัว'),
        'LIG': ('Lighting', 'โคมไฟและหลอดไฟ'),
        'MOM': ('Mom & Baby', 'แม่และเด็ก'),
        'NET': ('Network', 'เครือข่าย'),
        'OFF': ('Office', 'สำนักงาน'),
        'OUT': ('Outdoor', 'ของใช้กลางแจ้ง'),
        'PAI': ('Paint', 'สีและอุปกรณ์ทาสี'),
        'PET': ('Pet', 'สัตว์เลี้ยง'),
        'PLU': ('Plumbing', 'ประปา'),
        'POW': ('Power Tools', 'เครื่องมือไฟฟ้า'),
        'ROO': ('Roofing', 'หลังคา'),
        'SAF': ('Safety', 'ความปลอดภัย'),
        'SER': ('Services', 'บริการ'),
        'SMA': ('Smart Home', 'บ้านอัจฉริยะ'),
        'SPO': ('Sports', 'กีฬา'),
        'STA': ('Stationery', 'เครื่องเขียน'),
        'STO': ('Storage', 'ที่เก็บของ'),
        'TEX': ('Textiles', 'สิ่งทอ'),
        'TIL': ('Tiles', 'กระเบื้อง'),
        'TOO': ('Tools', 'เครื่องมือ'),
        'TVA': ('TV & Audio', 'ทีวีและเครื่องเสียง'),
        'WAL': ('Wall', 'ผนัง'),
    }
    
    # Extract code from URL
    match = re.search(r'/c/([A-Z]{3})$', url)
    if match:
        code = match.group(1)
        name, name_th = code_mapping.get(code, (code, code))
        return {"code": code, "name": name, "name_th": name_th}
    
    return {"code": "UNKNOWN", "name": "Unknown", "name_th": "ไม่ทราบ"}


def extract_twd_category(url: str) -> Dict[str, str]:
    """Extract Thai Watsadu category info from URL"""
    # Thai Watsadu uses pattern: /category/เหล็ก-51
    match = re.search(r'/category/(.+)-(\d+)$', url)
    if match:
        name_th = unquote(match.group(1))
        cat_id = match.group(2)
        
        # Map Thai names to English (common categories)
        th_to_en = {
            'เหล็ก': 'Steel',
            'ไฟเบอร์ซีเมนต์-ไม้อัด-ยิปซัม-โพลีคาร์บอเนต': 'Fiber Cement & Wood',
            'ปูนซีเมนต์': 'Cement',
            'อิฐ-บล็อก': 'Bricks & Blocks',
            'หิน-ทราย': 'Stone & Sand',
            'คอนกรีตผสมเสร็จ': 'Ready Mix Concrete',
            'เคมีภัณฑ์ก่อสร้าง': 'Construction Chemicals',
            'ระบบน้ำ-ประปา': 'Plumbing System',
            'ระบบไฟฟ้า': 'Electrical System',
            'เครื่องมือช่าง': 'Tools',
            'สี': 'Paint',
            'กระเบื้อง': 'Tiles',
            'สุขภัณฑ์-ห้องน้ำ': 'Bathroom & Sanitary',
            'ประตู-หน้าต่าง': 'Doors & Windows',
            'หลังคา': 'Roofing',
            'พื้น-ผนัง-ฝ้า': 'Floor Wall Ceiling',
            'ตกแต่ง': 'Decoration',
            'สวน': 'Garden',
            'เฟอร์นิเจอร์': 'Furniture',
            'เครื่องใช้ไฟฟ้า': 'Appliances',
        }
        
        name_en = th_to_en.get(name_th, name_th)
        code = f"TWD{cat_id}"
        
        return {"code": code, "name": name_en, "name_th": name_th}
    
    return {"code": "TWD_UNK", "name": "Unknown", "name_th": "ไม่ทราบ"}


def extract_globalhouse_category(url: str) -> Dict[str, str]:
    """Extract Global House category info from URL"""
    # Remove base URL and get last part
    parts = url.split('/')
    if len(parts) > 0:
        slug = parts[-1]
        
        # Convert slug to readable name
        name = slug.replace('-', ' ').title()
        
        # Common category mappings
        slug_mapping = {
            'adhesives': ('Adhesives', 'กาวและสารยึดติด'),
            'appliances': ('Appliances', 'เครื่องใช้ไฟฟ้า'),
            'automotive': ('Automotive', 'ยานยนต์'),
            'bathroom': ('Bathroom', 'ห้องน้ำ'),
            'bedroom': ('Bedroom', 'ห้องนอน'),
            'ceiling': ('Ceiling', 'ฝ้าเพดาน'),
            'cleaning': ('Cleaning', 'ทำความสะอาด'),
            'construction': ('Construction', 'วัสดุก่อสร้าง'),
            'curtains': ('Curtains', 'ผ้าม่าน'),
            'decorative-items': ('Decorative Items', 'ของตกแต่ง'),
            'doors-windows': ('Doors & Windows', 'ประตูและหน้าต่าง'),
            'electrical': ('Electrical', 'ไฟฟ้า'),
            'fasteners': ('Fasteners', 'ตัวยึด'),
            'flooring': ('Flooring', 'พื้น'),
            'furniture': ('Furniture', 'เฟอร์นิเจอร์'),
            'furniture-parts': ('Furniture Parts', 'อะไหล่เฟอร์นิเจอร์'),
            'garden': ('Garden', 'สวน'),
            'hand-tools': ('Hand Tools', 'เครื่องมือช่าง'),
            'hardware': ('Hardware', 'ฮาร์ดแวร์'),
            'home-decor': ('Home Decor', 'ของตกแต่งบ้าน'),
            'insulation': ('Insulation', 'ฉนวน'),
            'kitchen-appliances': ('Kitchen Appliances', 'เครื่องใช้ไฟฟ้าในครัว'),
            'kitchen-dining': ('Kitchen & Dining', 'ครัวและห้องอาหาร'),
            'lighting': ('Lighting', 'ไฟและโคมไฟ'),
            'living-room': ('Living Room', 'ห้องนั่งเล่น'),
            'measuring-tools': ('Measuring Tools', 'เครื่องมือวัด'),
            'metal-materials': ('Metal Materials', 'วัสดุโลหะ'),
            'office': ('Office', 'สำนักงาน'),
            'outdoor': ('Outdoor', 'กลางแจ้ง'),
            'paint': ('Paint', 'สี'),
            'pet-supplies': ('Pet Supplies', 'อุปกรณ์สัตว์เลี้ยง'),
            'plumbing': ('Plumbing', 'ประปา'),
            'power-tools': ('Power Tools', 'เครื่องมือไฟฟ้า'),
            'roofing': ('Roofing', 'หลังคา'),
            'rugs': ('Rugs', 'พรม'),
            'safety-equipment': ('Safety Equipment', 'อุปกรณ์ความปลอดภัย'),
            'sealants': ('Sealants', 'สารเคลือบ'),
            'small-appliances': ('Small Appliances', 'เครื่องใช้ไฟฟ้าขนาดเล็ก'),
            'sports': ('Sports', 'กีฬา'),
            'storage': ('Storage', 'ที่เก็บของ'),
            'textiles': ('Textiles', 'สิ่งทอ'),
            'tiles': ('Tiles', 'กระเบื้อง'),
            'tools': ('Tools', 'เครื่องมือ'),
            'toys': ('Toys', 'ของเล่น'),
            'wall-materials': ('Wall Materials', 'วัสดุผนัง'),
            'wood-materials': ('Wood Materials', 'วัสดุไม้'),
        }
        
        if slug in slug_mapping:
            name, name_th = slug_mapping[slug]
        else:
            name_th = name
        
        code = slug.upper().replace('-', '_')[:10]
        
        return {"code": code, "name": name, "name_th": name_th}
    
    return {"code": "GH_UNK", "name": "Unknown", "name_th": "ไม่ทราบ"}


def extract_dohome_category(url: str) -> Dict[str, str]:
    """Extract DoHome category info from URL"""
    # DoHome uses both /category/slug and /slug patterns
    match = re.search(r'/(category/)?([a-z-]+)$', url)
    if match:
        slug = match.group(2)
        
        # Category mappings
        slug_mapping = {
            'adhesives': ('Adhesives', 'กาวและสารยึดติด'),
            'air-conditioning': ('Air Conditioning', 'เครื่องปรับอากาศ'),
            'appliances': ('Appliances', 'เครื่องใช้ไฟฟ้า'),
            'automotive': ('Automotive', 'ยานยนต์'),
            'bathroom': ('Bathroom', 'ห้องน้ำ'),
            'bolts': ('Bolts', 'สลักเกลียว'),
            'brackets': ('Brackets', 'ขายึด'),
            'bricks': ('Bricks', 'อิฐ'),
            'building-materials': ('Building Materials', 'วัสดุก่อสร้าง'),
            'cement': ('Cement', 'ปูนซีเมนต์'),
            'cleaning': ('Cleaning', 'ทำความสะอาด'),
            'concrete': ('Concrete', 'คอนกรีต'),
            'coolers': ('Coolers', 'เครื่องทำความเย็น'),
            'doors-windows': ('Doors & Windows', 'ประตูและหน้าต่าง'),
            'electrical': ('Electrical', 'ไฟฟ้า'),
            'fans': ('Fans', 'พัดลม'),
            'fasteners': ('Fasteners', 'ตัวยึด'),
            'filters': ('Filters', 'ไส้กรอง'),
            'fittings': ('Fittings', 'ข้อต่อ'),
            'flooring': ('Flooring', 'พื้น'),
            'furniture': ('Furniture', 'เฟอร์นิเจอร์'),
            'garden': ('Garden', 'สวน'),
            'glass': ('Glass', 'กระจก'),
            'hand-tools': ('Hand Tools', 'เครื่องมือช่าง'),
            'handles': ('Handles', 'มือจับ'),
            'hardware-tools': ('Hardware & Tools', 'ฮาร์ดแวร์และเครื่องมือ'),
            'heaters': ('Heaters', 'เครื่องทำความร้อน'),
            'hinges': ('Hinges', 'บานพับ'),
            'household': ('Household', 'ของใช้ในบ้าน'),
            'insulation': ('Insulation', 'ฉนวน'),
            'kitchen': ('Kitchen', 'ครัว'),
            'lighting': ('Lighting', 'ไฟและโคมไฟ'),
            'locks': ('Locks', 'กุญแจ'),
            'metal-sheets': ('Metal Sheets', 'แผ่นโลหะ'),
            'nails': ('Nails', 'ตะปู'),
            'outdoor-living': ('Outdoor Living', 'ของใช้กลางแจ้ง'),
            'paint': ('Paint', 'สี'),
            'pipes': ('Pipes', 'ท่อ'),
            'plastic': ('Plastic', 'พลาสติก'),
            'plumbing': ('Plumbing', 'ประปา'),
            'power-tools': ('Power Tools', 'เครื่องมือไฟฟ้า'),
            'pumps': ('Pumps', 'ปั๊ม'),
            'roofing': ('Roofing', 'หลังคา'),
            'safety': ('Safety', 'ความปลอดภัย'),
            'sand': ('Sand', 'ทราย'),
            'screws': ('Screws', 'สกรู'),
            'steel': ('Steel', 'เหล็ก'),
            'stone': ('Stone', 'หิน'),
            'storage': ('Storage', 'ที่เก็บของ'),
            'tanks': ('Tanks', 'ถัง'),
            'tiles': ('Tiles', 'กระเบื้อง'),
            'valves': ('Valves', 'วาล์ว'),
            'ventilation': ('Ventilation', 'ระบายอากาศ'),
            'wood': ('Wood', 'ไม้'),
        }
        
        if slug in slug_mapping:
            name, name_th = slug_mapping[slug]
        else:
            name = slug.replace('-', ' ').title()
            name_th = name
        
        code = slug.upper().replace('-', '_')[:10]
        
        return {"code": code, "name": name, "name_th": name_th}
    
    return {"code": "DH_UNK", "name": "Unknown", "name_th": "ไม่ทราบ"}


def extract_boonthavorn_category(url: str) -> Dict[str, str]:
    """Extract Boonthavorn category info from URL"""
    # Boonthavorn uses pattern like /th/bathroom/faucets, /tiles, etc.
    match = re.search(r'/th/([^/]+)/?([^/]+)?', url)
    if match:
        main_cat = match.group(1)
        sub_cat = match.group(2) if match.group(2) else None
        
        # Category mappings
        cat_mapping = {
            'bathroom': ('Bathroom', 'ห้องน้ำ'),
            'faucets': ('Faucets', 'ก๊อกน้ำ'),
            'showers': ('Showers', 'ฝักบัว'),
            'sanitary-ware': ('Sanitary Ware', 'สุขภัณฑ์'),
            'bathroom-accessories': ('Bathroom Accessories', 'อุปกรณ์ห้องน้ำ'),
            'tiles': ('Tiles', 'กระเบื้อง'),
            'ceramic-tiles': ('Ceramic Tiles', 'กระเบื้องเซรามิก'),
            'porcelain-tiles': ('Porcelain Tiles', 'กระเบื้องพอร์ซเลน'),
            'floor-tiles': ('Floor Tiles', 'กระเบื้องพื้น'),
            'wall-tiles': ('Wall Tiles', 'กระเบื้องผนัง'),
            'mosaic-tiles': ('Mosaic Tiles', 'กระเบื้องโมเสค'),
            'wood-tiles': ('Wood Tiles', 'กระเบื้องลายไม้'),
            'kitchen': ('Kitchen', 'ครัว'),
            'kitchen-sinks': ('Kitchen Sinks', 'อ่างล้างจาน'),
            'kitchen-faucets': ('Kitchen Faucets', 'ก๊อกอ่างล้างจาน'),
            'doors': ('Doors', 'ประตู'),
            'wooden-doors': ('Wooden Doors', 'ประตูไม้'),
            'steel-doors': ('Steel Doors', 'ประตูเหล็ก'),
            'roofing': ('Roofing', 'หลังคา'),
            'roof-tiles': ('Roof Tiles', 'กระเบื้องหลังคา'),
            'concrete-roof-tiles': ('Concrete Roof Tiles', 'กระเบื้องคอนกรีต'),
        }
        
        # Use subcategory if available, otherwise main category
        lookup_key = sub_cat if sub_cat else main_cat
        if lookup_key in cat_mapping:
            name, name_th = cat_mapping[lookup_key]
        else:
            name = lookup_key.replace('-', ' ').title()
            name_th = name
        
        code = lookup_key.upper().replace('-', '_')[:10]
        
        return {"code": code, "name": name, "name_th": name_th}
    
    return {"code": "BT_UNK", "name": "Unknown", "name_th": "ไม่ทราบ"}


def extract_megahome_category(url: str) -> Dict[str, str]:
    """Extract MegaHome category info from URL"""
    # MegaHome uses multiple patterns: /c/CODE, /category/slug, or /slug
    
    # Try /c/CODE pattern first
    match = re.search(r'/c/([A-Z0-9]+)', url)
    if match:
        code = match.group(1)
        
        # Code mappings
        code_mapping = {
            'BAT': ('Bathroom', 'ห้องน้ำ'),
            'CON': ('Construction', 'วัสดุก่อสร้าง'),
            'DOW': ('Doors & Windows', 'ประตูและหน้าต่าง'),
            'ELT': ('Electrical', 'ไฟฟ้า'),
            'FLO': ('Flooring', 'พื้น'),
            'LIG': ('Lighting', 'ไฟและโคมไฟ'),
            'OUT': ('Outdoor', 'กลางแจ้ง'),
            'PAI': ('Paint', 'สี'),
            'PLU': ('Plumbing', 'ประปา'),
            'STE': ('Steel', 'เหล็ก'),
            'TOO': ('Tools', 'เครื่องมือ'),
        }
        
        # Check base code (first 3 chars)
        base_code = code[:3]
        if base_code in code_mapping:
            name, name_th = code_mapping[base_code]
        else:
            name = code
            name_th = code
        
        return {"code": code, "name": name, "name_th": name_th}
    
    # Try category/slug or slug pattern
    match = re.search(r'/(category/)?([a-z-]+)$', url)
    if match:
        slug = match.group(2)
        
        slug_mapping = {
            'adhesives-sealants': ('Adhesives & Sealants', 'กาวและสารเคลือบ'),
            'automotive-supplies': ('Automotive Supplies', 'อุปกรณ์ยานยนต์'),
            'building-materials': ('Building Materials', 'วัสดุก่อสร้าง'),
            'cleaning-supplies': ('Cleaning Supplies', 'อุปกรณ์ทำความสะอาด'),
            'compressors': ('Compressors', 'คอมเพรสเซอร์'),
            'concrete-cement': ('Concrete & Cement', 'คอนกรีตและปูน'),
            'concrete-tools': ('Concrete Tools', 'เครื่องมือคอนกรีต'),
            'construction-equipment': ('Construction Equipment', 'อุปกรณ์ก่อสร้าง'),
            'decking': ('Decking', 'พื้นไม้'),
            'doors-windows': ('Doors & Windows', 'ประตูและหน้าต่าง'),
            'drywall-tools': ('Drywall Tools', 'เครื่องมือติดตั้งผนัง'),
            'electrical-plumbing': ('Electrical & Plumbing', 'ไฟฟ้าและประปา'),
            'electrical-supplies': ('Electrical Supplies', 'อุปกรณ์ไฟฟ้า'),
            'electrical-tools': ('Electrical Tools', 'เครื่องมือไฟฟ้า'),
            'fasteners': ('Fasteners', 'ตัวยึด'),
            'fencing': ('Fencing', 'รั้ว'),
            'flooring': ('Flooring', 'พื้น'),
            'flooring-tools': ('Flooring Tools', 'เครื่องมือปูพื้น'),
            'garden-outdoor': ('Garden & Outdoor', 'สวนและกลางแจ้ง'),
            'generators': ('Generators', 'เครื่องกำเนิดไฟฟ้า'),
            'grills-bbq': ('Grills & BBQ', 'เตาย่างบาร์บีคิว'),
            'hand-tools': ('Hand Tools', 'เครื่องมือช่าง'),
            'hvac': ('HVAC', 'ระบบปรับอากาศ'),
            'industrial-supplies': ('Industrial Supplies', 'อุปกรณ์อุตสาหกรรม'),
            'insulation': ('Insulation', 'ฉนวน'),
            'irrigation': ('Irrigation', 'ระบบน้ำ'),
            'ladders': ('Ladders', 'บันได'),
            'landscaping': ('Landscaping', 'จัดสวน'),
            'lighting': ('Lighting', 'ไฟและโคมไฟ'),
            'masonry-tools': ('Masonry Tools', 'เครื่องมือก่ออิฐ'),
            'measuring-tools': ('Measuring Tools', 'เครื่องมือวัด'),
            'outdoor-furniture': ('Outdoor Furniture', 'เฟอร์นิเจอร์กลางแจ้ง'),
            'packaging-materials': ('Packaging Materials', 'วัสดุบรรจุภัณฑ์'),
            'paint-coating': ('Paint & Coating', 'สีและสารเคลือบ'),
            'painting-supplies': ('Painting Supplies', 'อุปกรณ์ทาสี'),
            'plumbing-fixtures': ('Plumbing Fixtures', 'อุปกรณ์ประปา'),
            'plumbing-tools': ('Plumbing Tools', 'เครื่องมือประปา'),
            'power-tools': ('Power Tools', 'เครื่องมือไฟฟ้า'),
            'roofing': ('Roofing', 'หลังคา'),
            'roofing-tools': ('Roofing Tools', 'เครื่องมือมุงหลังคา'),
            'safety-equipment': ('Safety Equipment', 'อุปกรณ์ความปลอดภัย'),
            'safety-gear': ('Safety Gear', 'อุปกรณ์เซฟตี้'),
            'scaffolding': ('Scaffolding', 'นั่งร้าน'),
            'steel-metal': ('Steel & Metal', 'เหล็กและโลหะ'),
            'storage-solutions': ('Storage Solutions', 'ระบบจัดเก็บ'),
            'tiles-ceramic': ('Tiles & Ceramic', 'กระเบื้องและเซรามิก'),
            'tools-hardware': ('Tools & Hardware', 'เครื่องมือและฮาร์ดแวร์'),
            'welding-supplies': ('Welding Supplies', 'อุปกรณ์เชื่อม'),
            'wheelbarrows': ('Wheelbarrows', 'รถเข็น'),
            'wood-lumber': ('Wood & Lumber', 'ไม้และไม้แปรรูป'),
            'workshop-equipment': ('Workshop Equipment', 'อุปกรณ์โรงงาน'),
        }
        
        if slug in slug_mapping:
            name, name_th = slug_mapping[slug]
        else:
            name = slug.replace('-', ' ').title()
            name_th = name
        
        code = slug.upper().replace('-', '_')[:10]
        
        return {"code": code, "name": name, "name_th": name_th}
    
    return {"code": "MH_UNK", "name": "Unknown", "name_th": "ไม่ทราบ"}