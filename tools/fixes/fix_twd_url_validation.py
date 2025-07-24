#!/usr/bin/env python3
"""
Fix TWD URL validation and brand extraction issues
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import re
from src.services.supabase_service import SupabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_twd_urls.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TWDUrlFixer:
    """Fix TWD URL validation and brand extraction issues"""
    
    def __init__(self):
        self.supabase = SupabaseService()
    
    async def identify_invalid_twd_urls(self) -> Dict[str, Any]:
        """Identify TWD products with invalid URLs (category URLs instead of product URLs)"""
        logger.info("Identifying invalid TWD URLs...")
        
        try:
            # Get all TWD products
            result = self.supabase.client.table('products')\
                .select('id, sku, name, brand, category, url, retailer_code')\
                .eq('retailer_code', 'TWD')\
                .execute()
            
            twd_products = result.data
            
            invalid_urls = []
            valid_urls = []
            
            for product in twd_products:
                url = product['url']
                
                # Check if URL is a category URL instead of product URL
                if '/category/' in url or '/en/category/' in url:
                    invalid_urls.append({
                        'product': product,
                        'issue': 'category_url',
                        'description': 'URL points to category page instead of product page'
                    })
                elif '/th/product/' not in url and '/en/product/' not in url:
                    invalid_urls.append({
                        'product': product,
                        'issue': 'unknown_format',
                        'description': 'URL format does not match expected product URL pattern'
                    })
                else:
                    valid_urls.append(product)
            
            analysis = {
                'total_twd_products': len(twd_products),
                'invalid_urls': len(invalid_urls),
                'valid_urls': len(valid_urls),
                'invalid_products': invalid_urls,
                'analysis_time': datetime.now().isoformat()
            }
            
            logger.info(f"Found {len(invalid_urls)} invalid URLs out of {len(twd_products)} TWD products")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error identifying invalid TWD URLs: {str(e)}")
            return {'error': str(e)}
    
    async def fix_twd_brand_extraction(self) -> Dict[str, Any]:
        """Fix TWD brand extraction by inferring from product names"""
        logger.info("Fixing TWD brand extraction...")
        
        try:
            # Get TWD products with missing brands
            result = self.supabase.client.table('products')\
                .select('id, sku, name, brand, category, url, retailer_code')\
                .eq('retailer_code', 'TWD')\
                .is_('brand', 'null')\
                .execute()
            
            twd_no_brand = result.data
            
            logger.info(f"Found {len(twd_no_brand)} TWD products with missing brands")
            
            fixes = []
            
            for product in twd_no_brand:
                name = product['name']
                extracted_brand = self._extract_brand_from_twd_name(name)
                
                if extracted_brand:
                    fixes.append({
                        'product_id': product['id'],
                        'sku': product['sku'],
                        'name': name,
                        'extracted_brand': extracted_brand
                    })
            
            # Apply fixes to database
            successful_fixes = 0
            failed_fixes = 0
            
            for fix in fixes:
                try:
                    update_result = self.supabase.client.table('products')\
                        .update({'brand': fix['extracted_brand']})\
                        .eq('id', fix['product_id'])\
                        .execute()
                    
                    if update_result.data:
                        successful_fixes += 1
                        logger.info(f"Fixed brand for {fix['sku']}: {fix['extracted_brand']}")
                    else:
                        failed_fixes += 1
                        logger.error(f"Failed to update brand for {fix['sku']}")
                        
                except Exception as e:
                    failed_fixes += 1
                    logger.error(f"Error updating brand for {fix['sku']}: {str(e)}")
            
            results = {
                'total_products': len(twd_no_brand),
                'potential_fixes': len(fixes),
                'successful_fixes': successful_fixes,
                'failed_fixes': failed_fixes,
                'fixes_applied': fixes,
                'completed_at': datetime.now().isoformat()
            }
            
            logger.info(f"Brand extraction fix completed: {successful_fixes}/{len(fixes)} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"Error fixing TWD brand extraction: {str(e)}")
            return {'error': str(e)}
    
    def _extract_brand_from_twd_name(self, name: str) -> Optional[str]:
        """Extract brand from TWD product name using patterns"""
        if not name:
            return None
        
        # Common brand patterns in TWD product names
        brand_patterns = [
            # Brand at the beginning of the name
            r'^([A-Z][A-Z0-9\s&]+?)\s+(?:Air|Water|Electric|Digital|Smart|Mini|Portable|Wireless|Bluetooth|LED|LCD|TV|Monitor|Phone|Tablet|Laptop|Computer|Camera|Speaker|Headphone|Mouse|Keyboard|Router|Modem|Printer|Scanner|Projector|Microphone|Refrigerator|Washing|Dryer|Dishwasher|Oven|Microwave|Blender|Mixer|Juicer|Toaster|Rice|Cooker|Kettle|Iron|Vacuum|Fan|Heater|Humidifier|Dehumidifier|Purifier|Conditioner|Pump|Generator|Drill|Saw|Grinder|Sander|Welder|Compressor|Ladder|Toolbox|Wrench|Screwdriver|Hammer|Pliers|Cutter|Meter|Tester|Charger|Battery|Cable|Wire|Switch|Socket|Light|Bulb|Lamp|Ceiling|Wall|Floor|Table|Chair|Bed|Sofa|Cabinet|Shelf|Drawer|Door|Window|Curtain|Blind|Carpet|Rug|Pillow|Blanket|Sheet|Towel|Soap|Shampoo|Lotion|Cream|Perfume|Makeup|Brush|Comb|Mirror|Scale|Thermometer|Clock|Watch|Jewelry|Bag|Wallet|Belt|Shoes|Clothes|Hat|Gloves|Sunglasses|Umbrella|Toy|Game|Book|Magazine|Pen|Pencil|Paper|Notebook|Folder|Stapler|Clip|Tape|Glue|Ruler|Calculator|Calendar|Card|Gift|Flower|Plant|Food|Drink|Coffee|Tea|Juice|Water|Milk|Bread|Rice|Noodle|Meat|Fish|Vegetable|Fruit|Snack|Candy|Chocolate|Ice|Cream|Cake|Cookie|Pie|Pizza|Burger|Sandwich|Salad|Soup|Sauce|Oil|Vinegar|Salt|Sugar|Spice|Herb|Vitamin|Medicine|Pill|Tablet|Capsule|Syrup|Cream|Ointment|Bandage|Gauze|Mask|Glove|Syringe|Needle|Stethoscope|Thermometer|Blood|Pressure|Glucose|Oxygen|Wheelchair|Crutch|Walker|Bed|Mattress|Pillow|Blanket|Sheet|Towel|Soap|Shampoo|Lotion|Cream|Perfume|Makeup|Brush|Comb|Mirror|Scale|Thermometer|Clock|Watch|Jewelry|Bag|Wallet|Belt|Shoes|Clothes|Hat|Gloves|Sunglasses|Umbrella|Toy|Game|Book|Magazine|Pen|Pencil|Paper|Notebook|Folder|Stapler|Clip|Tape|Glue|Ruler|Calculator|Calendar|Card|Gift|Flower|Plant)',
            
            # Known brands (case-insensitive)
            r'\\b(SAMSUNG|LG|SONY|PANASONIC|SHARP|TCL|HAIER|NANO|DAIKIN|CARRIER|MITSUBISHI|TOSHIBA|PHILIPS|BRAUN|DYSON|ELECTROLUX|WHIRLPOOL|BOSCH|SIEMENS|MIELE|BEKO|HITACHI|SANYO|NATIONAL|AKAI|TEAC|ONKYO|YAMAHA|PIONEER|KENWOOD|ALPINE|CLARION|GARMIN|TOMTOM|APPLE|GOOGLE|MICROSOFT|AMAZON|FACEBOOK|TWITTER|INSTAGRAM|YOUTUBE|NETFLIX|SPOTIFY|UBER|GRAB|LAZADA|SHOPEE|TIKTOK|LINE|GREE|MIDEA|CHANGHONG|HISENSE|SKYWORTH|KONKA|GALANZ|ASAKI|MANDARIN|COTTO|CARRIER|HAIER|TEKA|WORLDTECH|SONAR|ELECKTA|GEKO|WOODTECT|MATALL|BOSCH|RTB|JOTUN|ALECTRIC|LAMOON|MAXIMUS|COOL|STYLER|EVE|KITCHEN|LUCKY|MISU|THAI|WATSADU)\\b',
            
            # Brand in parentheses
            r'\\(([A-Z][A-Za-z0-9\\s&]+?)\\)',
            
            # Brand after model numbers
            r'\\b(?:Model|รุ่น|Code|รหัส)[:\\s]+([A-Z][A-Za-z0-9\\s&]+?)\\b',
            
            # Brand patterns for specific TWD formats
            r'^([A-Z][A-Z0-9&\\s]+?)\\s+(?:Air Conditioner|Refrigerator|Washing Machine|Dryer|Dishwasher|Oven|Microwave|Blender|Mixer|Juicer|Toaster|Rice Cooker|Kettle|Iron|Vacuum|Fan|Heater|Humidifier|Dehumidifier|Purifier|Pump|Generator|Drill|Saw|Grinder|Sander|Welder|Compressor)'
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                potential_brand = match.group(1).strip()
                
                # Clean and validate the brand
                cleaned_brand = self._clean_brand_text(potential_brand)
                if cleaned_brand:
                    return cleaned_brand
        
        return None
    
    def _clean_brand_text(self, text: str) -> Optional[str]:
        """Clean and validate brand text"""
        if not text:
            return None
        
        # Clean whitespace
        text = str(text).strip()
        
        # Remove common noise words
        noise_words = [
            'SYNC', '3', 'IN', '1', 'CHARGER', 'SIZE', 'MAH', 'AIR', 'CONDITIONER',
            'INVERTER', 'WI-FI', 'BTU', 'REFRIGERATOR', 'DOOR', 'LITER', 'WASHING',
            'MACHINE', 'KG', 'FRONT', 'LOAD', 'TOP', 'LOAD', 'FULLY', 'AUTOMATIC',
            'SEMI', 'AUTOMATIC', 'DIGITAL', 'DISPLAY', 'CONTROL', 'PANEL', 'REMOTE',
            'CONTROL', 'TIMER', 'DELAY', 'START', 'CHILD', 'LOCK', 'SAFETY', 'DOOR',
            'LOCK', 'OVERFLOW', 'PROTECTION', 'UNBALANCE', 'DETECTION', 'SPIN',
            'SPEED', 'WASH', 'PROGRAM', 'RINSE', 'HOLD', 'QUICK', 'WASH', 'DELICATE',
            'WASH', 'HEAVY', 'DUTY', 'NORMAL', 'WASH', 'GENTLE', 'WASH', 'SOAK',
            'WASH', 'PRE', 'WASH', 'EXTRA', 'RINSE', 'FABRIC', 'SOFTENER', 'BLEACH',
            'DISPENSER', 'DETERGENT', 'DISPENSER', 'WATER', 'LEVEL', 'SENSOR',
            'TEMPERATURE', 'SENSOR', 'MOISTURE', 'SENSOR', 'LOAD', 'SENSOR', 'DOOR',
            'SENSOR', 'FILTER', 'INDICATOR', 'ERROR', 'CODE', 'DISPLAY', 'LED',
            'INDICATOR', 'BUZZER', 'ALARM', 'SOUND', 'VOLUME', 'ADJUSTMENT', 'MUTE',
            'FUNCTION', 'POWER', 'SAVING', 'MODE', 'ECO', 'MODE', 'ENERGY', 'STAR',
            'RATING', 'EFFICIENCY', 'RATING', 'NOISE', 'LEVEL', 'VIBRATION',
            'REDUCTION', 'ANTI', 'VIBRATION', 'PADS', 'ADJUSTABLE', 'LEGS', 'LEVELING',
            'FEET', 'TRANSPORT', 'BOLTS', 'INSTALLATION', 'KIT', 'USER', 'MANUAL',
            'WARRANTY', 'CARD', 'SERVICE', 'HOTLINE', 'CUSTOMER', 'SUPPORT', 'SPARE',
            'PARTS', 'ACCESSORIES', 'REPLACEMENT', 'PARTS', 'MAINTENANCE', 'SCHEDULE',
            'TROUBLESHOOTING', 'GUIDE', 'FAQ', 'FREQUENTLY', 'ASKED', 'QUESTIONS'
        ]
        
        # Remove noise words
        words = text.split()
        cleaned_words = []
        for word in words:
            if word.upper() not in noise_words and len(word) > 1:
                cleaned_words.append(word)
        
        if not cleaned_words:
            return None
        
        cleaned_text = ' '.join(cleaned_words)
        
        # Filter out obviously wrong brands
        invalid_brands = [
            'LED', 'LCD', 'TV', 'ทีวี', 'PRODUCT', 'สินค้า', 'ITEM', 'OTHER', 'อื่นๆ',
            'GENERAL', 'ทั่วไป', 'DEFAULT', 'NONE', 'N/A', 'NOT AVAILABLE', 'ไม่มี',
            'HOME', 'บ้าน', 'SYNC', 'CHARGER', 'SIZE', 'MAH', 'BTU', 'KG', 'LITER',
            'GALLON', 'WATT', 'VOLT', 'AMP', 'HZ', 'RPM', 'CFM', 'PSI', 'BAR',
            'METER', 'CENTIMETER', 'MILLIMETER', 'INCH', 'FOOT', 'YARD', 'MILE',
            'GRAM', 'KILOGRAM', 'POUND', 'OUNCE', 'SECOND', 'MINUTE', 'HOUR', 'DAY',
            'WEEK', 'MONTH', 'YEAR', 'DEGREE', 'CELSIUS', 'FAHRENHEIT', 'KELVIN',
            'PERCENT', 'PERCENTAGE', 'RATIO', 'PROPORTION', 'FRACTION', 'DECIMAL',
            'NUMBER', 'DIGIT', 'FIGURE', 'AMOUNT', 'QUANTITY', 'VOLUME', 'CAPACITY',
            'WEIGHT', 'MASS', 'DENSITY', 'PRESSURE', 'TEMPERATURE', 'HUMIDITY',
            'MOISTURE', 'DRYNESS', 'WETNESS', 'CLEANLINESS', 'DIRTINESS', 'BRIGHTNESS',
            'DARKNESS', 'LOUDNESS', 'QUIETNESS', 'SOFTNESS', 'HARDNESS', 'SMOOTHNESS',
            'ROUGHNESS', 'SHARPNESS', 'BLUNTNESS', 'THICKNESS', 'THINNESS', 'WIDTH',
            'NARROWNESS', 'HEIGHT', 'SHORTNESS', 'LENGTH', 'SHORTNESS', 'DEPTH',
            'SHALLOWNESS', 'SIZE', 'SMALLNESS', 'LARGENESS', 'BIGNESS', 'HUGENESS',
            'TININESS', 'SPEED', 'SLOWNESS', 'FASTNESS', 'QUICKNESS', 'SLOWNESS'
        ]
        
        if cleaned_text.upper() in invalid_brands:
            return None
        
        # Length validation
        if len(cleaned_text) < 2 or len(cleaned_text) > 30:
            return None
        
        # Return cleaned brand
        return cleaned_text.title()
    
    async def remove_invalid_twd_products(self, invalid_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Remove products with invalid URLs from database"""
        logger.info(f"Removing {len(invalid_products)} invalid TWD products...")
        
        results = {
            'total_attempted': len(invalid_products),
            'successful_removals': 0,
            'failed_removals': 0,
            'removed_products': []
        }
        
        for invalid_product in invalid_products:
            try:
                product = invalid_product['product']
                product_id = product['id']
                
                # Remove from database
                delete_result = self.supabase.client.table('products')\
                    .delete()\
                    .eq('id', product_id)\
                    .execute()
                
                if delete_result.data:
                    results['successful_removals'] += 1
                    results['removed_products'].append({
                        'id': product_id,
                        'sku': product['sku'],
                        'name': product['name'],
                        'issue': invalid_product['issue']
                    })
                    logger.info(f"Removed invalid product: {product['sku']}")
                else:
                    results['failed_removals'] += 1
                    logger.error(f"Failed to remove product: {product['sku']}")
                    
            except Exception as e:
                results['failed_removals'] += 1
                logger.error(f"Error removing product {product.get('sku', 'unknown')}: {str(e)}")
        
        logger.info(f"Removal completed: {results['successful_removals']}/{results['total_attempted']} successful")
        return results

async def main():
    """Main function to run the TWD fixes"""
    fixer = TWDUrlFixer()
    
    print("🔧 TWD URL AND BRAND FIXES")
    print("=" * 50)
    
    # Step 1: Identify invalid URLs
    print("\n🔍 Identifying invalid TWD URLs...")
    url_analysis = await fixer.identify_invalid_twd_urls()
    
    if 'error' in url_analysis:
        print(f"❌ Error: {url_analysis['error']}")
        return
    
    # Save URL analysis
    with open('twd_url_analysis.json', 'w') as f:
        json.dump(url_analysis, f, indent=2)
    
    print(f"📊 URL Analysis Results:")
    print(f"  Total TWD products: {url_analysis['total_twd_products']}")
    print(f"  Invalid URLs: {url_analysis['invalid_urls']}")
    print(f"  Valid URLs: {url_analysis['valid_urls']}")
    
    # Step 2: Fix brand extraction
    print("\n🏷️ Fixing TWD brand extraction...")
    brand_results = await fixer.fix_twd_brand_extraction()
    
    if 'error' in brand_results:
        print(f"❌ Error: {brand_results['error']}")
        return
    
    # Save brand fix results
    with open('twd_brand_fix_results.json', 'w') as f:
        json.dump(brand_results, f, indent=2)
    
    print(f"📊 Brand Fix Results:")
    print(f"  Total products with missing brands: {brand_results['total_products']}")
    print(f"  Potential fixes found: {brand_results['potential_fixes']}")
    print(f"  Successful fixes: {brand_results['successful_fixes']}")
    print(f"  Failed fixes: {brand_results['failed_fixes']}")
    
    # Step 3: Handle invalid URLs
    if url_analysis['invalid_urls'] > 0:
        print(f"\n🗑️ Found {url_analysis['invalid_urls']} products with invalid URLs")
        response = input("Remove these products from database? (y/n): ")
        
        if response.lower() == 'y':
            removal_results = await fixer.remove_invalid_twd_products(url_analysis['invalid_products'])
            
            # Save removal results
            with open('twd_removal_results.json', 'w') as f:
                json.dump(removal_results, f, indent=2)
            
            print(f"📊 Removal Results:")
            print(f"  Total attempted: {removal_results['total_attempted']}")
            print(f"  Successful removals: {removal_results['successful_removals']}")
            print(f"  Failed removals: {removal_results['failed_removals']}")
        else:
            print("Invalid products retained in database.")
    
    print(f"\n📁 Files created:")
    print(f"  - twd_url_analysis.json")
    print(f"  - twd_brand_fix_results.json")
    if url_analysis['invalid_urls'] > 0:
        print(f"  - twd_removal_results.json")
    
    print(f"\n✅ TWD fixes completed!")

if __name__ == "__main__":
    asyncio.run(main())