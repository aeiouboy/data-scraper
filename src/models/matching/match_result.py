"""
Database models for matching results
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from uuid import UUID


class MatchingMethod(str, Enum):
    """Enumeration of matching methods"""
    NAME = "name"
    SKU = "sku"
    BRAND = "brand"
    SPECIFICATIONS = "specifications"
    HYBRID = "hybrid"


class MatchStatus(str, Enum):
    """Enumeration of match statuses"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class MatchResult(BaseModel):
    """Model for matching results"""
    id: Optional[UUID] = None
    source_product_id: UUID = Field(..., description="ID of the source product")
    matched_product_id: UUID = Field(..., description="ID of the matched product")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    matching_method: MatchingMethod = Field(..., description="Method used for matching")
    status: MatchStatus = Field(default=MatchStatus.PENDING, description="Status of the match")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        """Ensure confidence score is between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return round(v, 2)  # Round to 2 decimal places
    
    @validator('source_product_id', 'matched_product_id')
    def validate_different_products(cls, v, values):
        """Ensure source and matched products are different"""
        if 'source_product_id' in values and v == values['source_product_id']:
            raise ValueError('Source and matched products must be different')
        return v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            UUID: lambda uuid: str(uuid)
        }


class MatchResultCreate(BaseModel):
    """Model for creating new match results"""
    source_product_id: UUID
    matched_product_id: UUID
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    matching_method: MatchingMethod
    status: MatchStatus = MatchStatus.PENDING
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        return round(v, 2)


class MatchResultUpdate(BaseModel):
    """Model for updating match results"""
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    matching_method: Optional[MatchingMethod] = None
    status: Optional[MatchStatus] = None
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        if v is not None:
            return round(v, 2)
        return v


class MatchResultResponse(BaseModel):
    """Response model for match results with related product info"""
    id: UUID
    source_product_id: UUID
    matched_product_id: UUID
    confidence_score: float
    matching_method: MatchingMethod
    status: MatchStatus
    created_at: datetime
    updated_at: datetime
    
    # Optional product details
    source_product: Optional[Dict[str, Any]] = None
    matched_product: Optional[Dict[str, Any]] = None
    metadata: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            UUID: lambda uuid: str(uuid)
        }


class MatchStatsResponse(BaseModel):
    """Statistics about matching results"""
    total_matches: int
    pending_matches: int
    confirmed_matches: int
    rejected_matches: int
    average_confidence: float
    methods_breakdown: Dict[str, int]
    top_confidence_matches: List[MatchResultResponse]
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            UUID: lambda uuid: str(uuid)
        }