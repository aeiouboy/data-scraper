"""
Category Explorer Module - Automatic category discovery and structure mapping
"""
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from urllib.parse import urlparse, urljoin
import hashlib

from app.services.firecrawl_client import FirecrawlClient
from app.services.supabase_service import SupabaseService
from app.config.retailers import retailer_manager, RetailerConfig

logger = logging.getLogger(__name__)


class CategoryNode:
    """Represents a category in the hierarchy"""
    
    def __init__(self, code: str, name: str, url: str, level: int = 0):
        self.code = code
        self.name = name
        self.url = url
        self.level = level
        self.parent: Optional[CategoryNode] = None
        self.children: List[CategoryNode] = []
        self.product_count = 0
        self.is_active = True
        self.metadata = {}
        
    def add_child(self, child: 'CategoryNode'):
        """Add a child category"""
        child.parent = self
        child.level = self.level + 1
        self.children.append(child)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'category_code': self.code,
            'category_name': self.name,
            'category_url': self.url,
            'level': self.level,
            'parent_category_id': self.parent.code if self.parent else None,
            'product_count': self.product_count,
            'is_active': self.is_active,
            'metadata': self.metadata
        }


class CategoryExplorer:
    """
    Automatically discovers and maps category structures for retailers
    """
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.discovered_categories: Dict[str, CategoryNode] = {}
        self.visited_urls: Set[str] = set()
        
    async def discover_all_categories(
        self, 
        retailer_code: str,
        max_depth: int = 3,
        max_categories: int = 500
    ) -> Dict[str, Any]:
        """
        Discover all categories for a retailer
        
        Args:
            retailer_code: Retailer identifier
            max_depth: Maximum depth to explore
            max_categories: Maximum categories to discover
            
        Returns:
            Discovery results with category tree
        """
        logger.info(f"Starting category discovery for {retailer_code}")
        
        # Get retailer config
        retailer_config = retailer_manager.get_retailer_by_code(retailer_code)
        if not retailer_config:
            raise ValueError(f"Unknown retailer: {retailer_code}")
            
        start_time = datetime.now()
        
        # Initialize discovery from home page
        async with FirecrawlClient() as client:
            root_categories = await self._discover_from_homepage(
                client, 
                retailer_config
            )
            
            # Explore each root category
            for category in root_categories:
                if len(self.discovered_categories) >= max_categories:
                    break
                    
                await self._explore_category_tree(
                    client,
                    retailer_config,
                    category,
                    current_depth=1,
                    max_depth=max_depth
                )
        
        # Build category tree
        category_tree = self._build_category_tree()
        
        # Save to database
        saved_count = await self._save_categories(retailer_code)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            'retailer_code': retailer_code,
            'discovered_count': len(self.discovered_categories),
            'saved_count': saved_count,
            'max_depth_reached': max_depth,
            'duration_seconds': duration,
            'category_tree': category_tree,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _discover_from_homepage(
        self, 
        client: FirecrawlClient,
        retailer_config: RetailerConfig
    ) -> List[CategoryNode]:
        """Discover root categories from homepage"""
        logger.info(f"Discovering categories from homepage: {retailer_config.base_url}")
        
        try:
            # Scrape homepage
            page_data = await client.scrape(retailer_config.base_url)
            if not page_data:
                logger.error("Failed to scrape homepage")
                return []
                
            # Extract navigation/menu links
            categories = []
            
            # Try multiple selector patterns
            nav_patterns = [
                # Common navigation patterns
                {'selector': 'nav a[href*="/c/"], nav a[href*="/category/"]', 'type': 'css'},
                {'selector': '//nav//a[contains(@href, "/c/") or contains(@href, "/category/")]', 'type': 'xpath'},
                {'selector': '[class*="menu"] a, [class*="nav"] a', 'type': 'css'},
                {'selector': '[id*="menu"] a, [id*="nav"] a', 'type': 'css'},
                # Specific patterns for Thai sites
                {'selector': 'a[href*="/th/c/"], a[href*="/en/c/"]', 'type': 'css'},
            ]
            
            html = page_data.get('html', '')
            links_found = []
            
            # Extract links using patterns
            for pattern in nav_patterns:
                if pattern['type'] == 'css':
                    # Use regex to find CSS selector matches
                    # This is simplified - in production, use proper HTML parser
                    links = self._extract_links_by_pattern(html, pattern['selector'])
                    links_found.extend(links)
            
            # Process found links
            for link in links_found:
                category = self._parse_category_link(link, retailer_config)
                if category and category.code not in self.discovered_categories:
                    categories.append(category)
                    self.discovered_categories[category.code] = category
                    
            logger.info(f"Found {len(categories)} root categories")
            return categories
            
        except Exception as e:
            logger.error(f"Error discovering homepage categories: {str(e)}")
            return []
    
    async def _explore_category_tree(
        self,
        client: FirecrawlClient,
        retailer_config: RetailerConfig,
        parent_category: CategoryNode,
        current_depth: int,
        max_depth: int
    ):
        """Recursively explore category tree"""
        if current_depth >= max_depth:
            return
            
        if parent_category.url in self.visited_urls:
            return
            
        self.visited_urls.add(parent_category.url)
        
        try:
            logger.info(f"Exploring category: {parent_category.name} (depth: {current_depth})")
            
            # Scrape category page
            page_data = await client.scrape(parent_category.url)
            if not page_data:
                return
                
            # Look for subcategories
            subcategory_links = self._find_subcategory_links(
                page_data, 
                parent_category.url,
                retailer_config
            )
            
            # Count products on this page
            product_count = self._count_products_on_page(page_data, retailer_config)
            parent_category.product_count = product_count
            
            # Process subcategories
            for link in subcategory_links:
                subcategory = self._parse_category_link(link, retailer_config)
                if subcategory and subcategory.code not in self.discovered_categories:
                    parent_category.add_child(subcategory)
                    self.discovered_categories[subcategory.code] = subcategory
                    
                    # Explore subcategory
                    await self._explore_category_tree(
                        client,
                        retailer_config,
                        subcategory,
                        current_depth + 1,
                        max_depth
                    )
                    
                    # Rate limiting
                    await asyncio.sleep(retailer_config.rate_limit_delay)
                    
        except Exception as e:
            logger.error(f"Error exploring category {parent_category.name}: {str(e)}")
    
    def _extract_links_by_pattern(self, html: str, pattern: str) -> List[Dict[str, str]]:
        """Extract links matching a pattern from HTML"""
        links = []
        
        # Simplified link extraction using regex
        # In production, use BeautifulSoup or lxml for proper parsing
        href_pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        
        for match in re.finditer(href_pattern, html, re.IGNORECASE):
            url = match.group(1)
            text = match.group(2).strip()
            
            # Check if URL matches our category patterns
            if any(cat_pattern in url for cat_pattern in ['/c/', '/category/', '/th/c/', '/en/c/']):
                links.append({
                    'url': url,
                    'text': text
                })
                
        return links
    
    def _parse_category_link(
        self, 
        link: Dict[str, str], 
        retailer_config: RetailerConfig
    ) -> Optional[CategoryNode]:
        """Parse a link into a CategoryNode"""
        url = link['url']
        text = link['text']
        
        # Make URL absolute
        if not url.startswith('http'):
            url = urljoin(retailer_config.base_url, url)
            
        # Extract category code from URL
        code = self._extract_category_code(url)
        if not code:
            return None
            
        # Clean category name
        name = self._clean_category_name(text)
        if not name:
            return None
            
        return CategoryNode(code=code, name=name, url=url)
    
    def _extract_category_code(self, url: str) -> Optional[str]:
        """Extract category code from URL"""
        # Common patterns: /c/CODE, /category/CODE, /th/c/CODE
        patterns = [
            r'/c/([A-Za-z0-9\-_]+)',
            r'/category/([A-Za-z0-9\-_]+)',
            r'/th/c/([A-Za-z0-9\-_]+)',
            r'/en/c/([A-Za-z0-9\-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1).upper()
                
        # Use URL hash as fallback
        return hashlib.md5(url.encode()).hexdigest()[:8].upper()
    
    def _clean_category_name(self, name: str) -> str:
        """Clean and normalize category name"""
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove common prefixes/suffixes
        remove_patterns = [
            r'^\d+\.\s*',  # Remove numbering
            r'\s*\(\d+\)$',  # Remove count in parentheses
            r'\s*>\s*$',  # Remove arrow indicators
        ]
        
        for pattern in remove_patterns:
            name = re.sub(pattern, '', name)
            
        return name.strip()
    
    def _find_subcategory_links(
        self, 
        page_data: Dict[str, Any],
        current_url: str,
        retailer_config: RetailerConfig
    ) -> List[Dict[str, str]]:
        """Find subcategory links on a category page"""
        links = []
        html = page_data.get('html', '')
        
        # Look for subcategory sections
        subcategory_patterns = [
            r'<div[^>]*class=["\'][^"\']*subcategor[^"\']*["\'][^>]*>(.*?)</div>',
            r'<ul[^>]*class=["\'][^"\']*categor[^"\']*["\'][^>]*>(.*?)</ul>',
            r'<nav[^>]*class=["\'][^"\']*breadcrumb[^"\']*["\'][^>]*>(.*?)</nav>',
        ]
        
        for pattern in subcategory_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                section_html = match.group(1)
                section_links = self._extract_links_by_pattern(section_html, 'a')
                
                # Filter to only category links
                for link in section_links:
                    if self._is_category_link(link['url'], current_url):
                        links.append(link)
                        
        return links
    
    def _is_category_link(self, url: str, current_url: str) -> bool:
        """Check if a URL is likely a category link"""
        # Must contain category indicators
        if not any(pattern in url for pattern in ['/c/', '/category/']):
            return False
            
        # Should not be the current page
        if url == current_url:
            return False
            
        # Should not be a product page
        if any(pattern in url for pattern in ['/p/', '/product/', 'sku=', 'id=']):
            return False
            
        return True
    
    def _count_products_on_page(
        self, 
        page_data: Dict[str, Any],
        retailer_config: RetailerConfig
    ) -> int:
        """Count products on a category page"""
        html = page_data.get('html', '')
        
        # Common product link patterns
        product_patterns = [
            r'href=["\'][^"\']*\/p\/\d+[^"\']*["\']',
            r'href=["\'][^"\']*\/product\/[^"\']+["\']',
            r'class=["\'][^"\']*product-item[^"\']*["\']',
            r'class=["\'][^"\']*product-card[^"\']*["\']',
        ]
        
        product_count = 0
        for pattern in product_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            product_count = max(product_count, len(matches))
            
        return product_count
    
    def _build_category_tree(self) -> List[Dict[str, Any]]:
        """Build hierarchical category tree"""
        # Find root categories (no parent)
        roots = []
        for category in self.discovered_categories.values():
            if category.parent is None:
                roots.append(self._build_tree_node(category))
                
        return roots
    
    def _build_tree_node(self, category: CategoryNode) -> Dict[str, Any]:
        """Build tree node with children"""
        node = {
            'code': category.code,
            'name': category.name,
            'url': category.url,
            'level': category.level,
            'product_count': category.product_count,
            'children': []
        }
        
        for child in category.children:
            node['children'].append(self._build_tree_node(child))
            
        return node
    
    async def _save_categories(self, retailer_code: str) -> int:
        """Save discovered categories to database"""
        saved_count = 0
        
        try:
            # Get existing categories
            existing = await self._get_existing_categories(retailer_code)
            existing_codes = {cat['category_code'] for cat in existing}
            
            # Prepare categories for saving
            for category in self.discovered_categories.values():
                try:
                    category_data = {
                        'retailer_code': retailer_code,
                        'category_code': category.code,
                        'category_name': category.name,
                        'category_url': category.url,
                        'level': category.level,
                        'product_count': category.product_count,
                        'is_active': True,
                        'is_auto_discovered': True,
                        'discovered_at': datetime.now().isoformat(),
                        'last_verified': datetime.now().isoformat()
                    }
                    
                    # Find parent ID if exists
                    if category.parent:
                        parent_result = self.supabase.client.table('retailer_categories').select('id').eq('retailer_code', retailer_code).eq('category_code', category.parent.code).execute()
                        if parent_result.data:
                            category_data['parent_category_id'] = parent_result.data[0]['id']
                    
                    # Insert or update
                    if category.code in existing_codes:
                        # Update existing
                        result = self.supabase.client.table('retailer_categories').update(category_data).eq('retailer_code', retailer_code).eq('category_code', category.code).execute()
                    else:
                        # Insert new
                        result = self.supabase.client.table('retailer_categories').insert(category_data).execute()
                        
                    if result.data:
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Error saving category {category.code}: {str(e)}")
                    
            # Mark missing categories as inactive
            for existing_cat in existing:
                if existing_cat['category_code'] not in self.discovered_categories:
                    self.supabase.client.table('retailer_categories').update({
                        'is_active': False,
                        'last_verified': datetime.now().isoformat()
                    }).eq('id', existing_cat['id']).execute()
                    
        except Exception as e:
            logger.error(f"Error saving categories: {str(e)}")
            
        return saved_count
    
    async def _get_existing_categories(self, retailer_code: str) -> List[Dict[str, Any]]:
        """Get existing categories from database"""
        try:
            result = self.supabase.client.table('retailer_categories').select('*').eq('retailer_code', retailer_code).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching existing categories: {str(e)}")
            return []
    
    async def discover_single_category(
        self,
        retailer_code: str,
        category_url: str
    ) -> Optional[Dict[str, Any]]:
        """Discover or refresh a single category"""
        logger.info(f"Discovering single category: {category_url}")
        
        retailer_config = retailer_manager.get_retailer_by_code(retailer_code)
        if not retailer_config:
            raise ValueError(f"Unknown retailer: {retailer_code}")
            
        async with FirecrawlClient() as client:
            page_data = await client.scrape(category_url)
            if not page_data:
                return None
                
            # Parse category info
            code = self._extract_category_code(category_url)
            
            # Extract name from page
            name = self._extract_category_name_from_page(page_data)
            
            # Count products
            product_count = self._count_products_on_page(page_data, retailer_config)
            
            # Find subcategories
            subcategories = self._find_subcategory_links(page_data, category_url, retailer_config)
            
            return {
                'retailer_code': retailer_code,
                'category_code': code,
                'category_name': name,
                'category_url': category_url,
                'product_count': product_count,
                'subcategory_count': len(subcategories),
                'subcategories': subcategories[:10]  # Sample of subcategories
            }
    
    def _extract_category_name_from_page(self, page_data: Dict[str, Any]) -> str:
        """Extract category name from page content"""
        # Try common patterns
        html = page_data.get('html', '')
        
        patterns = [
            r'<h1[^>]*>([^<]+)</h1>',
            r'<title>([^<]+)</title>',
            r'class=["\']category-name["\'][^>]*>([^<]+)<',
            r'class=["\']page-title["\'][^>]*>([^<]+)<',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                name = match.group(1)
                # Clean up common suffixes
                name = re.sub(r'\s*[\|\-]\s*[^|<-]+$', '', name)
                return self._clean_category_name(name)
                
        return "Unknown Category"