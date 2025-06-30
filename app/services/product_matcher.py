"""
Cross-retailer product matching system for price comparison
Uses multiple algorithms to identify the same products across different retailers
"""

import re
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
from decimal import Decimal

from app.models.product import Product, ProductMatch
from app.utils.database import SupabaseClient
from app.config.retailers import retailer_manager, get_unified_category_mapping

logger = logging.getLogger(__name__)


@dataclass
class MatchCriteria:
    """Criteria used for product matching"""
    name_similarity: float = 0.0
    brand_match: bool = False
    category_match: bool = False
    specification_match: float = 0.0
    price_similarity: float = 0.0
    overall_confidence: float = 0.0


class ProductMatcher:
    """Advanced product matching system for cross-retailer comparison"""
    
    def __init__(self):
        self.db = SupabaseClient()
        self.unified_categories = get_unified_category_mapping()
        
        # Matching thresholds
        self.thresholds = {
            "name_similarity_min": 0.75,
            "brand_exact_match_bonus": 0.15,
            "category_match_bonus": 0.10,
            "specification_match_bonus": 0.05,
            "price_variance_max": 0.50,  # 50% price variance allowed
            "minimum_confidence": 0.70
        }
    
    async def find_product_matches(self, target_product: Product) -> List[Tuple[Product, MatchCriteria]]:
        """Find matching products across all retailers"""
        
        logger.info(f"Finding matches for: {target_product.name} ({target_product.retailer_code})")
        
        # Get potential matches from database
        potential_matches = await self._get_potential_matches(target_product)
        
        if not potential_matches:
            logger.info("No potential matches found")
            return []
        
        # Score each potential match
        scored_matches = []
        for candidate in potential_matches:
            criteria = await self._calculate_match_criteria(target_product, candidate)
            
            if criteria.overall_confidence >= self.thresholds["minimum_confidence"]:
                scored_matches.append((candidate, criteria))
        
        # Sort by confidence score
        scored_matches.sort(key=lambda x: x[1].overall_confidence, reverse=True)
        
        logger.info(f"Found {len(scored_matches)} high-confidence matches")
        return scored_matches
    
    async def create_product_match(self, master_product: Product, matched_products: List[Product]) -> ProductMatch:
        """Create a ProductMatch record for cross-retailer comparison"""
        
        # Calculate price statistics
        all_products = [master_product] + matched_products
        prices = [float(p.current_price) for p in all_products if p.current_price]
        
        price_min = min(prices) if prices else None
        price_max = max(prices) if prices else None
        
        # Find best price retailer
        best_price_retailer = None
        if prices:
            min_price = min(prices)
            for product in all_products:
                if product.current_price and float(product.current_price) == min_price:
                    best_price_retailer = product.retailer_code
                    break
        
        # Calculate price variance
        price_variance = None
        if price_min and price_max and price_min > 0:
            price_variance = ((price_max - price_min) / price_min) * 100
        
        # Generate normalized attributes
        normalized_name = self._normalize_text(master_product.name)
        normalized_brand = self._normalize_text(master_product.brand or "")
        
        # Extract key specifications
        key_specs = await self._extract_key_specifications(all_products)
        
        # Create match criteria summary
        match_criteria = {
            "algorithm_version": "1.0",
            "matched_retailers": [p.retailer_code for p in matched_products],
            "confidence_scores": [0.85] * len(matched_products),  # Simplified for now
            "matching_features": ["name", "brand", "category", "specifications"]
        }
        
        # Create ProductMatch object
        product_match = ProductMatch(
            master_product_id=master_product.id,
            matched_product_ids=[p.id for p in matched_products],
            match_confidence=0.85,  # Average confidence
            match_criteria=match_criteria,
            normalized_name=normalized_name,
            normalized_brand=normalized_brand,
            unified_category=master_product.unified_category or "unknown",
            key_specifications=key_specs,
            price_range_min=Decimal(str(price_min)) if price_min else None,
            price_range_max=Decimal(str(price_max)) if price_max else None,
            best_price_retailer=best_price_retailer,
            price_variance_percentage=price_variance
        )
        
        # Save to database
        await self.db.insert_product_match(product_match)
        
        logger.info(f"Created product match with {len(matched_products)} retailers")
        logger.info(f"Price range: ฿{price_min:.2f} - ฿{price_max:.2f} ({price_variance:.1f}% variance)")
        
        return product_match
    
    async def process_all_products(self, retailer_codes: Optional[List[str]] = None) -> Dict[str, Any]:
        """Process all products to find cross-retailer matches"""
        
        logger.info("Starting comprehensive product matching across all retailers")
        
        # Get all products
        filters = {}
        if retailer_codes:
            filters["retailer_code"] = retailer_codes
        
        all_products = await self.db.get_products(filters=filters)
        
        results = {
            "total_products": len(all_products),
            "matches_created": 0,
            "retailers_processed": set(),
            "categories_matched": set(),
            "price_savings_identified": 0.0
        }
        
        # Group products by hash for efficient matching
        product_groups = {}
        for product in all_products:
            if product.product_hash:
                if product.product_hash not in product_groups:
                    product_groups[product.product_hash] = []
                product_groups[product.product_hash].append(product)
        
        logger.info(f"Grouped {len(all_products)} products into {len(product_groups)} hash groups")
        
        # Process each group for matches
        for hash_key, products in product_groups.items():
            if len(products) > 1:  # Only process groups with multiple products
                # Choose master product (prefer HomePro as market leader)
                master_product = None
                for product in products:
                    if product.retailer_code == "HP":
                        master_product = product
                        break
                
                if not master_product:
                    master_product = products[0]
                
                # Get other products as matches
                matched_products = [p for p in products if p.id != master_product.id]
                
                if matched_products:
                    try:
                        product_match = await self.create_product_match(master_product, matched_products)
                        results["matches_created"] += 1
                        results["retailers_processed"].update([p.retailer_code for p in products])
                        results["categories_matched"].add(master_product.unified_category or "unknown")
                        
                        # Calculate potential savings
                        if product_match.price_range_min and product_match.price_range_max:
                            savings = float(product_match.price_range_max - product_match.price_range_min)
                            results["price_savings_identified"] += savings
                        
                    except Exception as e:
                        logger.error(f"Failed to create match for group {hash_key}: {str(e)}")
        
        results["retailers_processed"] = list(results["retailers_processed"])
        results["categories_matched"] = list(results["categories_matched"])
        
        logger.info(f"Product matching completed:")
        logger.info(f"  Matches created: {results['matches_created']:,}")
        logger.info(f"  Retailers involved: {len(results['retailers_processed'])}")
        logger.info(f"  Categories matched: {len(results['categories_matched'])}")
        logger.info(f"  Total savings identified: ฿{results['price_savings_identified']:,.2f}")
        
        return results
    
    async def _get_potential_matches(self, target_product: Product) -> List[Product]:
        """Get potential product matches from database"""
        
        # Search criteria
        filters = {
            "unified_category": target_product.unified_category,
            "exclude_retailer": target_product.retailer_code
        }
        
        # Add brand filter if available
        if target_product.brand:
            filters["brand"] = target_product.brand
        
        # Get products from database
        candidates = await self.db.get_products(filters=filters, limit=100)
        
        # Additional filtering based on name similarity
        filtered_candidates = []
        target_name_normalized = self._normalize_text(target_product.name)
        
        for candidate in candidates:
            candidate_name_normalized = self._normalize_text(candidate.name)
            similarity = self._calculate_text_similarity(target_name_normalized, candidate_name_normalized)
            
            if similarity >= 0.5:  # Minimum similarity threshold
                filtered_candidates.append(candidate)
        
        return filtered_candidates
    
    async def _calculate_match_criteria(self, product1: Product, product2: Product) -> MatchCriteria:
        """Calculate detailed matching criteria between two products"""
        
        criteria = MatchCriteria()
        
        # Name similarity
        name1_norm = self._normalize_text(product1.name)
        name2_norm = self._normalize_text(product2.name)
        criteria.name_similarity = self._calculate_text_similarity(name1_norm, name2_norm)
        
        # Brand match
        brand1_norm = self._normalize_text(product1.brand or "")
        brand2_norm = self._normalize_text(product2.brand or "")
        criteria.brand_match = brand1_norm == brand2_norm and brand1_norm != ""
        
        # Category match
        criteria.category_match = (
            product1.unified_category == product2.unified_category and
            product1.unified_category is not None
        )
        
        # Specification match (simplified)
        criteria.specification_match = self._calculate_specification_similarity(
            product1.specifications or {}, 
            product2.specifications or {}
        )
        
        # Price similarity
        if product1.current_price and product2.current_price:
            price1 = float(product1.current_price)
            price2 = float(product2.current_price)
            price_diff = abs(price1 - price2) / max(price1, price2)
            criteria.price_similarity = max(0, 1 - price_diff)
        
        # Calculate overall confidence
        confidence_score = 0
        confidence_score += criteria.name_similarity * 0.40  # 40% weight
        confidence_score += (0.15 if criteria.brand_match else 0)  # 15% weight
        confidence_score += (0.10 if criteria.category_match else 0)  # 10% weight
        confidence_score += criteria.specification_match * 0.15  # 15% weight
        confidence_score += criteria.price_similarity * 0.20  # 20% weight
        
        criteria.overall_confidence = min(1.0, confidence_score)
        
        return criteria
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase and remove special characters
        normalized = re.sub(r'[^\w\s]', '', text.lower())
        
        # Remove common words that don't help with matching
        stop_words = {'และ', 'หรือ', 'กับ', 'for', 'with', 'and', 'or', 'the', 'a', 'an'}
        words = normalized.split()
        filtered_words = [word for word in words if word not in stop_words]
        
        return ' '.join(filtered_words).strip()
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        if not text1 or not text2:
            return 0.0
        
        # Use difflib for sequence matching
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def _calculate_specification_similarity(self, specs1: Dict[str, Any], specs2: Dict[str, Any]) -> float:
        """Calculate similarity between specification dictionaries"""
        if not specs1 or not specs2:
            return 0.0
        
        # Find common keys
        common_keys = set(specs1.keys()) & set(specs2.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            val1 = str(specs1[key]).lower()
            val2 = str(specs2[key]).lower()
            if val1 == val2:
                matches += 1
        
        return matches / len(common_keys)
    
    async def _extract_key_specifications(self, products: List[Product]) -> Dict[str, Any]:
        """Extract key specifications common across products"""
        
        key_specs = {}
        
        # Collect all specification keys
        all_keys = set()
        for product in products:
            if product.specifications:
                all_keys.update(product.specifications.keys())
        
        # Find specifications present in most products
        for key in all_keys:
            values = []
            for product in products:
                if product.specifications and key in product.specifications:
                    values.append(product.specifications[key])
            
            # If specification is present in >50% of products, include it
            if len(values) > len(products) / 2:
                # Use most common value
                if values:
                    key_specs[key] = max(set(values), key=values.count)
        
        return key_specs


class ProductMatchAnalyzer:
    """Analyze and report on product matches"""
    
    def __init__(self):
        self.db = SupabaseClient()
    
    async def generate_price_comparison_report(self) -> Dict[str, Any]:
        """Generate comprehensive price comparison report"""
        
        # Get all product matches
        matches = await self.db.get_product_matches()
        
        report = {
            "total_matches": len(matches),
            "retailer_coverage": {},
            "category_analysis": {},
            "savings_opportunities": [],
            "price_variance_stats": {
                "average_variance": 0.0,
                "max_variance": 0.0,
                "min_variance": 100.0
            }
        }
        
        # Analyze retailer coverage
        for match in matches:
            for retailer_code in match.match_criteria.get("matched_retailers", []):
                if retailer_code not in report["retailer_coverage"]:
                    report["retailer_coverage"][retailer_code] = 0
                report["retailer_coverage"][retailer_code] += 1
        
        # Analyze by category
        for match in matches:
            category = match.unified_category
            if category not in report["category_analysis"]:
                report["category_analysis"][category] = {
                    "match_count": 0,
                    "avg_variance": 0.0,
                    "best_savings": 0.0
                }
            
            report["category_analysis"][category]["match_count"] += 1
            
            if match.price_variance_percentage:
                report["category_analysis"][category]["avg_variance"] += match.price_variance_percentage
            
            if match.price_range_min and match.price_range_max:
                savings = float(match.price_range_max - match.price_range_min)
                report["category_analysis"][category]["best_savings"] = max(
                    report["category_analysis"][category]["best_savings"], savings
                )
        
        # Calculate averages for categories
        for category_data in report["category_analysis"].values():
            if category_data["match_count"] > 0:
                category_data["avg_variance"] /= category_data["match_count"]
        
        # Find top savings opportunities
        savings_opportunities = []
        for match in matches:
            if match.price_range_min and match.price_range_max:
                savings = float(match.price_range_max - match.price_range_min)
                if savings > 100:  # Only show significant savings
                    savings_opportunities.append({
                        "product_name": match.normalized_name,
                        "category": match.unified_category,
                        "savings_amount": savings,
                        "price_range": f"฿{float(match.price_range_min):,.2f} - ฿{float(match.price_range_max):,.2f}",
                        "best_retailer": match.best_price_retailer,
                        "variance_percentage": match.price_variance_percentage
                    })
        
        # Sort by savings amount
        savings_opportunities.sort(key=lambda x: x["savings_amount"], reverse=True)
        report["savings_opportunities"] = savings_opportunities[:50]  # Top 50
        
        # Calculate price variance statistics
        variances = [m.price_variance_percentage for m in matches if m.price_variance_percentage]
        if variances:
            report["price_variance_stats"]["average_variance"] = sum(variances) / len(variances)
            report["price_variance_stats"]["max_variance"] = max(variances)
            report["price_variance_stats"]["min_variance"] = min(variances)
        
        return report
    
    async def get_retailer_competitiveness_analysis(self) -> Dict[str, Any]:
        """Analyze which retailers offer the best prices by category"""
        
        matches = await self.db.get_product_matches()
        
        analysis = {}
        
        for match in matches:
            category = match.unified_category
            best_retailer = match.best_price_retailer
            
            if not best_retailer:
                continue
            
            if category not in analysis:
                analysis[category] = {}
            
            if best_retailer not in analysis[category]:
                analysis[category][best_retailer] = {
                    "best_price_count": 0,
                    "total_products": 0,
                    "competitiveness_score": 0.0
                }
            
            analysis[category][best_retailer]["best_price_count"] += 1
            analysis[category][best_retailer]["total_products"] += 1
        
        # Calculate competitiveness scores
        for category_data in analysis.values():
            total_products = sum(retailer["total_products"] for retailer in category_data.values())
            for retailer_data in category_data.values():
                if total_products > 0:
                    retailer_data["competitiveness_score"] = (
                        retailer_data["best_price_count"] / total_products
                    ) * 100
        
        return analysis


# Convenience functions for common operations
async def match_new_product(product: Product) -> List[ProductMatch]:
    """Find matches for a newly scraped product"""
    matcher = ProductMatcher()
    matches = await matcher.find_product_matches(product)
    
    if matches:
        matched_products = [match[0] for match in matches]
        product_match = await matcher.create_product_match(product, matched_products)
        return [product_match]
    
    return []


async def refresh_all_matches() -> Dict[str, Any]:
    """Refresh all product matches across retailers"""
    matcher = ProductMatcher()
    return await matcher.process_all_products()


async def analyze_price_competition() -> Dict[str, Any]:
    """Generate comprehensive price competition analysis"""
    analyzer = ProductMatchAnalyzer()
    
    comparison_report = await analyzer.generate_price_comparison_report()
    competitiveness_analysis = await analyzer.get_retailer_competitiveness_analysis()
    
    return {
        "price_comparison": comparison_report,
        "retailer_competitiveness": competitiveness_analysis,
        "generated_at": "2025-06-28"
    }