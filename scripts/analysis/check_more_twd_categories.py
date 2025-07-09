"""
Check more Thai Watsadu categories
"""
import requests
import time

def check_more_categories():
    """Check additional Thai Watsadu categories"""
    base_url = "https://www.thaiwatsadu.com/th/category"
    
    # More categories to check
    categories_to_check = [
        # Safety and security
        ("อุปกรณ์เซฟตี้", "60"),
        ("อุปกรณ์ความปลอดภัย", "510"),
        ("อุปกรณ์ป้องกัน", "511"),
        
        # Building materials
        ("ปูน", "61"),
        ("ปูนซีเมนต์", "611"),
        ("ไม้", "62"),
        ("ไม้อัด", "621"),
        ("กระเบื้อง", "63"),
        ("กระเบื้องปูพื้น", "631"),
        ("กระเบื้องผนัง", "632"),
        ("สุขภัณฑ์", "64"),
        ("อ่างล้างหน้า", "641"),
        ("ชักโครก", "642"),
        ("ฮาร์ดแวร์", "65"),
        ("น็อต-สกรู", "651"),
        ("บานพับ", "652"),
        
        # Electrical appliances
        ("เครื่องใช้ไฟฟ้า", "66"),
        ("พัดลม", "661"),
        ("เครื่องปรับอากาศ", "662"),
        ("เครื่องทำน้ำอุ่น", "663"),
        
        # More tools
        ("ค้อน", "5206"),
        ("คีม", "5207"),
        ("ประแจ", "5208"),
        ("เลื่อย", "5209"),
        ("สายวัด", "5210"),
        
        # Plumbing
        ("ก๊อกน้ำ", "5401"),
        ("ท่อ-PVC", "5402"),
        ("ข้อต่อท่อ", "5403"),
        ("วาล์ว", "5404"),
        
        # Paint related
        ("แปรงทาสี", "5501"),
        ("ลูกกลิ้งทาสี", "5502"),
        ("สีรองพื้น", "5503"),
        ("สีน้ำมัน", "5504"),
        ("สีน้ำอะคริลิค", "5505"),
        
        # Garden
        ("ดินปลูก", "5901"),
        ("ปุ๋ย", "5902"),
        ("กระถางต้นไม้", "5903"),
        ("สปริงเกลอร์", "5904"),
        
        # Lighting
        ("หลอดไฟ", "5301"),
        ("โคมไฟ", "5302"),
        ("สายไฟ", "5303"),
        ("สวิตช์ไฟ", "5304"),
        ("ปลั๊กไฟ", "5305"),
    ]
    
    print("Checking additional Thai Watsadu categories...")
    print("=" * 80)
    
    valid_categories = []
    
    for name, cat_id in categories_to_check:
        url = f"{base_url}/{name}-{cat_id}"
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                valid_categories.append((name, cat_id, url))
                print(f"✓ Found: {name} (ID: {cat_id})")
            else:
                print(f"✗ Not found: {name} (ID: {cat_id}) - Status: {response.status_code}")
            time.sleep(0.2)  # Rate limiting
        except Exception as e:
            print(f"✗ Error checking {name}: {str(e)}")
    
    print("\n" + "=" * 80)
    print(f"Total valid categories found: {len(valid_categories)}")
    print("\nAdditional Category URLs:")
    print("-" * 80)
    for name, cat_id, url in valid_categories:
        print(f'            "{url}",  # {name}')

if __name__ == "__main__":
    check_more_categories()