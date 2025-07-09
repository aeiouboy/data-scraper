"""
Enhanced domain models for improved product matching and price comparison
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class MatchConfidenceLevel(str, Enum):
    """Confidence levels for product matches"""
    EXACT = "exact"  # 95-100% - SKU/barcode match
    HIGH = "high"    # 80-95% - Strong name/brand/spec match
    MEDIUM = "medium"  # 65-80% - Good similarity, some differences
    LOW = "low"      # 50-65% - Possible match, needs validation
    NONE = "none"    # <50% - Not a match


class PriceVolatilityLevel(str, Enum):
    """Price volatility classifications"""
    STABLE = "stable"      # <5% variation
    LOW = "low"           # 5-10% variation
    MODERATE = "moderate"  # 10-20% variation
    HIGH = "high"         # 20-40% variation
    EXTREME = "extreme"   # >40% variation


class MatchFeature(BaseModel):
    """Individual feature used in matching"""
    name: str
    value: Any
    weight: float = Field(ge=0, le=1)
    matched: bool
    similarity_score: float = Field(ge=0, le=1)


class ConfidenceBreakdown(BaseModel):
    """Detailed confidence score breakdown"""
    overall: float = Field(ge=0, le=1, default=0)
    name_match: float = Field(ge=0, le=1)
    brand_match: float = Field(ge=0, le=1)
    spec_match: float = Field(ge=0, le=1)
    price_consistency: float = Field(ge=0, le=1)
    user_validation: float = Field(ge=0, le=1, default=0)
    
    def __init__(self, **data):
        """Calculate overall score before validation"""
        if 'overall' not in data:
            weights = {
                'name_match': 0.3,
                'brand_match': 0.25,
                'spec_match': 0.25,
                'price_consistency': 0.15,
                'user_validation': 0.05
            }
            
            total = sum(
                float(data.get(key, 0)) * weight 
                for key, weight in weights.items()
            )
            data['overall'] = round(total, 2)
        
        super().__init__(**data)


class NormalizedSpecifications(BaseModel):
    """Normalized product specifications"""
    dimensions: Optional[Dict[str, float]] = None  # width, height, depth in mm
    weight: Optional[float] = None  # in kg
    capacity: Optional[Dict[str, float]] = None  # volume, storage, etc.
    power: Optional[Dict[str, float]] = None  # watts, voltage, etc.
    features: List[str] = []  # normalized feature list
    technical_specs: Dict[str, Any] = {}  # other specs


class CanonicalProduct(BaseModel):
    """Canonical representation of a product across retailers"""
    normalized_name: str
    brand: str
    category: str
    subcategory: Optional[str] = None
    product_type: str
    model_number: Optional[str] = None
    key_features: List[str] = []
    specifications: Optional[NormalizedSpecifications] = None


class VariantMapping(BaseModel):
    """Maps product variants across retailers"""
    variant_type: str  # color, size, capacity, etc.
    variant_value: str
    is_primary: bool = False
    price_difference: Optional[float] = None


class PricePoint(BaseModel):
    """Single price observation"""
    price: float
    currency: str = "THB"
    timestamp: datetime
    is_promotion: bool = False
    promotion_details: Optional[str] = None
    stock_status: str = "in_stock"


class PriceTrend(BaseModel):
    """Price trend analysis"""
    period: str  # daily, weekly, monthly
    direction: str  # up, down, stable
    change_percentage: float
    average_price: float
    min_price: float
    max_price: float
    volatility_score: float = Field(ge=0, le=1)


class PriceAnomaly(BaseModel):
    """Detected price anomaly"""
    timestamp: datetime
    anomaly_type: str  # spike, drop, gradual_increase, gradual_decrease
    severity: str  # low, medium, high
    actual_price: float
    expected_range: tuple[float, float]
    confidence: float = Field(ge=0, le=1)


class SavingsOpportunity(BaseModel):
    """Identified savings opportunity"""
    amount: float
    percentage: float
    best_retailer: str
    compared_to_retailers: List[str]
    confidence: float = Field(ge=0, le=1)
    valid_until: Optional[datetime] = None


class PriceAnalysis(BaseModel):
    """Comprehensive price analysis"""
    current_best_price: float
    current_best_retailer: str
    savings_opportunity: Optional[SavingsOpportunity] = None
    volatility: PriceVolatilityLevel
    volatility_score: float = Field(ge=0, le=1)
    price_trends: List[PriceTrend] = []
    anomalies: List[PriceAnomaly] = []
    last_updated: datetime


class MatchMetadata(BaseModel):
    """Metadata about the matching process"""
    algorithm_version: str
    match_features: List[MatchFeature]
    mismatched_features: List[str] = []
    processing_time_ms: int
    data_sources: List[str] = []
    created_at: datetime
    last_validated: Optional[datetime] = None


class MatchedProduct(BaseModel):
    """Product matched from a specific retailer"""
    product_id: str
    retailer_code: str
    retailer_name: str
    product_name: str
    current_price: float
    url: str
    variant_mapping: Optional[VariantMapping] = None
    availability: str = "in_stock"
    last_updated: datetime


class ProductMatchGroup(BaseModel):
    """Group of matched products across retailers"""
    id: str
    canonical_product: CanonicalProduct
    matched_products: List[MatchedProduct]
    confidence: ConfidenceBreakdown
    match_metadata: MatchMetadata
    price_analysis: PriceAnalysis
    created_at: datetime
    updated_at: datetime
    
    @property
    def confidence_level(self) -> MatchConfidenceLevel:
        """Get confidence level based on overall score"""
        score = self.confidence.overall
        if score >= 0.95:
            return MatchConfidenceLevel.EXACT
        elif score >= 0.80:
            return MatchConfidenceLevel.HIGH
        elif score >= 0.65:
            return MatchConfidenceLevel.MEDIUM
        elif score >= 0.50:
            return MatchConfidenceLevel.LOW
        else:
            return MatchConfidenceLevel.NONE
    
    @property
    def retailer_count(self) -> int:
        """Number of retailers with this product"""
        return len(set(p.retailer_code for p in self.matched_products))
    
    @property
    def price_range(self) -> tuple[float, float]:
        """Get min and max prices"""
        prices = [p.current_price for p in self.matched_products]
        return (min(prices), max(prices)) if prices else (0, 0)


class MatchingAlgorithmConfig(BaseModel):
    """Configuration for matching algorithm"""
    min_name_similarity: float = 0.7
    min_brand_similarity: float = 0.8
    use_ml_matching: bool = True
    ml_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ml_threshold: float = 0.75
    price_variance_threshold: float = 0.5  # 50% max price difference
    require_same_category: bool = True
    fuzzy_match_threshold: float = 0.85


class MatchingRequest(BaseModel):
    """Request to match products"""
    product_ids: Optional[List[str]] = None
    retailer_codes: Optional[List[str]] = None
    category: Optional[str] = None
    min_confidence: float = Field(default=0.65, ge=0, le=1)
    include_variants: bool = True
    algorithm_config: Optional[MatchingAlgorithmConfig] = None


class MatchingResponse(BaseModel):
    """Response from matching operation"""
    match_groups: List[ProductMatchGroup]
    total_groups: int
    total_products: int
    processing_time_ms: int
    algorithm_version: str