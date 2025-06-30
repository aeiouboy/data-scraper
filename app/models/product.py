"""
Product models for Supabase integration
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


class Product(BaseModel):
    """Product model matching Supabase schema - Multi-retailer enhanced"""
    
    id: Optional[str] = None
    sku: str
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    unified_category: Optional[str] = None  # Standardized category across retailers
    current_price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    discount_percentage: Optional[float] = None
    description: Optional[str] = None
    features: Optional[List[str]] = Field(default_factory=list)
    specifications: Optional[Dict[str, Any]] = Field(default_factory=dict)
    availability: str = "unknown"
    images: List[str] = Field(default_factory=list)
    url: str
    
    # Multi-retailer fields
    retailer_code: str = "HP"  # HP, TWD, GH, DH, BT, MH
    retailer_name: str = "HomePro"
    retailer_sku: Optional[str] = None  # Retailer-specific SKU
    product_hash: Optional[str] = None  # For product matching across retailers
    monitoring_tier: str = "standard"  # ultra_critical, high_value, standard, low_priority
    
    # Timestamps
    scraped_at: datetime = Field(default_factory=datetime.now)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v):
        if not v or not v.strip():
            raise ValueError("SKU cannot be empty")
        return v.strip()
    
    @field_validator("current_price", "original_price")
    @classmethod
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError("Price cannot be negative")
        return v
    
    @field_validator("discount_percentage")
    @classmethod
    def calculate_discount(cls, v, info):
        if info.data.get("current_price") and info.data.get("original_price"):
            current = info.data.get("current_price")
            original = info.data.get("original_price")
            if current and original and original > current:
                return float(((original - current) / original) * 100)
        return v
    
    def to_supabase_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase insertion"""
        data = self.model_dump(exclude={"id", "created_at", "updated_at"})
        
        # Convert Decimal to float for JSON serialization
        if data.get("current_price"):
            data["current_price"] = float(data["current_price"])
        if data.get("original_price"):
            data["original_price"] = float(data["original_price"])
            
        # Convert datetime to ISO format string
        if data.get("scraped_at"):
            data["scraped_at"] = data["scraped_at"].isoformat()
            
        # Convert lists and dicts to JSON-compatible format
        data["features"] = data.get("features", [])
        data["specifications"] = data.get("specifications", {})
        data["images"] = data.get("images", [])
        
        # Ensure multi-retailer fields are included
        data["retailer_code"] = data.get("retailer_code", "HP")
        data["retailer_name"] = data.get("retailer_name", "HomePro")
        data["monitoring_tier"] = data.get("monitoring_tier", "standard")
        
        return data


class PriceHistory(BaseModel):
    """Price history tracking model"""
    
    id: Optional[str] = None
    product_id: str
    price: Decimal
    original_price: Optional[Decimal] = None
    discount_percentage: Optional[float] = None
    recorded_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Price cannot be negative")
        return v
    
    def to_supabase_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase insertion"""
        data = self.model_dump(exclude={"id"})
        
        # Convert Decimal to float
        data["price"] = float(data["price"])
        if data.get("original_price"):
            data["original_price"] = float(data["original_price"])
            
        # Convert datetime to ISO format string
        if data.get("recorded_at"):
            data["recorded_at"] = data["recorded_at"].isoformat()
            
        return data


class Category(BaseModel):
    """Product category model"""
    
    id: Optional[str] = None
    name: str
    name_en: Optional[str] = None
    parent_id: Optional[str] = None
    path: Optional[str] = None
    level: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Category name cannot be empty")
        return v.strip()


class ProductMatch(BaseModel):
    """Cross-retailer product matching model"""
    
    id: Optional[str] = None
    master_product_id: str  # Primary product ID
    matched_product_ids: List[str] = Field(default_factory=list)  # Related products from other retailers
    match_confidence: float = 0.0  # 0.0-1.0 confidence score
    match_criteria: Dict[str, Any] = Field(default_factory=dict)  # What criteria were used for matching
    
    # Product attributes for matching
    normalized_name: str
    normalized_brand: Optional[str] = None
    unified_category: str
    key_specifications: Dict[str, Any] = Field(default_factory=dict)
    
    # Price comparison data
    price_range_min: Optional[Decimal] = None
    price_range_max: Optional[Decimal] = None
    best_price_retailer: Optional[str] = None
    price_variance_percentage: Optional[float] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_supabase_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase insertion"""
        data = self.model_dump(exclude={"id", "created_at", "updated_at"})
        
        # Convert Decimal to float
        if data.get("price_range_min"):
            data["price_range_min"] = float(data["price_range_min"])
        if data.get("price_range_max"):
            data["price_range_max"] = float(data["price_range_max"])
            
        return data


class ScrapeJob(BaseModel):
    """Scraping job tracking model"""
    
    id: Optional[str] = None
    job_type: str  # "discovery", "product", "category"
    status: str = "pending"  # pending, running, completed, failed
    target_url: Optional[str] = None
    retailer_code: Optional[str] = None  # HP, TWD, GH, DH, BT, MH
    total_items: int = 0
    processed_items: int = 0
    success_items: int = 0
    failed_items: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    created_at: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.processed_items == 0:
            return 0.0
        return (self.success_items / self.processed_items) * 100
    
    @property
    def is_running(self) -> bool:
        """Check if job is still running"""
        return self.status in ["pending", "running"]
    
    def to_supabase_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase insertion"""
        data = self.model_dump(exclude={"id", "created_at"})
        
        # Calculate duration if both timestamps are available
        if data.get("started_at") and data.get("completed_at") and not data.get("duration_seconds"):
            started = data["started_at"]
            completed = data["completed_at"]
            if isinstance(started, datetime) and isinstance(completed, datetime):
                data["duration_seconds"] = int((completed - started).total_seconds())
        
        # Convert datetime to ISO format string
        for field in ["started_at", "completed_at"]:
            if data.get(field) and isinstance(data[field], datetime):
                data[field] = data[field].isoformat()
                
        return data