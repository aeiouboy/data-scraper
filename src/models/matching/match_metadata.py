"""
Database models for matching metadata
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class MatchMetadata(BaseModel):
    """Model for matching metadata"""
    id: Optional[UUID] = None
    matching_result_id: UUID = Field(..., description="ID of the matching result")
    metadata_key: str = Field(..., max_length=100, description="Metadata key identifier")
    metadata_value: Dict[str, Any] = Field(..., description="JSON metadata value")
    created_at: Optional[datetime] = None
    
    @validator('metadata_key')
    def validate_metadata_key(cls, v):
        """Validate metadata key format"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Metadata key cannot be empty')
        return v.strip().lower()
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            UUID: lambda uuid: str(uuid)
        }


class MatchMetadataCreate(BaseModel):
    """Model for creating new match metadata"""
    matching_result_id: UUID
    metadata_key: str = Field(..., max_length=100)
    metadata_value: Dict[str, Any]
    
    @validator('metadata_key')
    def validate_metadata_key(cls, v):
        return v.strip().lower() if v else v


class AlgorithmMetadata(BaseModel):
    """Structured metadata for algorithm information"""
    algorithm_name: str
    algorithm_version: str
    parameters: Dict[str, Any]
    execution_time_ms: Optional[float] = None
    debug_info: Optional[Dict[str, Any]] = None


class NameMatchingMetadata(BaseModel):
    """Metadata specific to name matching algorithms"""
    original_name_1: str
    original_name_2: str
    normalized_name_1: str
    normalized_name_2: str
    similarity_score: float
    method: str  # exact, fuzzy, token_sort, etc.
    threshold_used: float
    tokens_1: List[str]
    tokens_2: List[str]
    common_tokens: List[str]


class SKUMatchingMetadata(BaseModel):
    """Metadata specific to SKU matching algorithms"""
    sku_1: Optional[str]
    sku_2: Optional[str]
    extracted_patterns_1: List[str]
    extracted_patterns_2: List[str]
    pattern_similarity: float
    exact_match: bool


class BrandMatchingMetadata(BaseModel):
    """Metadata specific to brand matching algorithms"""
    brand_1: Optional[str]
    brand_2: Optional[str]
    normalized_brand_1: str
    normalized_brand_2: str
    brand_aliases_1: List[str]
    brand_aliases_2: List[str]
    exact_match: bool
    alias_match: bool


class SpecificationMatchingMetadata(BaseModel):
    """Metadata specific to specification matching algorithms"""
    specs_1: Dict[str, Any]
    specs_2: Dict[str, Any]
    common_specs: Dict[str, Any]
    spec_similarity_scores: Dict[str, float]
    overall_spec_score: float
    critical_specs_match: bool


class ConfidenceScoreMetadata(BaseModel):
    """Metadata for confidence score calculation"""
    base_scores: Dict[str, float]  # Scores from each matching method
    weights: Dict[str, float]      # Weights applied to each method
    adjustments: Dict[str, float]  # Any adjustments applied
    final_score: float
    calculation_method: str


class ValidationMetadata(BaseModel):
    """Metadata for match validation"""
    validation_rules_applied: List[str]
    validation_results: Dict[str, bool]
    validation_scores: Dict[str, float]
    overall_validation_result: bool
    validation_notes: Optional[str] = None


class PerformanceMetadata(BaseModel):
    """Metadata for performance tracking"""
    total_execution_time_ms: float
    algorithm_times: Dict[str, float]
    database_query_time_ms: Optional[float] = None
    api_call_time_ms: Optional[float] = None
    cache_hit: bool = False
    

# Predefined metadata keys for consistent usage
class MetadataKeys:
    """Standard metadata keys"""
    ALGORITHM_INFO = "algorithm_info"
    NAME_MATCHING = "name_matching"
    SKU_MATCHING = "sku_matching"
    BRAND_MATCHING = "brand_matching"
    SPEC_MATCHING = "specification_matching"
    CONFIDENCE_CALCULATION = "confidence_calculation"
    VALIDATION_RESULTS = "validation_results"
    PERFORMANCE_METRICS = "performance_metrics"
    BRAVE_API_RESPONSE = "brave_api_response"
    MIGRATION_INFO = "migration_info"
    USER_FEEDBACK = "user_feedback"


class MatchMetadataResponse(BaseModel):
    """Response model for match metadata"""
    id: UUID
    matching_result_id: UUID
    metadata_key: str
    metadata_value: Dict[str, Any]
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            UUID: lambda uuid: str(uuid)
        }