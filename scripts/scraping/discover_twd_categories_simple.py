"""
Simple script to check Thai Watsadu categories
"""
import requests
import time

def check_categories():
    """Check Thai Watsadu categories"""
    base_url = "https://www.thaiwatsadu.com/th/category"
    
    # Common Thai Watsadu categories based on typical construction store patterns
    categories_to_check = [
        # Known working categories
        ("เหล็ก", "51"),
        ("สีผสมเครื่องแบบ-Digital-Color", "6010"),
        ("ระบบโซลาร์เซลล์", "6110"),
        ("ผ้าม่านสั่งตัด", "719900"),
        
        # Common construction categories
        ("เครื่องมือช่าง", "52"),
        ("อุปกรณ์ไฟฟ้า", "53"),
        ("ท่อและอุปกรณ์ประปา", "54"),
        ("สี", "55"),
        ("สีและเคมีภัณฑ์", "55"),
        ("วัสดุปูพื้นและผนัง", "56"),
        ("หลังคา", "57"),
        ("ประตู-หน้าต่าง", "58"),
        ("สวนและอุปกรณ์ตกแต่ง", "59"),
        ("อุปกรณ์เซฟตี้", "510"),
        ("ปูน", "511"),
        ("ไม้", "512"),
        ("กระเบื้อง", "513"),
        ("สุขภัณฑ์", "514"),
        ("ฮาร์ดแวร์", "515"),
        ("เครื่องใช้ไฟฟ้า", "516"),
        
        # Additional categories
        ("เหล็กเส้น", "5101"),
        ("เหล็กแผ่น", "5102"),
        ("ตะแกรงไวร์เมช", "5103"),
        ("อิฐ", "520"),
        ("หิน", "521"),
        ("ทราย", "522"),
        ("กาว", "530"),
        ("ซีเมนต์", "531"),
        ("เคมีภัณฑ์ก่อสร้าง", "540"),
        ("เครื่องมือไฟฟ้า", "5201"),
        ("เครื่องมือลม", "5202"),
        ("อุปกรณ์ช่าง", "5203"),
        ("สว่าน", "5204"),
        ("ไขควง", "5205"),
    ]
    
    print("Checking Thai Watsadu categories...")
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
    print("\nCategory URLs for configuration:")
    print("-" * 80)
    print("category_urls=[")
    for name, cat_id, url in valid_categories:
        print(f'            "{url}",  # {name}')
    print("        ],")

if __name__ == "__main__":
    check_categories()