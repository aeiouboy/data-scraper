"""
Multi-retailer scraper package
"""
from src.scrapers.homepro_scraper import HomeProScraper
from src.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from src.scrapers.globalhouse_scraper import GlobalHouseScraper
from src.scrapers.dohome_scraper import DoHomeScraper
from src.scrapers.boonthavorn_scraper import BoonthavornScraper
from src.scrapers.megahome_scraper import MegaHomeScraper

__all__ = [
    'HomeProScraper',
    'ThaiWatsaduScraper',
    'GlobalHouseScraper',
    'DoHomeScraper',
    'BoonthavornScraper',
    'MegaHomeScraper',
    'get_scraper',
    'get_scraper_for_retailer',
]

# Scraper factory
def get_scraper(retailer_code: str):
    """Get scraper instance for a specific retailer"""
    scrapers = {
        'HP': HomeProScraper,
        'TWD': ThaiWatsaduScraper,
        'GH': GlobalHouseScraper,
        'DH': DoHomeScraper,
        'BT': BoonthavornScraper,
        'MH': MegaHomeScraper,
    }
    
    scraper_class = scrapers.get(retailer_code.upper())
    if not scraper_class:
        raise ValueError(f"No scraper implemented for retailer: {retailer_code}")
    
    return scraper_class()


# Alias for backward compatibility
get_scraper_for_retailer = get_scraper