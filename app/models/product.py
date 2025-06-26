"""
Product models for Supabase integration
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class Product(BaseModel):
    """Product model matching Supabase schema"""
    
    id: Optional[str] = None
    sku: str
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    current_price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    discount_percentage: Optional[float] = None
    description: Optional[str] = None
    features: Optional[List[str]] = Field(default_factory=list)
    specifications: Optional[Dict[str, Any]] = Field(default_factory=dict)
    availability: str = "unknown"
    images: List[str] = Field(default_factory=list)
    url: str
    scraped_at: datetime = Field(default_factory=datetime.now)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator("sku")
    def validate_sku(cls, v):
        if not v or not v.strip():
            raise ValueError("SKU cannot be empty")
        return v.strip()
    
    @validator("current_price", "original_price")
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError("Price cannot be negative")
        return v
    
    @validator("discount_percentage")
    def calculate_discount(cls, v, values):
        if "current_price" in values and "original_price" in values:
            current = values.get("current_price")
            original = values.get("original_price")
            if current and original and original > current:
                return float(((original - current) / original) * 100)
        return v
    
    def to_supabase_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase insertion"""
        data = self.dict(exclude={"id", "created_at", "updated_at"})
        
        # Convert Decimal to float for JSON serialization
        if data.get("current_price"):
            data["current_price"] = float(data["current_price"])
        if data.get("original_price"):
            data["original_price"] = float(data["original_price"])
            
        # Convert lists and dicts to JSON-compatible format
        data["features"] = data.get("features", [])
        data["specifications"] = data.get("specifications", {})
        data["images"] = data.get("images", [])
        
        return data


class PriceHistory(BaseModel):
    """Price history tracking model"""
    
    id: Optional[str] = None
    product_id: str
    price: Decimal
    original_price: Optional[Decimal] = None
    discount_percentage: Optional[float] = None
    recorded_at: datetime = Field(default_factory=datetime.now)
    
    @validator("price")
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Price cannot be negative")
        return v
    
    def to_supabase_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase insertion"""
        data = self.dict(exclude={"id"})
        
        # Convert Decimal to float
        data["price"] = float(data["price"])
        if data.get("original_price"):
            data["original_price"] = float(data["original_price"])
            
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
    
    @validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Category name cannot be empty")
        return v.strip()


class ScrapeJob(BaseModel):
    """Scraping job tracking model"""
    
    id: Optional[str] = None
    job_type: str  # "discovery", "product", "category"
    status: str = "pending"  # pending, running, completed, failed
    target_url: Optional[str] = None
    total_items: int = 0
    processed_items: int = 0
    success_items: int = 0
    failed_items: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
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