"""
Retailer management API endpoints
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
import logging

from app.services.supabase_service import SupabaseService
from app.config.retailers import retailer_manager, RetailerType
from app.api.models import (
    MessageResponse,
    RetailerResponse,
    RetailerSummaryResponse,
    RetailerStatsResponse,
    RetailerCategoryResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["retailers"])


@router.get("", response_model=List[RetailerResponse])
async def get_all_retailers():
    """
    Get all configured retailers
    """
    retailers = []
    for retailer_config in retailer_manager.get_all_retailers():
        retailers.append(RetailerResponse(
            id=retailer_config.code,
            code=retailer_config.code,
            name=retailer_config.name,
            base_url=retailer_config.base_url,
            market_position=retailer_config.market_position,
            estimated_products=retailer_config.estimated_products,
            rate_limit_delay=retailer_config.rate_limit_delay,
            max_concurrent=retailer_config.max_concurrent,
            focus_categories=retailer_config.focus_categories,
            price_volatility=retailer_config.price_volatility,
            is_active=True  # All configured retailers are active
        ))
    
    return retailers


@router.get("/summary", response_model=List[RetailerSummaryResponse])
async def get_retailer_summary(request: Request):
    """
    Get summary statistics for all retailers
    """
    try:
        # Get Supabase client
        supabase: SupabaseService = request.app.state.supabase
        
        # Get all retailer codes
        retailer_codes = [r.code for r in retailer_manager.get_all_retailers()]
        
        summary = []
        for retailer_config in retailer_manager.get_all_retailers():
            code = retailer_config.code
            
            try:
                # Get product count and statistics for this retailer
                response = supabase.client.table('products')\
                    .select('id, current_price, availability, monitoring_tier, category, brand, scraped_at')\
                    .eq('retailer_code', code)\
                    .execute()
                
                products = response.data if response.data else []
            except Exception as e:
                logger.warning(f"Error fetching products for retailer {code}: {str(e)}")
                products = []
            total_products = len(products)
            
            if total_products > 0:
                # Calculate statistics
                in_stock = sum(1 for p in products if p.get('availability') == 'in_stock')
                priced = sum(1 for p in products if p.get('current_price') is not None)
                
                prices = [p['current_price'] for p in products if p.get('current_price')]
                avg_price = sum(prices) / len(prices) if prices else 0
                min_price = min(prices) if prices else 0
                max_price = max(prices) if prices else 0
                
                # Monitoring tier counts
                ultra_critical = sum(1 for p in products if p.get('monitoring_tier') == 'ultra_critical')
                high_value = sum(1 for p in products if p.get('monitoring_tier') == 'high_value')
                standard = sum(1 for p in products if p.get('monitoring_tier') == 'standard')
                low_priority = sum(1 for p in products if p.get('monitoring_tier') == 'low_priority')
                
                # Coverage calculations
                unique_categories = len(set(p['category'] for p in products if p.get('category')))
                unique_brands = len(set(p['brand'] for p in products if p.get('brand')))
                category_coverage = (unique_categories / total_products * 100) if total_products > 0 else 0
                brand_coverage = (unique_brands / total_products * 100) if total_products > 0 else 0
                
                # Last scraped
                scraped_dates = [p['scraped_at'] for p in products if p.get('scraped_at')]
                last_scraped = max(scraped_dates) if scraped_dates else None
                
                summary.append(RetailerSummaryResponse(
                    code=code,
                    name=retailer_config.name,
                    market_position=retailer_config.market_position,
                    actual_products=total_products,
                    in_stock_products=in_stock,
                    priced_products=priced,
                    avg_price=avg_price,
                    min_price=min_price,
                    max_price=max_price,
                    ultra_critical_count=ultra_critical,
                    high_value_count=high_value,
                    standard_count=standard,
                    low_priority_count=low_priority,
                    category_coverage_percentage=category_coverage,
                    brand_coverage_percentage=brand_coverage,
                    last_scraped_at=last_scraped
                ))
            else:
                # No data for this retailer yet
                summary.append(RetailerSummaryResponse(
                    code=code,
                    name=retailer_config.name,
                    market_position=retailer_config.market_position,
                    actual_products=0,
                    in_stock_products=0,
                    priced_products=0,
                    avg_price=0,
                    min_price=0,
                    max_price=0,
                    ultra_critical_count=0,
                    high_value_count=0,
                    standard_count=0,
                    low_priority_count=0,
                    category_coverage_percentage=0,
                    brand_coverage_percentage=0,
                    last_scraped_at=None
                ))
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting retailer summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get retailer summary")


@router.get("/monitoring-distribution", response_model=Dict[str, Any])
async def get_monitoring_distribution():
    """
    Get the monitoring tier distribution across all retailers
    """
    distribution = retailer_manager.calculate_monitoring_distribution()
    
    # Calculate totals
    total_ultra_critical = sum(r["ultra_critical"] for r in distribution.values())
    total_high_value = sum(r["high_value"] for r in distribution.values())
    total_standard = sum(r["standard"] for r in distribution.values())
    total_low_priority = sum(r["low_priority"] for r in distribution.values())
    total_products = sum(r["total"] for r in distribution.values())
    
    return {
        "by_retailer": distribution,
        "totals": {
            "ultra_critical": total_ultra_critical,
            "high_value": total_high_value,
            "standard": total_standard,
            "low_priority": total_low_priority,
            "total": total_products
        }
    }


@router.get("/{code}", response_model=RetailerResponse)
async def get_retailer_by_code(code: str):
    """
    Get a specific retailer by code
    """
    try:
        retailer_type = RetailerType(code.lower())
        retailer_config = retailer_manager.get_retailer(retailer_type)
        
        return RetailerResponse(
            id=retailer_config.code,
            code=retailer_config.code,
            name=retailer_config.name,
            base_url=retailer_config.base_url,
            market_position=retailer_config.market_position,
            estimated_products=retailer_config.estimated_products,
            rate_limit_delay=retailer_config.rate_limit_delay,
            max_concurrent=retailer_config.max_concurrent,
            focus_categories=retailer_config.focus_categories,
            price_volatility=retailer_config.price_volatility,
            is_active=True
        )
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Retailer '{code}' not found")


@router.get("/{code}/categories", response_model=List[RetailerCategoryResponse])
async def get_retailer_categories(code: str):
    """
    Get categories for a specific retailer
    """
    try:
        # Get retailer config
        try:
            # Map retailer codes to enum values
            code_to_enum = {
                'HP': RetailerType.HOMEPRO,
                'TWD': RetailerType.TWD,
                'GH': RetailerType.GLOBAL_HOUSE,
                'DH': RetailerType.DOHOME,
                'BT': RetailerType.BOONTHAVORN,
                'MH': RetailerType.MEGAHOME,
            }
            
            retailer_type = code_to_enum.get(code.upper())
            if not retailer_type:
                raise ValueError(f"Unknown retailer code: {code}")
                
            retailer_config = retailer_manager.get_retailer(retailer_type)
        except (ValueError, KeyError):
            raise HTTPException(status_code=404, detail=f"Retailer {code} not found")
        
        # Build category response from config
        categories = []
        for i, url in enumerate(retailer_config.category_urls):
            # Extract category code from URL
            if retailer_config.code == "HP":
                # HomePro: https://www.homepro.co.th/c/LIG
                parts = url.split("/c/")
                category_code = parts[-1] if len(parts) > 1 else f"CAT{i}"
                name_th = retailer_config.category_mapping.get(category_code, f"Category {i+1}")
                # Map Thai names to English
                th_to_en = {
                    'โคมไฟและหลอดไฟ': 'Lighting',
                    'สีและอุปกรณ์ทาสี': 'Paint & Equipment',
                    'เฟอร์นิเจอร์': 'Furniture',
                    'เครื่องใช้ไฟฟ้า': 'Appliances',
                    'ทีวีและเครื่องเสียง': 'TV & Audio',
                    'ห้องครัว': 'Kitchen',
                    'ห้องน้ำ': 'Bathroom',
                    'ของใช้ในบ้าน': 'Household',
                    'วัสดุก่อสร้าง': 'Construction',
                    'อิเล็กทรอนิกส์': 'Electronics',
                    'ประตูและหน้าต่าง': 'Doors & Windows',
                    'เครื่องมือ': 'Tools',
                    'ของใช้กลางแจ้ง': 'Outdoor',
                    'ห้องนอน': 'Bedroom',
                    'กีฬา': 'Sports',
                    'ความงาม': 'Beauty',
                    'แม่และเด็ก': 'Mom & Baby',
                    'สุขภาพ': 'Health',
                    'สัตว์เลี้ยง': 'Pet',
                    'ยานยนต์': 'Automotive',
                    'สวน': 'Garden',
                    'สำนักงาน': 'Office',
                    'ทำความสะอาด': 'Cleaning',
                }
                category_name = th_to_en.get(name_th, name_th)
            elif retailer_config.code == "TWD":
                # Thai Watsadu: https://www.thaiwatsadu.com/th/c/construction-materials
                parts = url.split("/c/")
                category_slug = parts[-1] if len(parts) > 1 else f"cat-{i}"
                # Map slugs to names
                slug_to_name = {
                    "construction-materials": ("Construction Materials", "วัสดุก่อสร้าง"),
                    "tools-hardware": ("Tools & Hardware", "เครื่องมือและฮาร์ดแวร์"),
                    "electrical-lighting": ("Electrical & Lighting", "ไฟฟ้าและแสงสว่าง"),
                    "plumbing-bathroom": ("Plumbing & Bathroom", "ประปาและห้องน้ำ"),
                    "paint-coating": ("Paint & Coating", "สีและสารเคลือบ"),
                    "flooring-tile": ("Flooring & Tile", "พื้นและกระเบื้อง"),
                    "roofing": ("Roofing", "หลังคา"),
                    "doors-windows": ("Doors & Windows", "ประตูและหน้าต่าง"),
                    "garden-outdoor": ("Garden & Outdoor", "สวนและกลางแจ้ง"),
                    "safety-security": ("Safety & Security", "ความปลอดภัย"),
                }
                category_code = category_slug.upper().replace("-", "_")[:3]
                name_en, name_th = slug_to_name.get(category_slug, (f"Category {i+1}", f"หมวดหมู่ {i+1}"))
                category_name = name_en
            else:
                # Generic handling for other retailers
                category_code = f"CAT{i}"
                category_name = f"Category {i+1}"
                name_th = f"หมวดหมู่ {i+1}"
            
            categories.append(RetailerCategoryResponse(
                code=category_code,
                name=category_name,
                name_th=name_th,
                url=url,
                estimated_products=retailer_config.estimated_products // len(retailer_config.category_urls)
            ))
        
        return categories
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting categories for retailer {code}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{code}/stats", response_model=RetailerStatsResponse)
async def get_retailer_stats(code: str, request: Request):
    """
    Get detailed statistics for a specific retailer
    """
    try:
        retailer_type = RetailerType(code.lower())
        retailer_config = retailer_manager.get_retailer(retailer_type)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Retailer '{code}' not found")
    
    try:
        # Get Supabase client
        supabase: SupabaseService = request.app.state.supabase
        
        # Get all products for this retailer
        response = supabase.client.table('products')\
            .select('id, current_price, availability, category, brand')\
            .eq('retailer_code', code)\
            .execute()
        
        products = response.data if response.data else []
        
        # Calculate statistics
        total_products = len(products)
        in_stock = sum(1 for p in products if p.get('availability') == 'in_stock')
        
        prices = [p['current_price'] for p in products if p.get('current_price')]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        unique_categories = len(set(p['category'] for p in products if p.get('category')))
        unique_brands = len(set(p['brand'] for p in products if p.get('brand')))
        
        # Calculate price distribution
        price_distribution = {
            '0-999': 0,
            '1000-2999': 0,
            '3000-9999': 0,
            '10000+': 0
        }
        
        for p in products:
            price = p.get('current_price')
            if price is not None:
                if price < 1000:
                    price_distribution['0-999'] += 1
                elif price < 3000:
                    price_distribution['1000-2999'] += 1
                elif price < 10000:
                    price_distribution['3000-9999'] += 1
                else:
                    price_distribution['10000+'] += 1
        
        # Get top categories
        category_counts = {}
        for p in products:
            cat = p.get('category')
            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        top_categories = sorted(
            [{"name": cat, "count": count} for cat, count in category_counts.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:10]
        
        return RetailerStatsResponse(
            retailer_code=code,
            retailer_name=retailer_config.name,
            total_products=total_products,
            in_stock_products=in_stock,
            average_price=avg_price,
            unique_categories=unique_categories,
            unique_brands=unique_brands,
            price_distribution=price_distribution,
            top_categories=top_categories
        )
        
    except Exception as e:
        logger.error(f"Error getting retailer stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get retailer statistics")


