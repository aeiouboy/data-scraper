#!/usr/bin/env python3
"""
Debug script to analyze HomePro pricing extraction in detail
"""
import asyncio
import sys
import os
sys.path.append('/Users/chongraktanaka/Documents/Project/ris data scrap')

import aiohttp
import ssl
from bs4 import BeautifulSoup
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_homepro_pricing():
    """Debug HomePro pricing extraction step by step"""
    
    url = "https://www.homepro.co.th/p/1288319"
    
    logger.info(f"Debugging HomePro pricing for: {url}")
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text(encoding='utf-8', errors='ignore')
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    logger.info(f"Successfully fetched page (content length: {len(content)})")
                    
                    # Debug: Look for all price-related elements
                    logger.info("=== DEBUGGING PRICE EXTRACTION ===")
                    
                    # Check for gtmPrice input
                    gtm_price_input = soup.find('input', {'id': re.compile(r'gtmPrice-\d+')})
                    if gtm_price_input:
                        logger.info(f"Found gtmPrice input: {gtm_price_input.get('value', 'N/A')}")
                    else:
                        logger.info("No gtmPrice input found")
                    
                    # Test HomePro-specific current price selectors
                    homepro_current_price_selectors = [
                        '.product-price .price-sale',
                        '.product-price .price-current',
                        '.price-now',
                        '.current-price',
                        '.sale-price',
                        '.product-price-value',
                        'span.price-sale',
                        'span.price-current',
                        '.price-container .price-sale',
                        '.price-container .price-current'
                    ]
                    
                    logger.info("Testing HomePro current price selectors:")
                    for selector in homepro_current_price_selectors:
                        element = soup.select_one(selector)
                        if element:
                            logger.info(f"  ✓ {selector}: {element.get_text(strip=True)}")
                        else:
                            logger.info(f"  ✗ {selector}: not found")
                    
                    # Test HomePro-specific original price selectors  
                    homepro_original_price_selectors = [
                        '.product-price .price-regular',
                        '.product-price .price-original',
                        '.original-price', 
                        '.regular-price', 
                        '.list-price', 
                        '.was-price',
                        'span.price-regular',
                        'span.price-original',
                        '.price-container .price-regular',
                        '.price-container .price-original'
                    ]
                    
                    logger.info("Testing HomePro original price selectors:")
                    for selector in homepro_original_price_selectors:
                        element = soup.select_one(selector)
                        if element:
                            logger.info(f"  ✓ {selector}: {element.get_text(strip=True)}")
                        else:
                            logger.info(f"  ✗ {selector}: not found")
                    
                    # Find all elements with price text
                    logger.info("=== ALL PRICE ELEMENTS ON PAGE ===")
                    price_elements = soup.find_all(['span', 'div', 'p'], string=re.compile(r'฿\s*[0-9,]+'))
                    
                    found_prices = []
                    for i, elem in enumerate(price_elements[:20]):  # Limit to first 20 for readability
                        price_text = elem.get_text(strip=True)
                        price_match = re.search(r'฿\s*([0-9,]+)', price_text)
                        if price_match:
                            try:
                                price_val = float(price_match.group(1).replace(',', ''))
                                found_prices.append(price_val)
                                logger.info(f"  {i+1}. Element: {elem.name}.{elem.get('class', [])} - Text: '{price_text}' - Price: ฿{price_val}")
                            except ValueError:
                                logger.info(f"  {i+1}. Element: {elem.name}.{elem.get('class', [])} - Text: '{price_text}' - Price: INVALID")
                    
                    # Show price analysis
                    logger.info("=== PRICE ANALYSIS ===")
                    unique_prices = sorted(list(set(found_prices)))
                    logger.info(f"All unique prices found: {unique_prices}")
                    
                    valid_prices = [p for p in unique_prices if 1000 <= p <= 100000]
                    logger.info(f"Valid prices (1000-100000): {valid_prices}")
                    
                    if valid_prices:
                        logger.info(f"Highest price (likely current): ฿{max(valid_prices)}")
                        if len(valid_prices) > 1:
                            logger.info(f"Second highest (potential original): ฿{sorted(valid_prices, reverse=True)[1]}")
                    
                    # Check what the actual page title says
                    title = soup.find('title')
                    if title:
                        logger.info(f"Page title: {title.get_text(strip=True)}")
                    
                    # Look for structured data (JSON-LD)
                    logger.info("=== CHECKING STRUCTURED DATA ===")
                    scripts = soup.find_all('script', type='application/ld+json')
                    for i, script in enumerate(scripts):
                        if script.string:
                            try:
                                import json
                                json_data = json.loads(script.string)
                                if isinstance(json_data, dict):
                                    logger.info(f"JSON-LD {i+1}: {json_data.get('@type', 'Unknown')}")
                                    if 'offers' in json_data:
                                        offers = json_data['offers']
                                        if isinstance(offers, dict):
                                            logger.info(f"  Price: {offers.get('price', 'N/A')}")
                                            logger.info(f"  Currency: {offers.get('priceCurrency', 'N/A')}")
                                        elif isinstance(offers, list):
                                            for j, offer in enumerate(offers):
                                                logger.info(f"  Offer {j+1}: {offer.get('price', 'N/A')} {offer.get('priceCurrency', 'N/A')}")
                            except json.JSONDecodeError:
                                logger.info(f"JSON-LD {i+1}: Invalid JSON")
                
                else:
                    logger.error(f"Failed to fetch page: HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"Error during debugging: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_homepro_pricing())