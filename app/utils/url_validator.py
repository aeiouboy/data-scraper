"""
URL validation utilities
"""
import re
from urllib.parse import urlparse, parse_qs
from typing import Optional, List


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid URL
    """
    if not url:
        return False
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_product_url(url: str, base_url: str) -> bool:
    """
    Check if URL is a valid product URL for the retailer
    
    Args:
        url: URL to validate
        base_url: Base URL of the retailer
        
    Returns:
        True if valid product URL
    """
    if not is_valid_url(url):
        return False
    
    # Must be from the same domain
    if not url.startswith(base_url):
        return False
    
    # Check for common product URL patterns
    product_patterns = [
        r'/p/[\w\-]+',           # /p/product-id
        r'/product/[\w\-]+',     # /product/product-id
        r'/product/[^/]+',       # /product/any-characters (for Thai Watsadu & Global House)
        r'/item/[\w\-]+',        # /item/product-id
        r'/[\w\-]+\.html',       # /product-name.html
        r'/pd/[\w\-]+',          # /pd/product-id
        r'/products/[\w\-]+',    # /products/product-id
        r'-i\.\d+$',             # Global House pattern ending with -i.numeric-id
    ]
    
    path = urlparse(url).path
    
    for pattern in product_patterns:
        if re.search(pattern, path):
            return True
    
    # Check query parameters for product indicators
    query_params = parse_qs(urlparse(url).query)
    product_param_keys = ['id', 'pid', 'product_id', 'item_id', 'sku']
    
    for key in product_param_keys:
        if key in query_params:
            return True
    
    return False


def is_category_url(url: str) -> bool:
    """
    Check if URL is a category page
    
    Args:
        url: URL to check
        
    Returns:
        True if category URL
    """
    if not is_valid_url(url):
        return False
    
    # Common category patterns
    category_patterns = [
        r'/c/[\w\-]+',           # /c/category-name
        r'/category/[\w\-]+',    # /category/category-name
        r'/categories/[\w\-]+',  # /categories/category-name
        r'/shop/[\w\-]+',        # /shop/category-name
        r'/[\w\-]+/c-[\d]+',     # /category-name/c-123
    ]
    
    path = urlparse(url).path
    
    for pattern in category_patterns:
        if re.search(pattern, path):
            return True
    
    return False


def normalize_url(url: str) -> str:
    """
    Normalize URL for consistency
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
    """
    if not url:
        return ""
    
    # Parse URL
    parsed = urlparse(url)
    
    # Remove trailing slash
    path = parsed.path.rstrip('/')
    
    # Remove common tracking parameters
    query_params = parse_qs(parsed.query)
    tracking_params = [
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
        'gclid', 'fbclid', 'ref', 'source', 'aff_id'
    ]
    
    for param in tracking_params:
        query_params.pop(param, None)
    
    # Rebuild query string
    if query_params:
        query_parts = []
        for key, values in sorted(query_params.items()):
            for value in values:
                query_parts.append(f"{key}={value}")
        query = '&'.join(query_parts)
    else:
        query = ''
    
    # Rebuild URL
    normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
    if query:
        normalized += f"?{query}"
    
    return normalized


def extract_product_id_from_url(url: str) -> Optional[str]:
    """
    Extract product ID from URL
    
    Args:
        url: Product URL
        
    Returns:
        Product ID or None
    """
    if not url:
        return None
    
    # Try path patterns first
    path = urlparse(url).path
    
    # Common patterns
    patterns = [
        r'/p/([\w\-]+)',         # /p/ABC123
        r'/product/([\w\-]+)',   # /product/ABC123
        r'/item/([\w\-]+)',      # /item/ABC123
        r'/pd/([\w\-]+)',        # /pd/ABC123
        r'/([\w\-]+)\.html',     # /product-id.html
    ]
    
    for pattern in patterns:
        match = re.search(pattern, path)
        if match:
            return match.group(1)
    
    # Try query parameters
    query_params = parse_qs(urlparse(url).query)
    
    for key in ['id', 'pid', 'product_id', 'item_id', 'sku']:
        if key in query_params and query_params[key]:
            return query_params[key][0]
    
    # Last resort: use last path segment
    segments = path.strip('/').split('/')
    if segments and segments[-1]:
        return segments[-1]
    
    return None