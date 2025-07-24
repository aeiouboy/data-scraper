"""
Retailer-specific CSS/XPath selectors for native scraping
"""
from typing import Dict, List, Any


# HomePro Selectors
HOMEPRO_SELECTORS = {
    'product_name': [
        'h1.product-title',
        '.product-name h1',
        'h1[data-testid="product-title"]',
        '.pdp-product-title h1',
        'css:.product-detail h1'
    ],
    'price': [
        '.price-current .price-value',
        '.product-price .current-price',
        '.price-display .final-price',
        '[data-testid="price-current"]',
        'regex:฿\\s*([0-9,]+(?:\\.[0-9]{1,2})?)'
    ],
    'brand': [
        '.product-brand',
        '.brand-name',
        '[data-testid="brand-name"]',
        '.pdp-brand-name'
    ],
    'sku': [
        '.product-sku',
        '.sku-code',
        '[data-testid="sku"]',
        'regex:SKU[:\\s]*([A-Z0-9\\-]+)'
    ],
    'category': [
        '.breadcrumb a:last-child',
        '.breadcrumb-item:last-child',
        '.category-path .last',
        'nav.breadcrumb a:not([href="/"])'
    ],
    'description': [
        '.product-description',
        '.product-details .description',
        '.pdp-description',
        '.product-info .description'
    ],
    'specifications': [
        '.product-specs table',
        '.specifications-table',
        '.product-attributes',
        '.spec-table'
    ],
    'images': [
        '.product-gallery img',
        '.product-images img',
        '.image-gallery img',
        '.pdp-gallery img'
    ],
    'availability': [
        '.stock-status',
        '.availability-status',
        '.product-availability',
        '[data-testid="stock-status"]'
    ],
    'rating': [
        '.rating-score',
        '.product-rating .score',
        '.review-rating',
        'regex:([0-5](?:\\.[0-9]+)?)\\s*(?:out of|/)\\s*5'
    ],
    'reviews_count': [
        '.review-count',
        '.rating-count',
        '.reviews-total',
        'regex:([0-9,]+)\\s*(?:reviews?|รีวิว)'
    ],
    'product_links': [
        '.product-item a',
        '.product-card a',
        '.item-link',
        '.product-tile a'
    ],
    'category_name': [
        'h1.category-title',
        '.category-header h1',
        '.page-title h1',
        '.category-name'
    ],
    'pagination': [
        '.pagination a',
        '.page-navigation a',
        '.pager a',
        '.pagination-links a'
    ],
    'total_products': [
        '.total-results',
        '.product-count',
        '.results-count',
        'regex:([0-9,]+)\\s*(?:products?|สินค้า)'
    ]
}

# Thai Watsadu Selectors
TWD_SELECTORS = {
    'product_name': [
        'h1.product-title',
        '.product-name h1',
        '.product-detail-title',
        'h1[data-product-title]'
    ],
    'price': [
        '.price-current',
        '.current-price',
        '.product-price .price',
        '.price-display',
        'regex:฿\\s*([0-9,]+(?:\\.[0-9]{1,2})?)'
    ],
    'brand': [
        '.brand-name',
        '.product-brand',
        '.manufacturer-name',
        '.brand-label'
    ],
    'sku': [
        '.product-code',
        '.sku-number',
        '.item-code',
        'regex:รหัสสินค้า[:\\s]*([A-Z0-9\\-]+)'
    ],
    'category': [
        '.breadcrumb a:last-child',
        '.category-breadcrumb a:last-child',
        '.navigation-path a:last-child'
    ],
    'description': [
        '.product-description',
        '.product-details',
        '.description-content',
        '.product-info'
    ],
    'specifications': [
        '.specifications table',
        '.product-specs',
        '.spec-list',
        '.attributes-table'
    ],
    'images': [
        '.product-image img',
        '.gallery-image img',
        '.product-photos img',
        '.image-slider img'
    ],
    'availability': [
        '.stock-info',
        '.availability-text',
        '.inventory-status',
        '.stock-display'
    ],
    'rating': [
        '.rating-value',
        '.product-rating',
        '.review-score',
        'regex:([0-5](?:\\.[0-9]+)?)\\s*ดาว'
    ],
    'reviews_count': [
        '.review-count',
        '.rating-total',
        '.reviews-number',
        'regex:([0-9,]+)\\s*รีวิว'
    ],
    'product_links': [
        '.product-item a[href*="/product/"]',
        '.product-card a',
        '.item-link',
        'a[href*="/category/"]'
    ],
    'category_name': [
        'h1.category-title',
        '.category-header h1',
        '.page-title'
    ],
    'pagination': [
        '.pagination a',
        '.page-nav a',
        '.pager-links a'
    ],
    'total_products': [
        '.result-count',
        '.total-items',
        'regex:([0-9,]+)\\s*รายการ'
    ]
}

# Global House Selectors
GLOBAL_HOUSE_SELECTORS = {
    'product_name': [
        'h1.product-title',
        '.product-name',
        '.item-title h1',
        '.product-header h1'
    ],
    'price': [
        '.price-current',
        '.product-price',
        '.current-price',
        '.price-value',
        'regex:฿\\s*([0-9,]+(?:\\.[0-9]{1,2})?)'
    ],
    'brand': [
        '.brand-name',
        '.product-brand',
        '.manufacturer',
        '.brand-label'
    ],
    'sku': [
        '.product-sku',
        '.sku-code',
        '.item-number',
        'regex:SKU[:\\s]*([A-Z0-9\\-]+)'
    ],
    'category': [
        '.breadcrumb a:last-child',
        '.category-path a:last-child',
        '.navigation a:last-child'
    ],
    'description': [
        '.product-description',
        '.product-details',
        '.description-text',
        '.product-info'
    ],
    'specifications': [
        '.product-specs',
        '.specifications',
        '.spec-table',
        '.attributes'
    ],
    'images': [
        '.product-gallery img',
        '.product-image img',
        '.gallery img',
        '.image-viewer img'
    ],
    'availability': [
        '.stock-status',
        '.availability',
        '.inventory-info',
        '.stock-level'
    ],
    'rating': [
        '.rating-score',
        '.product-rating',
        '.review-rating',
        'regex:([0-5](?:\\.[0-9]+)?)\\s*stars?'
    ],
    'reviews_count': [
        '.review-count',
        '.rating-count',
        '.reviews-total',
        'regex:([0-9,]+)\\s*reviews?'
    ],
    'product_links': [
        '.product-item a',
        '.product-card a',
        '.item-link',
        'a[href*="/product/"]'
    ],
    'category_name': [
        'h1.category-title',
        '.category-header h1',
        '.page-title'
    ],
    'pagination': [
        '.pagination a',
        '.page-links a',
        '.pager a'
    ],
    'total_products': [
        '.result-count',
        '.total-results',
        'regex:([0-9,]+)\\s*items?'
    ]
}

# DoHome Selectors
DOHOME_SELECTORS = {
    'product_name': [
        'h1.product-title',
        '.product-name h1',
        '.item-title',
        '.product-header h1'
    ],
    'price': [
        '.price-current',
        '.product-price',
        '.current-price',
        '.price-display',
        'regex:฿\\s*([0-9,]+(?:\\.[0-9]{1,2})?)'
    ],
    'brand': [
        '.brand-name',
        '.product-brand',
        '.manufacturer-name',
        '.brand-info'
    ],
    'sku': [
        '.product-code',
        '.sku-number',
        '.item-code',
        'regex:รหัส[:\\s]*([A-Z0-9\\-]+)'
    ],
    'category': [
        '.breadcrumb a:last-child',
        '.category-nav a:last-child',
        '.path-nav a:last-child'
    ],
    'description': [
        '.product-description',
        '.product-details',
        '.description-content',
        '.product-info'
    ],
    'specifications': [
        '.product-specs',
        '.specifications',
        '.spec-list',
        '.product-attributes'
    ],
    'images': [
        '.product-image img',
        '.gallery-image img',
        '.product-gallery img',
        '.image-display img'
    ],
    'availability': [
        '.stock-status',
        '.availability-info',
        '.inventory-status',
        '.stock-display'
    ],
    'rating': [
        '.rating-score',
        '.product-rating',
        '.review-rating',
        'regex:([0-5](?:\\.[0-9]+)?)\\s*(?:ดาว|stars?)'
    ],
    'reviews_count': [
        '.review-count',
        '.rating-total',
        '.reviews-number',
        'regex:([0-9,]+)\\s*(?:รีวิว|reviews?)'
    ],
    'product_links': [
        '.product-item a',
        '.product-card a',
        '.item-link',
        'a[href*="/product/"]'
    ],
    'category_name': [
        'h1.category-title',
        '.category-header h1',
        '.page-title'
    ],
    'pagination': [
        '.pagination a',
        '.page-nav a',
        '.pager a'
    ],
    'total_products': [
        '.result-count',
        '.total-items',
        'regex:([0-9,]+)\\s*(?:รายการ|items?)'
    ]
}

# Boonthavorn Selectors
BOONTHAVORN_SELECTORS = {
    'product_name': [
        'h1.product-title',
        '.product-name',
        '.item-title h1',
        '.product-header h1'
    ],
    'price': [
        '.price-current',
        '.product-price',
        '.current-price',
        '.price-value',
        'regex:฿\\s*([0-9,]+(?:\\.[0-9]{1,2})?)'
    ],
    'brand': [
        '.brand-name',
        '.product-brand',
        '.manufacturer',
        '.brand-info'
    ],
    'sku': [
        '.product-sku',
        '.sku-code',
        '.item-number',
        'regex:รหัสสินค้า[:\\s]*([A-Z0-9\\-]+)'
    ],
    'category': [
        '.breadcrumb a:last-child',
        '.category-path a:last-child',
        '.navigation a:last-child'
    ],
    'description': [
        '.product-description',
        '.product-details',
        '.description-text',
        '.product-info'
    ],
    'specifications': [
        '.product-specs',
        '.specifications',
        '.spec-table',
        '.product-attributes'
    ],
    'images': [
        '.product-gallery img',
        '.product-image img',
        '.gallery img',
        '.image-viewer img'
    ],
    'availability': [
        '.stock-status',
        '.availability',
        '.inventory-info',
        '.stock-level'
    ],
    'rating': [
        '.rating-score',
        '.product-rating',
        '.review-rating',
        'regex:([0-5](?:\\.[0-9]+)?)\\s*(?:ดาว|stars?)'
    ],
    'reviews_count': [
        '.review-count',
        '.rating-count',
        '.reviews-total',
        'regex:([0-9,]+)\\s*(?:รีวิว|reviews?)'
    ],
    'product_links': [
        '.product-item a',
        '.product-card a',
        '.item-link',
        'a[href*="/product/"]'
    ],
    'category_name': [
        'h1.category-title',
        '.category-header h1',
        '.page-title'
    ],
    'pagination': [
        '.pagination a',
        '.page-links a',
        '.pager a'
    ],
    'total_products': [
        '.result-count',
        '.total-results',
        'regex:([0-9,]+)\\s*(?:รายการ|items?)'
    ]
}

# MegaHome Selectors
MEGAHOME_SELECTORS = {
    'product_name': [
        'h1.product-title',
        '.product-name h1',
        '.item-title',
        '.product-header h1'
    ],
    'price': [
        '.price-current',
        '.product-price',
        '.current-price',
        '.price-display',
        'regex:฿\\s*([0-9,]+(?:\\.[0-9]{1,2})?)'
    ],
    'brand': [
        '.brand-name',
        '.product-brand',
        '.manufacturer-name',
        '.brand-label'
    ],
    'sku': [
        '.product-code',
        '.sku-number',
        '.item-code',
        'regex:รหัสสินค้า[:\\s]*([A-Z0-9\\-]+)'
    ],
    'category': [
        '.breadcrumb a:last-child',
        '.category-breadcrumb a:last-child',
        '.navigation-path a:last-child'
    ],
    'description': [
        '.product-description',
        '.product-details',
        '.description-content',
        '.product-info'
    ],
    'specifications': [
        '.product-specs',
        '.specifications',
        '.spec-list',
        '.product-attributes'
    ],
    'images': [
        '.product-image img',
        '.gallery-image img',
        '.product-gallery img',
        '.image-slider img'
    ],
    'availability': [
        '.stock-status',
        '.availability-info',
        '.inventory-status',
        '.stock-display'
    ],
    'rating': [
        '.rating-score',
        '.product-rating',
        '.review-rating',
        'regex:([0-5](?:\\.[0-9]+)?)\\s*(?:ดาว|stars?)'
    ],
    'reviews_count': [
        '.review-count',
        '.rating-total',
        '.reviews-number',
        'regex:([0-9,]+)\\s*(?:รีวิว|reviews?)'
    ],
    'product_links': [
        '.product-item a',
        '.product-card a',
        '.item-link',
        'a[href*="/product/"]'
    ],
    'category_name': [
        'h1.category-title',
        '.category-header h1',
        '.page-title'
    ],
    'pagination': [
        '.pagination a',
        '.page-nav a',
        '.pager-links a'
    ],
    'total_products': [
        '.result-count',
        '.total-items',
        'regex:([0-9,]+)\\s*(?:รายการ|items?)'
    ]
}

# Mapping of retailer codes to selectors
RETAILER_SELECTORS = {
    'HP': HOMEPRO_SELECTORS,
    'TWD': TWD_SELECTORS,
    'GH': GLOBAL_HOUSE_SELECTORS,
    'DH': DOHOME_SELECTORS,
    'BT': BOONTHAVORN_SELECTORS,
    'MH': MEGAHOME_SELECTORS
}

# Search URL patterns for each retailer
SEARCH_PATTERNS = {
    'HP': {
        'url_pattern': '/search?q={query}',
        'query_parameter': 'q',
        'results_per_page': 20
    },
    'TWD': {
        'url_pattern': '/search?keyword={query}',
        'query_parameter': 'keyword',
        'results_per_page': 24
    },
    'GH': {
        'url_pattern': '/search?q={query}',
        'query_parameter': 'q',
        'results_per_page': 16
    },
    'DH': {
        'url_pattern': '/search?q={query}',
        'query_parameter': 'q',
        'results_per_page': 20
    },
    'BT': {
        'url_pattern': '/search?q={query}',
        'query_parameter': 'q',
        'results_per_page': 12
    },
    'MH': {
        'url_pattern': '/search?q={query}',
        'query_parameter': 'q',
        'results_per_page': 20
    }
}

# Product URL patterns for filtering
PRODUCT_URL_PATTERNS = {
    'HP': ['/p/', '/product/', '/products/'],
    'TWD': ['/product/', '/item/', '/p/'],
    'GH': ['/product/', '/item/', '/p/'],
    'DH': ['/product/', '/item/', '/p/'],
    'BT': ['/product/', '/item/', '/p/'],
    'MH': ['/product/', '/item/', '/p/']
}


def get_retailer_selectors(retailer_code: str) -> Dict[str, List[str]]:
    """Get selectors for a specific retailer"""
    return RETAILER_SELECTORS.get(retailer_code, {})


def get_search_patterns(retailer_code: str) -> Dict[str, Any]:
    """Get search patterns for a specific retailer"""
    return SEARCH_PATTERNS.get(retailer_code, {})


def get_product_url_patterns(retailer_code: str) -> List[str]:
    """Get product URL patterns for a specific retailer"""
    return PRODUCT_URL_PATTERNS.get(retailer_code, [])


def update_retailer_config_with_selectors(retailer_config: Dict[str, Any]) -> Dict[str, Any]:
    """Update retailer configuration with selectors and patterns"""
    retailer_code = retailer_config.get('code', '')
    
    # Add selectors
    if 'selectors' not in retailer_config:
        retailer_config['selectors'] = {}
    
    retailer_selectors = get_retailer_selectors(retailer_code)
    retailer_config['selectors'].update(retailer_selectors)
    
    # Add search patterns
    if 'search_patterns' not in retailer_config:
        retailer_config['search_patterns'] = {}
    
    search_patterns = get_search_patterns(retailer_code)
    retailer_config['search_patterns'].update(search_patterns)
    
    # Add product URL patterns
    if 'product_url_patterns' not in retailer_config:
        retailer_config['product_url_patterns'] = []
    
    product_patterns = get_product_url_patterns(retailer_code)
    retailer_config['product_url_patterns'].extend(product_patterns)
    
    return retailer_config