"""Factory for generating test products."""

import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from faker import Faker
from src.models.product import Product


fake = Faker(['th_TH', 'en_US'])


class ProductFactory:
    """Generate test products with realistic data."""
    
    RETAILERS = ['homepro', 'megahome', 'thaiwatsadu', 'boonthavorn']
    
    BRANDS = [
        'Bosch', 'Makita', 'Stanley', 'DeWalt', '3M',
        'TOA', 'Nippon', 'Dulux', 'Jotun', 'Beger',
        'SCG', 'Cotto', 'American Standard', 'Kohler', 'TOTO'
    ]
    
    CATEGORIES = {
        'power_tools': ['Drills', 'Saws', 'Sanders', 'Grinders'],
        'hand_tools': ['Hammers', 'Screwdrivers', 'Wrenches', 'Pliers'],
        'paint': ['Interior Paint', 'Exterior Paint', 'Primers', 'Wood Stain'],
        'tiles': ['Floor Tiles', 'Wall Tiles', 'Ceramic Tiles', 'Porcelain Tiles'],
        'bathroom': ['Toilets', 'Sinks', 'Faucets', 'Showers']
    }
    
    @classmethod
    def create(
        cls,
        retailer_code: Optional[str] = None,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        price_range: tuple = (100, 10000),
        **kwargs
    ) -> Product:
        """Create a single product with realistic data."""
        
        retailer_code = retailer_code or random.choice(cls.RETAILERS)
        brand = brand or random.choice(cls.BRANDS)
        
        # Select category
        if category:
            main_cat = category
            sub_cats = cls.CATEGORIES.get(category, [category])
        else:
            main_cat = random.choice(list(cls.CATEGORIES.keys()))
            sub_cats = cls.CATEGORIES[main_cat]
        
        sub_cat = random.choice(sub_cats) if sub_cats else main_cat
        
        # Generate SKU
        sku = f"{retailer_code.upper()}-{fake.bothify('???-#####').upper()}"
        
        # Generate name
        if random.random() > 0.5:  # 50% chance of Thai name
            name = f"{brand} {fake.word()} {sub_cat} {fake.bothify('### ??')}"
        else:
            name = f"{brand} {fake.word().title()} {sub_cat} Model {fake.bothify('??-###')}"
        
        # Generate prices
        current_price = round(random.uniform(*price_range), 2)
        is_promotion = random.random() > 0.7  # 30% chance of promotion
        
        if is_promotion:
            discount = random.uniform(0.1, 0.3)  # 10-30% discount
            original_price = round(current_price / (1 - discount), 2)
        else:
            original_price = current_price
        
        # Generate specifications
        specs = cls._generate_specifications(main_cat, sub_cat)
        
        # Create product
        product_data = {
            'retailer_code': retailer_code,
            'sku': sku,
            'name': name,
            'current_price': current_price,
            'original_price': original_price,
            'brand': brand,
            'category': f"{main_cat}/{sub_cat}",
            'is_promotion': is_promotion,
            'specifications': specs,
            'in_stock': random.random() > 0.1,  # 90% in stock
            'image_url': f"https://example.com/{retailer_code}/{sku}.jpg",
            'product_url': f"https://{retailer_code}.com/product/{sku}",
            'last_updated': datetime.utcnow() - timedelta(hours=random.randint(0, 72))
        }
        
        # Override with any provided kwargs
        product_data.update(kwargs)
        
        return Product(**product_data)
    
    @classmethod
    def create_batch(
        cls,
        count: int,
        retailer_code: Optional[str] = None,
        **kwargs
    ) -> list[Product]:
        """Create multiple products."""
        return [cls.create(retailer_code=retailer_code, **kwargs) for _ in range(count)]
    
    @classmethod
    def create_matching_pair(
        cls,
        confidence: float = 0.85,
        different_retailers: bool = True
    ) -> tuple[Product, Product]:
        """Create two products that should match."""
        
        # Base product
        product1 = cls.create()
        
        # Create matching product
        retailer2 = random.choice([r for r in cls.RETAILERS if r != product1.retailer_code]) if different_retailers else product1.retailer_code
        
        # Slightly modify the name
        name_variations = [
            product1.name,
            product1.name.upper(),
            product1.name.lower(),
            product1.name.replace(' ', '-'),
            f"{product1.brand} - {product1.name.split(product1.brand)[-1].strip()}"
        ]
        
        product2 = cls.create(
            retailer_code=retailer2,
            brand=product1.brand,
            category=product1.category.split('/')[0],
            name=random.choice(name_variations),
            current_price=product1.current_price * random.uniform(0.95, 1.05)
        )
        
        return product1, product2
    
    @classmethod
    def _generate_specifications(cls, category: str, subcategory: str) -> Dict[str, Any]:
        """Generate category-specific specifications."""
        
        specs = {}
        
        if category == 'power_tools':
            specs.update({
                'power': f"{random.choice([400, 600, 800, 1000, 1200])}W",
                'voltage': f"{random.choice([110, 220])}V",
                'speed': f"{random.randint(1000, 3000)} rpm",
                'weight': f"{round(random.uniform(1.5, 5.0), 1)} kg"
            })
        
        elif category == 'hand_tools':
            specs.update({
                'material': random.choice(['Steel', 'Chrome Vanadium', 'Carbon Steel']),
                'handle': random.choice(['Rubber', 'Wood', 'Fiberglass', 'Plastic']),
                'length': f"{random.randint(15, 50)} cm",
                'weight': f"{random.randint(200, 2000)} g"
            })
        
        elif category == 'paint':
            specs.update({
                'volume': f"{random.choice([1, 3, 5, 18])} L",
                'coverage': f"{random.randint(8, 15)} sqm/L",
                'finish': random.choice(['Matt', 'Eggshell', 'Satin', 'Gloss']),
                'drying_time': f"{random.randint(2, 6)} hours"
            })
        
        elif category == 'tiles':
            size = random.choice([30, 40, 60, 80, 100])
            specs.update({
                'size': f"{size}x{size} cm",
                'thickness': f"{random.randint(8, 12)} mm",
                'surface': random.choice(['Glossy', 'Matt', 'Textured', 'Polished']),
                'usage': random.choice(['Floor', 'Wall', 'Floor/Wall'])
            })
        
        elif category == 'bathroom':
            specs.update({
                'material': random.choice(['Ceramic', 'Porcelain', 'Stainless Steel']),
                'color': random.choice(['White', 'Beige', 'Grey', 'Black']),
                'installation': random.choice(['Wall-mounted', 'Floor-mounted', 'Countertop']),
                'warranty': f"{random.choice([1, 2, 5, 10])} years"
            })
        
        return specs