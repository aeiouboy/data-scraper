# Code Organization Guide

This guide provides best practices for organizing code in the RIS Data Scrap project.

## 1. File Organization Best Practices

### Python Files

#### Module Structure
```python
"""
Module description explaining the purpose of this file.
"""
# Standard library imports
import os
import sys
from typing import List, Dict, Optional

# Third-party imports
import pandas as pd
from fastapi import APIRouter

# Local imports
from src.core.config import settings
from src.models.product import Product
from src.utils.text import normalize_text

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Module code follows...
```

#### Class Organization
```python
class ProductMatcher:
    """
    Product matching service with confidence scoring.
    
    This class handles cross-retailer product matching using
    multiple algorithms and confidence metrics.
    
    Attributes:
        config: Matching configuration
        logger: Logger instance
    
    Example:
        >>> matcher = ProductMatcher(config)
        >>> matches = matcher.match_products(products)
    """
    
    def __init__(self, config: MatchConfig):
        """Initialize the matcher with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._cache = {}
    
    # Public methods first
    def match_products(self, products: List[Product]) -> List[Match]:
        """Match products across retailers."""
        pass
    
    # Private methods follow
    def _calculate_confidence(self, p1: Product, p2: Product) -> float:
        """Calculate match confidence between two products."""
        pass
```

### Configuration Files

#### Environment Variables (.env)
```bash
# Application
APP_NAME="RIS Data Scrap"
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://user:pass@localhost/db
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-key-here

# API Keys
FIRECRAWL_API_KEY=your-firecrawl-key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

#### Settings Module (src/core/config.py)
```python
from pydantic import BaseSettings, validator
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Application
    app_name: str = "RIS Data Scrap"
    environment: str = "development"
    debug: bool = False
    
    # Database
    database_url: str
    supabase_url: str
    supabase_key: str
    
    # API Keys
    firecrawl_api_key: Optional[str]
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

## 2. API Organization

### Router Structure
```python
# src/api/routers/products.py
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from src.api.schemas.product import ProductResponse, ProductQuery
from src.services.product_service import ProductService
from src.api.dependencies import get_product_service

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=List[ProductResponse])
async def list_products(
    query: ProductQuery = Depends(),
    service: ProductService = Depends(get_product_service)
):
    """List products with filtering and pagination."""
    return await service.list_products(query)
```

### Schema Organization
```python
# src/api/schemas/product.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    """Base product schema."""
    name: str = Field(..., min_length=1, max_length=500)
    brand: Optional[str]
    category: Optional[str]
    
class ProductCreate(ProductBase):
    """Schema for creating products."""
    retailer_code: str
    url: str
    
class ProductResponse(ProductBase):
    """Schema for product responses."""
    id: str
    current_price: float
    created_at: datetime
    
    class Config:
        orm_mode = True
```

## 3. Service Layer Organization

### Service Pattern
```python
# src/services/product_service.py
from typing import List, Optional
from src.database.repositories.product_repo import ProductRepository
from src.models.domain.product import Product
from src.core.exceptions import ProductNotFoundError

class ProductService:
    """Business logic for product operations."""
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    async def get_product(self, product_id: str) -> Product:
        """Get a product by ID."""
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(f"Product {product_id} not found")
        return product
    
    async def list_products(self, filters: dict) -> List[Product]:
        """List products with filters."""
        return await self.repository.list_with_filters(filters)
```

## 4. Testing Organization

### Test Structure
```python
# tests/unit/services/test_product_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.services.product_service import ProductService
from src.core.exceptions import ProductNotFoundError

@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = Mock()
    repo.get_by_id = AsyncMock()
    repo.list_with_filters = AsyncMock()
    return repo

@pytest.fixture
def product_service(mock_repository):
    """Create product service with mock repository."""
    return ProductService(mock_repository)

class TestProductService:
    """Test product service operations."""
    
    async def test_get_product_success(self, product_service, mock_repository):
        """Test successful product retrieval."""
        # Arrange
        mock_repository.get_by_id.return_value = {"id": "123", "name": "Test"}
        
        # Act
        result = await product_service.get_product("123")
        
        # Assert
        assert result["id"] == "123"
        mock_repository.get_by_id.assert_called_once_with("123")
    
    async def test_get_product_not_found(self, product_service, mock_repository):
        """Test product not found error."""
        # Arrange
        mock_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ProductNotFoundError):
            await product_service.get_product("999")
```

## 5. Frontend Organization

### Component Structure
```typescript
// frontend/src/components/products/ProductCard.tsx
import React, { FC, memo } from 'react';
import { Card, CardContent, Typography } from '@mui/material';
import { Product } from '../../types/product';
import { formatPrice } from '../../utils/format';

interface ProductCardProps {
  product: Product;
  onClick?: (product: Product) => void;
}

export const ProductCard: FC<ProductCardProps> = memo(({ product, onClick }) => {
  const handleClick = () => {
    onClick?.(product);
  };
  
  return (
    <Card onClick={handleClick} sx={{ cursor: onClick ? 'pointer' : 'default' }}>
      <CardContent>
        <Typography variant="h6">{product.name}</Typography>
        <Typography variant="body2" color="text.secondary">
          {product.brand}
        </Typography>
        <Typography variant="h5" color="primary">
          {formatPrice(product.currentPrice)}
        </Typography>
      </CardContent>
    </Card>
  );
});

ProductCard.displayName = 'ProductCard';
```

### Custom Hook Example
```typescript
// frontend/src/hooks/useProducts.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productApi } from '../services/api';
import { Product, ProductFilters } from '../types/product';

export const useProducts = (filters: ProductFilters) => {
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => productApi.list(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useUpdateProduct = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: productApi.update,
    onSuccess: (data) => {
      queryClient.invalidateQueries(['products']);
      queryClient.setQueryData(['products', data.id], data);
    },
  });
};
```

## 6. Documentation Standards

### Function Documentation
```python
def calculate_match_confidence(
    product1: Product,
    product2: Product,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate confidence score for product match.
    
    Uses multiple factors including name similarity, brand match,
    and price consistency to determine match confidence.
    
    Args:
        product1: First product to compare
        product2: Second product to compare
        weights: Optional custom weights for factors
            - name_weight: Weight for name similarity (default: 0.4)
            - brand_weight: Weight for brand match (default: 0.3)
            - price_weight: Weight for price consistency (default: 0.3)
    
    Returns:
        Confidence score between 0 and 1
    
    Raises:
        ValueError: If weights don't sum to 1.0
    
    Example:
        >>> p1 = Product(name="iPhone 13", brand="Apple", price=25000)
        >>> p2 = Product(name="iPhone 13 Pro", brand="Apple", price=30000)
        >>> confidence = calculate_match_confidence(p1, p2)
        >>> print(f"Match confidence: {confidence:.2%}")
        Match confidence: 85.00%
    """
    pass
```

### API Documentation
```python
@router.post("/matches", response_model=MatchResponse)
async def create_match(
    match_data: MatchCreate,
    service: MatchService = Depends(get_match_service)
):
    """
    Create a new product match.
    
    Creates a cross-retailer product match with confidence scoring.
    
    **Request Body:**
    - `product_ids`: List of product IDs to match (2-10 products)
    - `confidence_override`: Optional manual confidence score
    
    **Response:**
    - `match_id`: Unique identifier for the match
    - `products`: List of matched products
    - `confidence`: Match confidence score
    - `created_at`: Timestamp of creation
    
    **Errors:**
    - `400`: Invalid product IDs or too few/many products
    - `404`: One or more products not found
    - `409`: Products already matched
    """
    return await service.create_match(match_data)
```

## 7. Naming Conventions

### Python
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### TypeScript/React
- **Files**: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- **Components**: `PascalCase`
- **Functions**: `camelCase`
- **Types/Interfaces**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`

### Database
- **Tables**: `snake_case` (plural)
- **Columns**: `snake_case`
- **Indexes**: `idx_table_column`
- **Foreign Keys**: `fk_table_reference`

## 8. Error Handling

### Custom Exceptions
```python
# src/core/exceptions.py
class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(message)

class ValidationError(AppException):
    """Validation error."""
    def __init__(self, message: str, field: str = None):
        super().__init__(message, code="VALIDATION_ERROR")
        self.field = field

class NotFoundError(AppException):
    """Resource not found."""
    def __init__(self, resource: str, id: str):
        message = f"{resource} with id {id} not found"
        super().__init__(message, code="NOT_FOUND")
```

### Error Handler
```python
# src/api/middleware/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from src.core.exceptions import AppException, NotFoundError

async def error_handler(request: Request, exc: Exception):
    """Global error handler."""
    if isinstance(exc, NotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": exc.code,
                "message": exc.message,
                "path": request.url.path
            }
        )
    
    # Log unexpected errors
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred"
        }
    )
```

## Summary

Following these organization patterns will:
1. Improve code maintainability
2. Make the codebase more navigable
3. Reduce bugs through consistent patterns
4. Speed up development
5. Improve team collaboration

Remember: Consistency is key. Choose patterns and stick to them throughout the project.