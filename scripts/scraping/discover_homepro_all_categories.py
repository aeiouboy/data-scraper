"""
Discover ALL HomePro categories
"""
import asyncio
import aiohttp
from src.services.firecrawl_client import FirecrawlClient
from dotenv import load_dotenv
import json

load_dotenv()

async def discover_homepro_categories():
    """Discover all HomePro categories using Firecrawl"""
    print("Discovering ALL HomePro Categories")
    print("=" * 80)
    
    firecrawl = FirecrawlClient()
    base_url = "https://www.homepro.co.th"
    
    all_categories = set()
    
    # Known HomePro category codes (comprehensive list)
    known_codes = [
        # Main categories from current config
        'LIG', 'PAI', 'FUR', 'APP', 'TVA', 'KIT', 'BAT', 'HHP', 'CON', 'ELT',
        'DOW', 'TOO', 'OUT', 'BED', 'SPO', 'BEA', 'MOM', 'HEA', 'PET', 'ATM',
        'GAR', 'OFF', 'CLO',
        
        # Additional categories to check
        'STA', 'TEX', 'DEC', 'SAF', 'PLU', 'TIL', 'FLO', 'CEI', 'WAL', 'ROO',
        'INS', 'HVA', 'POW', 'NET', 'PHO', 'COM', 'AUD', 'CAM', 'GAM', 'TOY',
        'BOO', 'MUS', 'SPT', 'FIT', 'BIK', 'CAR', 'MOT', 'STO', 'ORG', 'SEC',
        'SMH', 'ENT', 'HOB', 'CRA', 'ART', 'GIF', 'STA', 'SCH', 'FAB', 'SEW',
        'WED', 'PAR', 'CHR', 'HAL', 'NEW', 'VAL', 'EAS', 'SUM', 'WIN', 'AUT',
        'SPR', 'BTS', 'HOL', 'PRO', 'CLE', 'SAL', 'DEA', 'FEA', 'TRE', 'ECO',
        'GRE', 'SUS', 'REC', 'DIY', 'REP', 'MAI', 'UPG', 'REN', 'BUI', 'IND',
        'COM', 'AGR', 'FAR', 'MED', 'LAB', 'SAF', 'SEC', 'FIR', 'EME', 'DIS',
        'WEA', 'OUT', 'CAM', 'TRA', 'LUG', 'BAG', 'TEN', 'SLE', 'HIK', 'FIS',
        'HUN', 'BOA', 'MAR', 'BEA', 'POO', 'SPA', 'GYM', 'YOG', 'RUN', 'CYC',
        'GOL', 'TEN', 'BAD', 'TAB', 'SOC', 'BAS', 'VOL', 'BOX', 'WRE', 'MAR',
        'KAR', 'JUD', 'TAE', 'MUA', 'KUN', 'AIK', 'KEN', 'CAP', 'FEN', 'ARC',
        'SHO', 'BOW', 'DAR', 'BIL', 'CHE', 'BRI', 'POK', 'MAH', 'SCR', 'CRO',
        'KNI', 'PUZ', 'BOA', 'CAR', 'VID', 'COM', 'TAB', 'MOB', 'LAP', 'DES',
        'PRI', 'SCA', 'MON', 'KEY', 'MOU', 'WEB', 'MIC', 'SPE', 'HEA', 'EAR',
        'CAS', 'BAT', 'CHA', 'CAB', 'ADA', 'MEM', 'STO', 'HAR', 'SSD', 'USB',
        'HUB', 'ROU', 'MOD', 'SWI', 'ACC', 'NET', 'WIF', 'BLU', 'IOT', 'SMA'
    ]
    
    # Add all known codes
    for code in known_codes:
        all_categories.add(f"{base_url}/c/{code}")
    
    # Try to discover more from main page
    try:
        result = await firecrawl.scrape(base_url)
        if result:
            links = result.get('linksOnPage', result.get('links', []))
            for link in links:
                if isinstance(link, dict):
                    href = link.get('url', link.get('href', ''))
                else:
                    href = str(link)
                
                if '/c/' in href and 'homepro.co.th' in href:
                    all_categories.add(href)
    except Exception as e:
        print(f"Error with Firecrawl: {e}")
    
    # Additional systematic check for 3-letter codes
    print("\nChecking additional 3-letter category codes...")
    async with aiohttp.ClientSession() as session:
        # Common prefixes
        prefixes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 
                   'N', 'O', 'P', 'R', 'S', 'T', 'U', 'V', 'W', 'Y', 'Z']
        
        for prefix in prefixes:
            for i in range(65, 91):  # A-Z
                for j in range(65, 91):  # A-Z
                    code = f"{prefix}{chr(i)}{chr(j)}"
                    url = f"{base_url}/c/{code}"
                    
                    try:
                        async with session.head(url, timeout=2, allow_redirects=False) as response:
                            if response.status == 200 or response.status == 301:
                                all_categories.add(url)
                                print(f"✓ Found: {code}")
                        await asyncio.sleep(0.05)  # Rate limiting
                    except:
                        pass
    
    # Convert to sorted list
    final_categories = sorted(list(all_categories))
    
    # Extract just the codes for display
    codes_only = []
    for url in final_categories:
        if '/c/' in url:
            code = url.split('/c/')[-1]
            codes_only.append((code, url))
    
    codes_only.sort(key=lambda x: x[0])
    
    print(f"\n{'='*80}")
    print(f"TOTAL HOMEPRO CATEGORIES FOUND: {len(codes_only)}")
    print("="*80)
    
    # Save results
    with open('homepro_all_categories.json', 'w') as f:
        json.dump([{"code": code, "url": url} for code, url in codes_only], f, indent=2)
    
    # Generate category_urls
    print("\nCategory URLs for retailers.py:")
    print("-" * 80)
    print("category_urls=[")
    for code, url in codes_only:
        print(f'    "{url}",  # {code}')
    print("],")
    
    return codes_only

async def main():
    await discover_homepro_categories()

if __name__ == "__main__":
    asyncio.run(main())