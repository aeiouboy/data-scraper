"""
Matching models package
"""
from .match_result import (
    MatchResult,
    MatchResultCreate,
    MatchResultUpdate,
    MatchResultResponse,
    MatchStatsResponse,
    MatchingMethod,
    MatchStatus
)
from .match_metadata import (
    MatchMetadata,
    MatchMetadataCreate,
    MatchMetadataResponse,
    AlgorithmMetadata,
    NameMatchingMetadata,
    SKUMatchingMetadata,
    BrandMatchingMetadata,
    SpecificationMatchingMetadata,
    ConfidenceScoreMetadata,
    ValidationMetadata,
    PerformanceMetadata,
    MetadataKeys
)

__all__ = [
    # Match Result Models
    'MatchResult',
    'MatchResultCreate', 
    'MatchResultUpdate',
    'MatchResultResponse',
    'MatchStatsResponse',
    'MatchingMethod',
    'MatchStatus',
    
    # Match Metadata Models
    'MatchMetadata',
    'MatchMetadataCreate',
    'MatchMetadataResponse',
    'AlgorithmMetadata',
    'NameMatchingMetadata',
    'SKUMatchingMetadata',
    'BrandMatchingMetadata',
    'SpecificationMatchingMetadata',
    'ConfidenceScoreMetadata',
    'ValidationMetadata',
    'PerformanceMetadata',
    'MetadataKeys'
]