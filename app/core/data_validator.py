"""
Data quality validation system for scraped products
"""
import re
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlparse

from app.models.product import Product

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue found in product data"""
    field: str
    severity: str  # 'error', 'warning', 'info'
    issue_type: str
    message: str
    value: Any = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of product validation"""
    product_id: Optional[str]
    product_sku: str
    retailer_code: str
    is_valid: bool
    quality_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_issues_by_severity(self, severity: str) -> List[ValidationIssue]:
        """Get issues filtered by severity"""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_error_count(self) -> int:
        """Get count of error-level issues"""
        return len(self.get_issues_by_severity('error'))
    
    def get_warning_count(self) -> int:
        """Get count of warning-level issues"""
        return len(self.get_issues_by_severity('warning'))


class ProductValidator:
    """
    Comprehensive product data validation system
    Checks for data quality, completeness, and consistency
    """
    
    def __init__(self):
        # Thai regex patterns
        self.thai_pattern = re.compile(r'[\u0E00-\u0E7F]+')
        self.url_pattern = re.compile(r'^https?://[\w\-\.]+(\.[\w\-]+)+[^\s]*$')
        self.sku_pattern = re.compile(r'^[A-Z0-9\-_]{3,50}$')
        
        # Valid categories
        self.valid_categories = {
            'electronics', 'appliances', 'kitchen', 'bathroom', 'bedroom',
            'living', 'furniture', 'lighting', 'tools', 'electrical',
            'plumbing', 'paint', 'construction', 'garden', 'automotive',
            'safety', 'storage', 'decor', 'flooring', 'outdoor',
            'office', 'cooling', 'cleaning', 'doors_windows', 'other'
        }
        
        # Known brand variations (for normalization)
        self.brand_normalizations = {
            'lg': 'LG',
            'samsung': 'Samsung',
            'panasonic': 'Panasonic',
            'sony': 'Sony',
            'sharp': 'Sharp',
            'hitachi': 'Hitachi',
            'mitsubishi': 'Mitsubishi',
            'daikin': 'Daikin',
            'bosch': 'Bosch',
            'makita': 'Makita',
            'stanley': 'Stanley',
            'kohler': 'Kohler',
            'toto': 'TOTO',
            'cotto': 'COTTO',
            'american standard': 'American Standard',
        }
        
        # Price thresholds by category
        self.price_thresholds = {
            'electronics': {'min': 100, 'max': 500000},
            'appliances': {'min': 100, 'max': 300000},
            'furniture': {'min': 50, 'max': 200000},
            'tools': {'min': 20, 'max': 50000},
            'paint': {'min': 50, 'max': 5000},
            'default': {'min': 10, 'max': 1000000}
        }
    
    def validate_product(self, product: Product) -> ValidationResult:
        """
        Validate a single product
        
        Args:
            product: Product to validate
            
        Returns:
            ValidationResult with issues and quality score
        """
        issues = []
        
        # Basic field validation
        issues.extend(self._validate_required_fields(product))
        issues.extend(self._validate_sku(product))
        issues.extend(self._validate_name(product))
        issues.extend(self._validate_prices(product))
        issues.extend(self._validate_brand(product))
        issues.extend(self._validate_category(product))
        issues.extend(self._validate_url(product))
        issues.extend(self._validate_images(product))
        issues.extend(self._validate_availability(product))
        issues.extend(self._validate_specifications(product))
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(product, issues)
        
        # Determine if valid (no errors)
        is_valid = all(issue.severity != 'error' for issue in issues)
        
        return ValidationResult(
            product_id=product.id if hasattr(product, 'id') else None,
            product_sku=product.sku,
            retailer_code=product.retailer_code,
            is_valid=is_valid,
            quality_score=quality_score,
            issues=issues
        )
    
    def _validate_required_fields(self, product: Product) -> List[ValidationIssue]:
        """Validate required fields are present"""
        issues = []
        
        required_fields = ['sku', 'name', 'retailer_code', 'url']
        
        for field in required_fields:
            value = getattr(product, field, None)
            if not value:
                issues.append(ValidationIssue(
                    field=field,
                    severity='error',
                    issue_type='missing_required',
                    message=f"Required field '{field}' is missing",
                    value=value
                ))
        
        return issues
    
    def _validate_sku(self, product: Product) -> List[ValidationIssue]:
        """Validate SKU format and uniqueness"""
        issues = []
        
        if not product.sku:
            return issues  # Already caught by required fields
        
        # Check format
        if not self.sku_pattern.match(product.sku):
            issues.append(ValidationIssue(
                field='sku',
                severity='warning',
                issue_type='invalid_format',
                message=f"SKU format is invalid: {product.sku}",
                value=product.sku,
                suggestion="SKU should be 3-50 characters, uppercase letters, numbers, hyphens, or underscores"
            ))
        
        # Check if it looks generated
        if product.sku.startswith(f"{product.retailer_code}-"):
            issues.append(ValidationIssue(
                field='sku',
                severity='info',
                issue_type='generated_sku',
                message="SKU appears to be auto-generated",
                value=product.sku
            ))
        
        return issues
    
    def _validate_name(self, product: Product) -> List[ValidationIssue]:
        """Validate product name"""
        issues = []
        
        if not product.name:
            return issues  # Already caught by required fields
        
        # Check length
        if len(product.name) < 5:
            issues.append(ValidationIssue(
                field='name',
                severity='error',
                issue_type='too_short',
                message="Product name is too short",
                value=product.name,
                suggestion="Product name should be at least 5 characters"
            ))
        elif len(product.name) > 500:
            issues.append(ValidationIssue(
                field='name',
                severity='warning',
                issue_type='too_long',
                message="Product name is unusually long",
                value=product.name[:100] + "...",
                suggestion="Consider shortening to under 500 characters"
            ))
        
        # Check for suspicious patterns
        if product.name.count('฿') > 0 or re.search(r'\d+\s*บาท', product.name):
            issues.append(ValidationIssue(
                field='name',
                severity='warning',
                issue_type='price_in_name',
                message="Product name contains price information",
                value=product.name,
                suggestion="Price should be in price field, not name"
            ))
        
        # Check for repeated characters
        if re.search(r'(.)\1{4,}', product.name):
            issues.append(ValidationIssue(
                field='name',
                severity='warning',
                issue_type='repeated_chars',
                message="Product name contains repeated characters",
                value=product.name
            ))
        
        return issues
    
    def _validate_prices(self, product: Product) -> List[ValidationIssue]:
        """Validate product prices"""
        issues = []
        
        # Check current price
        if product.current_price is None:
            issues.append(ValidationIssue(
                field='current_price',
                severity='error',
                issue_type='missing_price',
                message="Current price is missing",
                value=None
            ))
        elif product.current_price <= 0:
            issues.append(ValidationIssue(
                field='current_price',
                severity='error',
                issue_type='invalid_price',
                message="Current price must be positive",
                value=float(product.current_price)
            ))
        else:
            # Check price range
            category = product.unified_category or 'default'
            thresholds = self.price_thresholds.get(category, self.price_thresholds['default'])
            
            if float(product.current_price) < thresholds['min']:
                issues.append(ValidationIssue(
                    field='current_price',
                    severity='warning',
                    issue_type='price_too_low',
                    message=f"Price unusually low for category {category}",
                    value=float(product.current_price),
                    suggestion=f"Expected minimum: ฿{thresholds['min']}"
                ))
            elif float(product.current_price) > thresholds['max']:
                issues.append(ValidationIssue(
                    field='current_price',
                    severity='warning',
                    issue_type='price_too_high',
                    message=f"Price unusually high for category {category}",
                    value=float(product.current_price),
                    suggestion=f"Expected maximum: ฿{thresholds['max']}"
                ))
        
        # Check original vs current price
        if product.original_price is not None:
            if product.original_price <= 0:
                issues.append(ValidationIssue(
                    field='original_price',
                    severity='warning',
                    issue_type='invalid_price',
                    message="Original price must be positive",
                    value=float(product.original_price)
                ))
            elif product.current_price and product.original_price < product.current_price:
                issues.append(ValidationIssue(
                    field='original_price',
                    severity='warning',
                    issue_type='price_logic_error',
                    message="Original price is less than current price",
                    value=float(product.original_price),
                    suggestion="Original price should be >= current price"
                ))
            elif product.current_price and product.original_price > product.current_price * 10:
                issues.append(ValidationIssue(
                    field='original_price',
                    severity='warning',
                    issue_type='suspicious_discount',
                    message="Discount appears too high (>90%)",
                    value=float(product.original_price)
                ))
        
        return issues
    
    def _validate_brand(self, product: Product) -> List[ValidationIssue]:
        """Validate brand information"""
        issues = []
        
        if not product.brand:
            # Brand is optional but good to have
            issues.append(ValidationIssue(
                field='brand',
                severity='info',
                issue_type='missing_brand',
                message="Brand information is missing",
                value=None,
                suggestion="Adding brand improves searchability"
            ))
        else:
            # Check brand normalization
            brand_lower = product.brand.lower()
            if brand_lower in self.brand_normalizations:
                normalized = self.brand_normalizations[brand_lower]
                if product.brand != normalized:
                    issues.append(ValidationIssue(
                        field='brand',
                        severity='info',
                        issue_type='brand_normalization',
                        message=f"Brand can be normalized",
                        value=product.brand,
                        suggestion=f"Consider using: {normalized}"
                    ))
            
            # Check for suspicious brand names
            if len(product.brand) < 2:
                issues.append(ValidationIssue(
                    field='brand',
                    severity='warning',
                    issue_type='brand_too_short',
                    message="Brand name is too short",
                    value=product.brand
                ))
        
        return issues
    
    def _validate_category(self, product: Product) -> List[ValidationIssue]:
        """Validate category information"""
        issues = []
        
        # Check unified category
        if not product.unified_category:
            issues.append(ValidationIssue(
                field='unified_category',
                severity='error',
                issue_type='missing_category',
                message="Unified category is missing",
                value=None
            ))
        elif product.unified_category not in self.valid_categories:
            issues.append(ValidationIssue(
                field='unified_category',
                severity='error',
                issue_type='invalid_category',
                message=f"Invalid unified category: {product.unified_category}",
                value=product.unified_category,
                suggestion=f"Valid categories: {', '.join(sorted(self.valid_categories))}"
            ))
        
        # Check original category
        if not product.category:
            issues.append(ValidationIssue(
                field='category',
                severity='info',
                issue_type='missing_original_category',
                message="Original category is missing",
                value=None
            ))
        
        return issues
    
    def _validate_url(self, product: Product) -> List[ValidationIssue]:
        """Validate product URL"""
        issues = []
        
        if not product.url:
            return issues  # Already caught by required fields
        
        # Check URL format
        if not self.url_pattern.match(product.url):
            issues.append(ValidationIssue(
                field='url',
                severity='error',
                issue_type='invalid_url',
                message="Invalid URL format",
                value=product.url
            ))
        else:
            # Check domain matches retailer
            parsed = urlparse(product.url)
            domain = parsed.netloc.lower()
            
            retailer_domains = {
                'HP': 'homepro.co.th',
                'TWD': 'thaiwatsadu.com',
                'GH': 'globalhouse.co.th',
                'DH': 'dohome.co.th',
                'BT': 'boonthavorn.com',
                'MH': 'megahome.co.th'
            }
            
            expected_domain = retailer_domains.get(product.retailer_code)
            if expected_domain and expected_domain not in domain:
                issues.append(ValidationIssue(
                    field='url',
                    severity='warning',
                    issue_type='domain_mismatch',
                    message=f"URL domain doesn't match retailer",
                    value=domain,
                    suggestion=f"Expected domain containing: {expected_domain}"
                ))
        
        return issues
    
    def _validate_images(self, product: Product) -> List[ValidationIssue]:
        """Validate product images"""
        issues = []
        
        if not product.images or len(product.images) == 0:
            issues.append(ValidationIssue(
                field='images',
                severity='warning',
                issue_type='no_images',
                message="No product images found",
                value=None,
                suggestion="Products should have at least one image"
            ))
        else:
            # Check image URLs
            invalid_images = []
            for img in product.images:
                if not self.url_pattern.match(img):
                    invalid_images.append(img)
            
            if invalid_images:
                issues.append(ValidationIssue(
                    field='images',
                    severity='warning',
                    issue_type='invalid_image_urls',
                    message=f"Found {len(invalid_images)} invalid image URLs",
                    value=invalid_images[:3]  # Show first 3
                ))
            
            # Check for too many images
            if len(product.images) > 20:
                issues.append(ValidationIssue(
                    field='images',
                    severity='info',
                    issue_type='too_many_images',
                    message=f"Product has {len(product.images)} images",
                    value=len(product.images),
                    suggestion="Consider limiting to 10-15 best images"
                ))
        
        return issues
    
    def _validate_availability(self, product: Product) -> List[ValidationIssue]:
        """Validate availability status"""
        issues = []
        
        valid_statuses = ['in_stock', 'out_of_stock', 'unknown']
        
        if product.availability not in valid_statuses:
            issues.append(ValidationIssue(
                field='availability',
                severity='warning',
                issue_type='invalid_availability',
                message=f"Invalid availability status: {product.availability}",
                value=product.availability,
                suggestion=f"Valid values: {', '.join(valid_statuses)}"
            ))
        
        return issues
    
    def _validate_specifications(self, product: Product) -> List[ValidationIssue]:
        """Validate product specifications"""
        issues = []
        
        if product.specifications:
            # Check for empty values
            empty_specs = [k for k, v in product.specifications.items() if not v]
            if empty_specs:
                issues.append(ValidationIssue(
                    field='specifications',
                    severity='info',
                    issue_type='empty_spec_values',
                    message=f"Found {len(empty_specs)} specifications with empty values",
                    value=empty_specs[:5]  # Show first 5
                ))
            
            # Check for suspicious keys
            suspicious_keys = [k for k in product.specifications.keys() 
                             if 'ราคา' in k or 'price' in k.lower()]
            if suspicious_keys:
                issues.append(ValidationIssue(
                    field='specifications',
                    severity='warning',
                    issue_type='price_in_specs',
                    message="Price information found in specifications",
                    value=suspicious_keys,
                    suggestion="Price should be in price fields, not specifications"
                ))
        
        return issues
    
    def _calculate_quality_score(self, product: Product, issues: List[ValidationIssue]) -> float:
        """
        Calculate overall quality score for product
        
        Returns:
            Score from 0.0 (worst) to 1.0 (best)
        """
        # Start with perfect score
        score = 1.0
        
        # Deduct for issues
        error_count = sum(1 for i in issues if i.severity == 'error')
        warning_count = sum(1 for i in issues if i.severity == 'warning')
        info_count = sum(1 for i in issues if i.severity == 'info')
        
        # Errors have biggest impact
        score -= error_count * 0.2
        score -= warning_count * 0.05
        score -= info_count * 0.01
        
        # Bonus for completeness
        if product.brand:
            score += 0.05
        if product.description:
            score += 0.05
        if product.features and len(product.features) > 0:
            score += 0.05
        if product.specifications and len(product.specifications) > 0:
            score += 0.05
        if product.images and len(product.images) >= 3:
            score += 0.05
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def validate_batch(self, products: List[Product]) -> Dict[str, Any]:
        """
        Validate a batch of products and return summary
        
        Args:
            products: List of products to validate
            
        Returns:
            Summary statistics and issues
        """
        results = []
        
        for product in products:
            result = self.validate_product(product)
            results.append(result)
        
        # Calculate summary statistics
        total_products = len(results)
        valid_products = sum(1 for r in results if r.is_valid)
        total_errors = sum(r.get_error_count() for r in results)
        total_warnings = sum(r.get_warning_count() for r in results)
        avg_quality = sum(r.quality_score for r in results) / total_products if total_products > 0 else 0
        
        # Group issues by type
        issue_types = {}
        for result in results:
            for issue in result.issues:
                key = f"{issue.field}.{issue.issue_type}"
                if key not in issue_types:
                    issue_types[key] = {
                        'count': 0,
                        'severity': issue.severity,
                        'field': issue.field,
                        'type': issue.issue_type,
                        'examples': []
                    }
                issue_types[key]['count'] += 1
                if len(issue_types[key]['examples']) < 3:
                    issue_types[key]['examples'].append({
                        'product_sku': result.product_sku,
                        'value': issue.value,
                        'message': issue.message
                    })
        
        # Find products with lowest quality
        results.sort(key=lambda r: r.quality_score)
        worst_products = [
            {
                'sku': r.product_sku,
                'retailer': r.retailer_code,
                'quality_score': r.quality_score,
                'errors': r.get_error_count(),
                'warnings': r.get_warning_count()
            }
            for r in results[:10]  # Top 10 worst
        ]
        
        return {
            'summary': {
                'total_products': total_products,
                'valid_products': valid_products,
                'validation_rate': valid_products / total_products * 100 if total_products > 0 else 0,
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'average_quality_score': avg_quality
            },
            'issue_breakdown': sorted(issue_types.values(), key=lambda x: x['count'], reverse=True),
            'worst_products': worst_products,
            'validation_results': results
        }