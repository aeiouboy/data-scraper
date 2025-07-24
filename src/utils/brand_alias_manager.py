"""
Brand Alias Management System
Handles brand name normalization and alias mapping for product matching
"""

import re
import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path

from src.config.text_normalization_config import BRAND_MAPPINGS, BRAND_EXCLUSIONS

logger = logging.getLogger(__name__)


@dataclass
class BrandAlias:
    """Brand alias data structure"""
    canonical_name: str
    aliases: List[str]
    language: str
    confidence: float
    category: Optional[str] = None
    source: Optional[str] = None


class BrandAliasManager:
    """Manages brand aliases and normalization"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize brand alias manager"""
        self.config_file = config_file
        self.brand_mappings = dict(BRAND_MAPPINGS)
        self.brand_exclusions = set(BRAND_EXCLUSIONS)
        
        # Brand aliases structure
        self.aliases = {}  # canonical_name -> BrandAlias
        self.reverse_mapping = {}  # alias -> canonical_name
        
        # Load additional aliases if config file provided
        if config_file and Path(config_file).exists():
            self._load_from_file(config_file)
        
        # Build internal mappings
        self._build_mappings()
        
        # Compile regex patterns
        self._compile_patterns()
    
    def _build_mappings(self):
        """Build internal brand mappings from configuration"""
        # Group brands by canonical name
        brand_groups = {}
        
        for alias, canonical in self.brand_mappings.items():
            if canonical not in brand_groups:
                brand_groups[canonical] = []
            brand_groups[canonical].append(alias)
        
        # Create BrandAlias objects
        for canonical, aliases in brand_groups.items():
            self.aliases[canonical] = BrandAlias(
                canonical_name=canonical,
                aliases=aliases,
                language='mixed',
                confidence=1.0
            )
            
            # Build reverse mapping
            for alias in aliases:
                self.reverse_mapping[alias.lower()] = canonical
            
            # Add canonical name to reverse mapping
            self.reverse_mapping[canonical.lower()] = canonical
    
    def _compile_patterns(self):
        """Compile regex patterns for brand matching"""
        # Create pattern for each brand
        self.brand_patterns = {}
        
        for canonical, brand_alias in self.aliases.items():
            patterns = []
            
            # Create patterns for each alias
            for alias in brand_alias.aliases + [canonical]:
                # Exact match pattern
                exact_pattern = r'\b' + re.escape(alias) + r'\b'
                patterns.append(exact_pattern)
                
                # Fuzzy pattern for common variations
                fuzzy_pattern = self._create_fuzzy_pattern(alias)
                if fuzzy_pattern:
                    patterns.append(fuzzy_pattern)
            
            # Combine all patterns for this brand
            combined_pattern = '|'.join(patterns)
            self.brand_patterns[canonical] = re.compile(combined_pattern, re.IGNORECASE)
    
    def _create_fuzzy_pattern(self, brand: str) -> Optional[str]:
        """Create fuzzy pattern for brand variations"""
        # Handle common variations
        variations = []
        
        # Handle spaces and hyphens
        spaced = brand.replace(' ', r'[\s\-]?')
        if spaced != brand:
            variations.append(spaced)
        
        # Handle optional suffixes
        if brand.endswith('professional'):
            base = brand.replace('professional', '')
            variations.append(base.rstrip() + r'(?:\s+professional)?')
        
        # Handle abbreviations
        if len(brand) > 5:
            # Create pattern for first letters
            first_letters = ''.join(word[0] for word in brand.split() if word)
            if len(first_letters) > 1:
                variations.append(first_letters.upper())
        
        if variations:
            return '|'.join(variations)
        return None
    
    def normalize_brand(self, brand: str) -> str:
        """Normalize brand name to canonical form"""
        if not brand:
            return ""
        
        # Clean input
        cleaned = brand.strip().lower()
        
        # Direct lookup
        if cleaned in self.reverse_mapping:
            return self.reverse_mapping[cleaned]
        
        # Pattern matching
        canonical = self._find_brand_by_pattern(brand)
        if canonical:
            return canonical
        
        # Fuzzy matching
        canonical = self._fuzzy_brand_match(brand)
        if canonical:
            return canonical
        
        # Return original if no match found
        return brand.strip()
    
    def _find_brand_by_pattern(self, brand: str) -> Optional[str]:
        """Find brand using compiled patterns"""
        for canonical, pattern in self.brand_patterns.items():
            if pattern.search(brand):
                return canonical
        return None
    
    def _fuzzy_brand_match(self, brand: str, threshold: float = 0.8) -> Optional[str]:
        """Fuzzy match brand name"""
        brand_lower = brand.lower()
        best_match = None
        best_score = 0
        
        for canonical, brand_alias in self.aliases.items():
            for alias in brand_alias.aliases + [canonical]:
                # Calculate similarity
                similarity = self._calculate_similarity(brand_lower, alias.lower())
                
                if similarity > threshold and similarity > best_score:
                    best_score = similarity
                    best_match = canonical
        
        return best_match
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity using various metrics"""
        # Jaccard similarity
        set1 = set(s1)
        set2 = set(s2)
        intersection = set1 & set2
        union = set1 | set2
        jaccard = len(intersection) / len(union) if union else 0
        
        # Length similarity
        len_sim = 1 - abs(len(s1) - len(s2)) / max(len(s1), len(s2))
        
        # Substring similarity
        substr_sim = 0
        if s1 in s2 or s2 in s1:
            substr_sim = 0.5
        
        # Combine metrics
        return (jaccard * 0.5 + len_sim * 0.3 + substr_sim * 0.2)
    
    def are_aliases(self, brand1: str, brand2: str) -> bool:
        """Check if two brands are aliases of each other"""
        norm1 = self.normalize_brand(brand1)
        norm2 = self.normalize_brand(brand2)
        
        return norm1 == norm2 and norm1 != "" and norm2 != ""
    
    def get_brand_aliases(self, brand: str) -> List[str]:
        """Get all aliases for a brand"""
        canonical = self.normalize_brand(brand)
        
        if canonical in self.aliases:
            return self.aliases[canonical].aliases + [canonical]
        
        return [brand]
    
    def add_brand_alias(self, canonical: str, alias: str, language: str = 'mixed', 
                       confidence: float = 1.0, category: Optional[str] = None):
        """Add a new brand alias"""
        canonical = canonical.lower()
        alias = alias.lower()
        
        # Update existing or create new
        if canonical in self.aliases:
            if alias not in self.aliases[canonical].aliases:
                self.aliases[canonical].aliases.append(alias)
        else:
            self.aliases[canonical] = BrandAlias(
                canonical_name=canonical,
                aliases=[alias],
                language=language,
                confidence=confidence,
                category=category
            )
        
        # Update reverse mapping
        self.reverse_mapping[alias] = canonical
        self.reverse_mapping[canonical] = canonical
        
        # Update brand mappings
        self.brand_mappings[alias] = canonical
        
        # Recompile patterns
        self._compile_patterns()
    
    def remove_brand_alias(self, alias: str):
        """Remove a brand alias"""
        alias = alias.lower()
        
        if alias in self.reverse_mapping:
            canonical = self.reverse_mapping[alias]
            
            # Remove from aliases
            if canonical in self.aliases:
                if alias in self.aliases[canonical].aliases:
                    self.aliases[canonical].aliases.remove(alias)
                
                # Remove entire brand if no aliases left
                if not self.aliases[canonical].aliases and alias == canonical:
                    del self.aliases[canonical]
            
            # Remove from reverse mapping
            del self.reverse_mapping[alias]
            
            # Remove from brand mappings
            if alias in self.brand_mappings:
                del self.brand_mappings[alias]
            
            # Recompile patterns
            self._compile_patterns()
    
    def get_brand_statistics(self) -> Dict[str, int]:
        """Get brand alias statistics"""
        total_brands = len(self.aliases)
        total_aliases = sum(len(brand.aliases) for brand in self.aliases.values())
        
        # Language breakdown
        language_counts = {}
        for brand in self.aliases.values():
            lang = brand.language
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        return {
            'total_brands': total_brands,
            'total_aliases': total_aliases,
            'average_aliases_per_brand': total_aliases / total_brands if total_brands > 0 else 0,
            'language_breakdown': language_counts
        }
    
    def validate_brand_mappings(self) -> List[str]:
        """Validate brand mappings and return issues"""
        issues = []
        
        # Check for duplicate mappings
        canonical_counts = {}
        for alias, canonical in self.brand_mappings.items():
            if canonical in canonical_counts:
                canonical_counts[canonical] += 1
            else:
                canonical_counts[canonical] = 1
        
        # Check for conflicting mappings
        for canonical, count in canonical_counts.items():
            if count > 10:  # Arbitrary threshold
                issues.append(f"Brand '{canonical}' has {count} aliases (possibly too many)")
        
        # Check for circular mappings
        for alias, canonical in self.brand_mappings.items():
            if canonical in self.brand_mappings and self.brand_mappings[canonical] != canonical:
                issues.append(f"Circular mapping detected: {alias} -> {canonical} -> {self.brand_mappings[canonical]}")
        
        return issues
    
    def export_to_file(self, file_path: str):
        """Export brand aliases to JSON file"""
        export_data = {
            'aliases': {},
            'metadata': {
                'version': '1.0',
                'total_brands': len(self.aliases),
                'export_date': str(Path().resolve())
            }
        }
        
        # Convert BrandAlias objects to dict
        for canonical, brand_alias in self.aliases.items():
            export_data['aliases'][canonical] = {
                'canonical_name': brand_alias.canonical_name,
                'aliases': brand_alias.aliases,
                'language': brand_alias.language,
                'confidence': brand_alias.confidence,
                'category': brand_alias.category,
                'source': brand_alias.source
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Brand aliases exported to {file_path}")
    
    def _load_from_file(self, file_path: str):
        """Load brand aliases from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'aliases' in data:
                for canonical, alias_data in data['aliases'].items():
                    brand_alias = BrandAlias(
                        canonical_name=alias_data['canonical_name'],
                        aliases=alias_data['aliases'],
                        language=alias_data.get('language', 'mixed'),
                        confidence=alias_data.get('confidence', 1.0),
                        category=alias_data.get('category'),
                        source=alias_data.get('source')
                    )
                    self.aliases[canonical] = brand_alias
            
            logger.info(f"Brand aliases loaded from {file_path}")
        
        except Exception as e:
            logger.error(f"Error loading brand aliases from {file_path}: {e}")
    
    def find_brand_in_text(self, text: str) -> List[Tuple[str, float]]:
        """Find all brands mentioned in text with confidence scores"""
        found_brands = []
        
        for canonical, pattern in self.brand_patterns.items():
            matches = pattern.findall(text)
            if matches:
                # Calculate confidence based on match quality
                confidence = self._calculate_match_confidence(matches[0], canonical)
                found_brands.append((canonical, confidence))
        
        # Sort by confidence
        found_brands.sort(key=lambda x: x[1], reverse=True)
        
        return found_brands
    
    def _calculate_match_confidence(self, match: str, canonical: str) -> float:
        """Calculate confidence score for a brand match"""
        # Base confidence
        confidence = 0.8
        
        # Boost for exact canonical match
        if match.lower() == canonical.lower():
            confidence = 1.0
        
        # Boost for longer matches
        if len(match) > 5:
            confidence += 0.1
        
        # Boost for matches with brand-specific patterns
        if any(c.isupper() for c in match):
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def get_brand_suggestions(self, partial_brand: str, limit: int = 5) -> List[str]:
        """Get brand suggestions for partial input"""
        suggestions = []
        partial_lower = partial_brand.lower()
        
        for canonical, brand_alias in self.aliases.items():
            # Check canonical name
            if canonical.lower().startswith(partial_lower):
                suggestions.append(canonical)
            
            # Check aliases
            for alias in brand_alias.aliases:
                if alias.lower().startswith(partial_lower) and alias not in suggestions:
                    suggestions.append(alias)
        
        return suggestions[:limit]


# Example usage and testing
if __name__ == "__main__":
    # Initialize brand alias manager
    manager = BrandAliasManager()
    
    # Test brand normalization
    test_brands = [
        "มิตซูบิชิ",
        "MITSUBISHI",
        "Mitsubishi Electric",
        "ซัมซุง",
        "Samsung",
        "แอลจี",
        "LG Electronics",
        "บอช",
        "Bosch Professional",
        "Unknown Brand"
    ]
    
    print("Brand Normalization Test:")
    print("=" * 50)
    
    for brand in test_brands:
        normalized = manager.normalize_brand(brand)
        aliases = manager.get_brand_aliases(brand)
        
        print(f"Original: {brand}")
        print(f"Normalized: {normalized}")
        print(f"Aliases: {aliases}")
        print()
    
    # Test brand finding in text
    test_texts = [
        "MITSUBISHI แอร์ รุ่น MSY-KP13VF",
        "ซัมซุง ตู้เย็น 300 ลิตร",
        "LG Smart TV 55 นิ้ว",
        "Bosch Professional Drill 18V"
    ]
    
    print("Brand Finding Test:")
    print("=" * 50)
    
    for text in test_texts:
        found = manager.find_brand_in_text(text)
        print(f"Text: {text}")
        print(f"Found brands: {found}")
        print()
    
    # Test alias checking
    print("Alias Checking Test:")
    print("=" * 50)
    
    alias_pairs = [
        ("มิตซูบิชิ", "MITSUBISHI"),
        ("ซัมซุง", "Samsung"),
        ("LG", "แอลจี"),
        ("Bosch", "Bosch Professional"),
        ("Unknown1", "Unknown2")
    ]
    
    for brand1, brand2 in alias_pairs:
        are_aliases = manager.are_aliases(brand1, brand2)
        print(f"'{brand1}' and '{brand2}' are aliases: {are_aliases}")
    
    # Statistics
    print("\nBrand Statistics:")
    print("=" * 50)
    stats = manager.get_brand_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Validation
    print("\nValidation Issues:")
    print("=" * 50)
    issues = manager.validate_brand_mappings()
    if issues:
        for issue in issues:
            print(f"- {issue}")
    else:
        print("No validation issues found.")