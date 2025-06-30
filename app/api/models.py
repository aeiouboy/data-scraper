"""
API models for request/response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


class ProductSearchRequest(BaseModel):
    """Product search request"""
    query: Optional[str] = None
    retailer_code: Optional[str] = None
    brands: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    on_sale_only: bool = False
    in_stock_only: bool = False
    sort_by: str = Field(default="name", pattern="^(name|price|discount|created_at)$")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ProductResponse(BaseModel):
    """Product response"""
    id: str
    sku: str
    name: str
    brand: Optional[str]
    category: Optional[str]
    current_price: Optional[float]
    original_price: Optional[float]
    discount_percentage: Optional[float]
    description: Optional[str]
    features: List[str]
    specifications: Dict[str, Any]
    availability: str
    images: List[str]
    url: str
    last_scraped: datetime
    created_at: datetime
    updated_at: Optional[datetime]


class ProductSearchResponse(BaseModel):
    """Product search response with pagination"""
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ScrapeJobRequest(BaseModel):
    """Scrape job request"""
    job_type: str = Field(pattern="^(product|category|search)$")
    target_url: Optional[str] = None
    urls: Optional[List[str]] = None
    max_pages: Optional[int] = Field(default=5, ge=1, le=200)
    max_concurrent: Optional[int] = Field(default=5, ge=1, le=10)
    retailer_code: Optional[str] = Field(None, description="Retailer code (HP, TWD, GH, etc)")
    category_code: Optional[str] = Field(None, description="Category code for targeted scraping")
    priority: Optional[str] = Field(default="normal", pattern="^(low|normal|high)$")


class ScrapeJobResponse(BaseModel):
    """Scrape job response"""
    id: str
    job_type: str
    status: str
    target_url: Optional[str]
    total_items: Optional[int]
    processed_items: Optional[int]
    success_items: Optional[int]
    failed_items: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class ScrapeJobListResponse(BaseModel):
    """List of scrape jobs"""
    jobs: List[ScrapeJobResponse]
    total: int
    active_jobs: int
    completed_jobs: int
    failed_jobs: int


class AnalyticsResponse(BaseModel):
    """Analytics dashboard response"""
    product_stats: Dict[str, Any]
    daily_stats: List[Dict[str, Any]]
    brand_distribution: List[Dict[str, Any]]
    category_distribution: List[Dict[str, Any]]
    price_distribution: Dict[str, Any]


class ConfigResponse(BaseModel):
    """Configuration response"""
    scraping_enabled: bool
    max_concurrent_jobs: int
    default_max_pages: int
    rate_limit_delay: int
    environments: List[str]
    current_environment: str


class ConfigUpdateRequest(BaseModel):
    """Configuration update request"""
    scraping_enabled: Optional[bool] = None
    max_concurrent_jobs: Optional[int] = Field(None, ge=1, le=10)
    default_max_pages: Optional[int] = Field(None, ge=1, le=100)
    rate_limit_delay: Optional[int] = Field(None, ge=1, le=60)


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str


class RetailerResponse(BaseModel):
    """Retailer configuration response"""
    id: str
    code: str
    name: str
    base_url: str
    market_position: str
    estimated_products: int
    rate_limit_delay: float
    max_concurrent: int
    focus_categories: List[str]
    price_volatility: str
    is_active: bool


class RetailerSummaryResponse(BaseModel):
    """Retailer summary with product statistics"""
    code: str
    name: str
    market_position: str
    actual_products: int
    in_stock_products: int
    priced_products: int
    avg_price: float
    min_price: float
    max_price: float
    ultra_critical_count: int
    high_value_count: int
    standard_count: int
    low_priority_count: int
    category_coverage_percentage: float
    brand_coverage_percentage: float
    last_scraped_at: Optional[str]


class RetailerStatsResponse(BaseModel):
    """Detailed retailer statistics"""
    retailer_code: str
    retailer_name: str
    total_products: int
    in_stock_products: int
    average_price: float
    unique_categories: int
    unique_brands: int
    price_distribution: Dict[str, int]
    top_categories: List[Dict[str, Any]]


class RetailerCategoryResponse(BaseModel):
    """Retailer category information"""
    code: str
    name: str
    name_th: str
    url: str
    estimated_products: Optional[int] = None
    actual_products: Optional[int] = None
    last_scraped: Optional[str] = None


class HealthMetricsResponse(BaseModel):
    """System health metrics"""
    overall_health: str  # 'healthy', 'warning', 'critical'
    success_rate_24h: float
    success_rate_7d: float
    avg_response_time: float
    total_jobs_24h: int
    failed_jobs_24h: int
    active_jobs: int
    queue_size: int
    last_updated: str


class RetailerHealthResponse(BaseModel):
    """Individual retailer health status"""
    retailer_code: str
    retailer_name: str
    status: str  # 'healthy', 'warning', 'critical', 'offline'
    success_rate: float
    avg_response_time: float
    last_successful_scrape: Optional[str] = None
    error_count_24h: int
    products_scraped_24h: int


class JobMetricsResponse(BaseModel):
    """Hourly job metrics for charts"""
    hour: str
    successful: int
    failed: int
    avg_duration: float