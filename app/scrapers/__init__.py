"""
Multi-retailer scraper package
"""
from app.scrapers.homepro_scraper import HomeProScraper
from app.scrapers.thaiwatsadu_scraper import ThaiWatsaduScraper
from app.scrapers.globalhouse_scraper import GlobalHouseScraper
from app.scrapers.dohome_scraper import DoHomeScraper
from app.scrapers.boonthavorn_scraper import BoonthavornScraper
from app.scrapers.megahome_scraper import MegaHomeScraper

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