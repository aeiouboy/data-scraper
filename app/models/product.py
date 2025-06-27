"""
Product models for Supabase integration
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
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