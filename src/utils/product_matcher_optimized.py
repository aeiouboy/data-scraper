"""
Optimized Product Matcher with Improved Matching Rates
Addresses low matching rates while maintaining accuracy
"""
import re
import logging
import math
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
from decimal import Decimal
import unicodedata
from difflib import SequenceMatcher
import numpy as np

from src.utils.text_normalizer_advanced import AdvancedTextNormalizer

logger = logging.getLogger(__name__)

@dataclass
class OptimizedMatchResult:
    """Optimized match result with enhanced scoring details"""
    confidence: float
    match_type: str  # 'exact', 'high', 'medium', 'low', 'none'
    details: Dict[str, float]
    matched_fields: List[str]
    warnings: List[str]
    linguistic_scores: Dict[str, float]
    progressive_scores: Dict[str, float]  # Multi-tier scoring
    
class OptimizedProductMatcher:
    """Optimized product matcher with improved matching rates"""
    
    def __init__(self):
        self.normalizer = AdvancedTextNormalizer()
        
        # Relaxed thresholds for better matching rates
        self.thresholds = {
            'exact': 0.92,      # Slightly relaxed from 0.95
            'high': 0.75,       # Significantly relaxed from 0.85
            'medium': 0.55,     # Relaxed from 0.70
            'low': 0.35         # Much more permissive from 0.55
        }
        
        # Progressive matching tiers
        self.progressive_tiers = {
            'strict': {
                'name_similarity_min': 0.85,
                'brand_similarity_min': 0.90,
                'sku_similarity_min': 0.95,
                'spec_similarity_min': 0.80,
                'price_variance_max': 0.15
            },
            'moderate': {
                'name_similarity_min': 0.65,
                'brand_similarity_min': 0.75,
                'sku_similarity_min': 0.80,
                'spec_similarity_min': 0.60,
                'price_variance_max': 0.30
            },
            'relaxed': {
                'name_similarity_min': 0.45,
                'brand_similarity_min': 0.55,
                'sku_similarity_min': 0.65,
                'spec_similarity_min': 0.40,
                'price_variance_max': 0.50
            },
            'fuzzy': {
                'name_similarity_min': 0.25,
                'brand_similarity_min': 0.35,
                'sku_similarity_min': 0.45,
                'spec_similarity_min': 0.20,
                'price_variance_max': 0.75
            }
        }
        
        # Enhanced weight profiles with more balanced scoring
        self.weight_profiles = {
            'electronics': {
                'sku': 0.30,      # Reduced from 0.40
                'brand': 0.25,    
                'name': 0.20,     # Increased from 0.10
                'specs': 0.20,    
                'category': 0.05  
            },
            'appliances': {
                'sku': 0.25,      # Reduced from 0.35
                'brand': 0.25,    
                'name': 0.25,     # Increased from 0.15
                'specs': 0.20,    
                'category': 0.05  
            },
            'general': {
                'sku': 0.20,      # Reduced from 0.30
                'brand': 0.25,    
                'name': 0.35,     # Increased from 0.25
                'specs': 0.15,    
                'category': 0.05  
            }
        }
        
        # Enhanced brand mapping with more variations
        self.enhanced_brand_mapping = {
            # Thai to English
            'มิตซูบิชิ': ['mitsubishi', 'mitsubishi electric', 'mitsu'],
            'ไดกิ้น': ['daikin', 'daikin industries'],
            'แอลจี': ['lg', 'lg electronics', 'life good'],
            'ซัมซุง': ['samsung', 'samsung electronics'],
            'โตชิบา': ['toshiba', 'toshiba corporation'],
            'ปานาโซนิค': ['panasonic', 'panasonic corporation'],
            'ฮิตาชิ': ['hitachi', 'hitachi ltd'],
            'ฟูจิตสึ': ['fujitsu', 'fujitsu general'],
            'ไฮเออร์': ['haier', 'haier group'],
            'แคเรียร์': ['carrier', 'carrier corporation'],
            'ยอร์ค': ['york', 'york international'],
            'เซ็นทรัล': ['central', 'central air'],
            'ไซโจ เดนกิ': ['saijo denki', 'saijo'],
            'แอมเวย์': ['amway', 'amway corporation'],
            'เทคนิก': ['tcl', 'tcl electronics'],
            'ฮอนด้า': ['honda', 'honda motor'],
            'ยามาฮ่า': ['yamaha', 'yamaha corporation'],
            'ซูซูกิ': ['suzuki', 'suzuki motor'],
            'คาวาซากิ': ['kawasaki', 'kawasaki heavy'],
            'โซนี่': ['sony', 'sony corporation'],
            'ฟิลิปส์': ['philips', 'philips electronics'],
            'บอช': ['bosch', 'bosch group'],
            'ไซเมนส์': ['siemens', 'siemens ag'],
            'วิร์ลพูล': ['whirlpool', 'whirlpool corporation'],
            'อีเลคโทรลักซ์': ['electrolux', 'electrolux ab'],
            'เจนเนอรัลอิเล็กทริก': ['ge', 'general electric'],
            'เฟรดิแดร์': ['frigidaire', 'frigidaire home'],
            'เคนมอร์': ['kenmore', 'kenmore appliances'],
            'มายเทก': ['maytag', 'maytag corporation'],
            'ไฮเซนส์': ['hisense', 'hisense group'],
            'ฮาร์ป': ['sharp', 'sharp corporation'],
            'บาลมูดา': ['balmuda', 'balmuda inc'],
            'ไดสัน': ['dyson', 'dyson ltd'],
            'มิเล่': ['miele', 'miele company'],
            'ไวกิ้ง': ['viking', 'viking range'],
            'ซับซีโร่': ['sub-zero', 'sub-zero group'],
            'วูล์ฟ': ['wolf', 'wolf appliances'],
            'เทอร์มาดอร์': ['thermador', 'thermador home'],
            'จีเอ มอนแกรม': ['ge monogram', 'monogram appliances'],
            'คาเฟ่': ['cafe', 'cafe appliances'],
            'ฮาร์ทแลนด์': ['heartland', 'heartland appliances'],
            'บิ๊กชิลล์': ['big chill', 'big chill appliances'],
            'สมิก': ['smeg', 'smeg spa'],
            'ไฟเออร์': ['fisher', 'fisher appliances'],
            'ดีซีเอส': ['dcs', 'dcs appliances'],
            'ลินเนีย': ['lynx', 'lynx professional'],
            'ทูร์โบแอร์': ['turbo air', 'turbo air inc'],
            'ลูทรอน': ['lutron', 'lutron electronics'],
            'เนสต์': ['nest', 'nest labs'],
            'ฮันนีเวล': ['honeywell', 'honeywell international'],
            'เอเมอร์สัน': ['emerson', 'emerson electric'],
            'ไวท์ เวสติ้งเฮาส์': ['westinghouse', 'westinghouse electric'],
            'เจเนอรัลอิเล็กทริก': ['ge', 'general electric'],
            'ไวท์-เวสติ้งเฮาส์': ['white-westinghouse', 'white westinghouse'],
            'โกลด์สตาร์': ['goldstar', 'gold star'],
            'เคนมอร์-เอลิต': ['kenmore elite', 'kenmore elite appliances'],
            'อะมาน่า': ['amana', 'amana corporation'],
            'โรเปอร์': ['roper', 'roper appliances'],
            'เอสเตท': ['estate', 'estate appliances'],
            'อิงลิส': ['inglis', 'inglis appliances'],
            'โครสลีย์': ['crosley', 'crosley appliances'],
            'คิทเช่นเอด': ['kitchenaid', 'kitchenaid appliances'],
            'จีอี โปรไฟล์': ['ge profile', 'ge profile appliances'],
            'จีอี สปอร์ต': ['ge spacemaker', 'ge spacemaker appliances'],
            'จีอี เอาท์ดอร์': ['ge outdoor', 'ge outdoor appliances'],
            'โฮตพอยท์': ['hotpoint', 'hotpoint appliances'],
            'โฮเวอร์': ['hoover', 'hoover company'],
            'โจท์เทม': ['jotul', 'jotul north america'],
            'ลูเธอร์': ['luther', 'luther appliances'],
            'คอนเทมโพ': ['contempo', 'contempo appliances'],
            'ซูเปอร์บา': ['superba', 'superba appliances'],
            'ฟริจิแดร์ แกลเลอรี่': ['frigidaire gallery', 'frigidaire gallery appliances'],
            'ฟริจิแดร์ โปรเฟสชันนัล': ['frigidaire professional', 'frigidaire professional appliances'],
            'จีอี อาทิซาน': ['ge artistry', 'ge artistry appliances'],
            'จีอี ฮาร์โมนี': ['ge harmony', 'ge harmony appliances'],
            'จีอี โปรไฟล์ สปีริต': ['ge profile spire', 'ge profile spire appliances'],
            'โครสลีย์ แอ็คเทรส': ['crosley actress', 'crosley actress appliances'],
            'เคนมอร์ เอลิต': ['kenmore elite', 'kenmore elite appliances'],
            'อะมาน่า ออกซิเจน': ['amana oxygen', 'amana oxygen appliances'],
            'วิร์ลพูล ดูแอต': ['whirlpool duet', 'whirlpool duet appliances'],
            'วิร์ลพูล แคบริโอ': ['whirlpool cabrio', 'whirlpool cabrio appliances'],
            'เมย์แทก เนปจูน': ['maytag neptune', 'maytag neptune appliances'],
            'เมย์แทก บราโว': ['maytag bravo', 'maytag bravo appliances'],
            'อิเล็กโทรลักซ์ ไอคิว ทัช': ['electrolux iq-touch', 'electrolux iq-touch appliances'],
            'อิเล็กโทรลักซ์ เพอร์เฟกต์ สตีม': ['electrolux perfect steam', 'electrolux perfect steam appliances'],
            'บอช แอสไคท์': ['bosch ascenta', 'bosch ascenta appliances'],
            'บอช เนกซ์ต': ['bosch nexxt', 'bosch nexxt appliances'],
            'ซีแมนส์ ไอคิว': ['siemens iq', 'siemens iq appliances'],
            'ซีแมนส์ สตูดิโอ': ['siemens studio', 'siemens studio appliances'],
            'ไฮเออร์ ไอแมก': ['haier i-mag', 'haier i-mag appliances'],
            'ไฮเออร์ ไอเคิร์ฟ': ['haier i-curve', 'haier i-curve appliances'],
            'แอลจี ทรูบาลานซ์': ['lg tru balance', 'lg tru balance appliances'],
            'แอลจี สตีมแอร์': ['lg steam air', 'lg steam air appliances'],
            'ซัมซุง ไอแคร์': ['samsung i-care', 'samsung i-care appliances'],
            'ซัมซุง ไอซีแคร์': ['samsung ice care', 'samsung ice care appliances'],
            'โตชิบา ไอไซคิล': ['toshiba i-cycle', 'toshiba i-cycle appliances'],
            'โตชิบา ไอเซนส์': ['toshiba i-sense', 'toshiba i-sense appliances'],
            'ปานาโซนิค ไอคิว': ['panasonic iq', 'panasonic iq appliances'],
            'ปานาโซนิค ไอแคร์': ['panasonic i-care', 'panasonic i-care appliances'],
            'ฮิตาชิ ไอแคร์': ['hitachi i-care', 'hitachi i-care appliances'],
            'ฮิตาชิ ไอเซนส์': ['hitachi i-sense', 'hitachi i-sense appliances'],
            'ฟูจิตสึ ไอคิว': ['fujitsu iq', 'fujitsu iq appliances'],
            'ฟูจิตสึ ไอแคร์': ['fujitsu i-care', 'fujitsu i-care appliances'],
            'แคเรียร์ ไอคิว': ['carrier iq', 'carrier iq appliances'],
            'แคเรียร์ ไอแคร์': ['carrier i-care', 'carrier i-care appliances'],
            'ยอร์ค ไอคิว': ['york iq', 'york iq appliances'],
            'ยอร์ค ไอแคร์': ['york i-care', 'york i-care appliances'],
            'เซ็นทรัล ไอคิว': ['central iq', 'central iq appliances'],
            'เซ็นทรัล ไอแคร์': ['central i-care', 'central i-care appliances'],
            'ไซโจ เดนกิ ไอคิว': ['saijo denki iq', 'saijo denki iq appliances'],
            'ไซโจ เดนกิ ไอแคร์': ['saijo denki i-care', 'saijo denki i-care appliances'],
            'แอมเวย์ ไอคิว': ['amway iq', 'amway iq appliances'],
            'แอมเวย์ ไอแคร์': ['amway i-care', 'amway i-care appliances'],
            'เทคนิก ไอคิว': ['tcl iq', 'tcl iq appliances'],
            'เทคนิก ไอแคร์': ['tcl i-care', 'tcl i-care appliances'],
            
            # English variations
            'mitsubishi': ['mitsubishi electric', 'mitsu', 'มิตซูบิชิ'],
            'daikin': ['daikin industries', 'ไดกิ้น'],
            'lg': ['lg electronics', 'life good', 'แอลจี'],
            'samsung': ['samsung electronics', 'ซัมซุง'],
            'toshiba': ['toshiba corporation', 'โตชิบา'],
            'panasonic': ['panasonic corporation', 'ปานาโซนิค'],
            'hitachi': ['hitachi ltd', 'ฮิตาชิ'],
            'fujitsu': ['fujitsu general', 'ฟูจิตสึ'],
            'haier': ['haier group', 'ไฮเออร์'],
            'carrier': ['carrier corporation', 'แคเรียร์'],
            'york': ['york international', 'ยอร์ค'],
            'central': ['central air', 'เซ็นทรัล'],
            'saijo': ['saijo denki', 'ไซโจ เดนกิ'],
            'amway': ['amway corporation', 'แอมเวย์'],
            'tcl': ['tcl electronics', 'เทคนิก'],
            'honda': ['honda motor', 'ฮอนด้า'],
            'yamaha': ['yamaha corporation', 'ยามาฮ่า'],
            'suzuki': ['suzuki motor', 'ซูซูกิ'],
            'kawasaki': ['kawasaki heavy', 'คาวาซากิ'],
            'sony': ['sony corporation', 'โซนี่'],
            'philips': ['philips electronics', 'ฟิลิปส์'],
            'bosch': ['bosch group', 'บอช'],
            'siemens': ['siemens ag', 'ไซเมนส์'],
            'whirlpool': ['whirlpool corporation', 'วิร์ลพูล'],
            'electrolux': ['electrolux ab', 'อีเลคโทรลักซ์'],
            'ge': ['general electric', 'เจนเนอรัลอิเล็กทริก'],
            'frigidaire': ['frigidaire home', 'เฟรดิแดร์'],
            'kenmore': ['kenmore appliances', 'เคนมอร์'],
            'maytag': ['maytag corporation', 'มายเทก'],
            'hisense': ['hisense group', 'ไฮเซนส์'],
            'sharp': ['sharp corporation', 'ฮาร์ป'],
            'balmuda': ['balmuda inc', 'บาลมูดา'],
            'dyson': ['dyson ltd', 'ไดสัน'],
            'miele': ['miele company', 'มิเล่'],
            'viking': ['viking range', 'ไวกิ้ง'],
            'sub-zero': ['sub-zero group', 'ซับซีโร่'],
            'wolf': ['wolf appliances', 'วูล์ฟ'],
            'thermador': ['thermador home', 'เทอร์มาดอร์'],
            'monogram': ['ge monogram', 'จีเอ มอนแกรม'],
            'cafe': ['cafe appliances', 'คาเฟ่'],
            'heartland': ['heartland appliances', 'ฮาร์ทแลนด์'],
            'big chill': ['big chill appliances', 'บิ๊กชิลล์'],
            'smeg': ['smeg spa', 'สมิก'],
            'fisher': ['fisher appliances', 'ไฟเออร์'],
            'dcs': ['dcs appliances', 'ดีซีเอส'],
            'lynx': ['lynx professional', 'ลินเนีย'],
            'turbo air': ['turbo air inc', 'ทูร์โบแอร์'],
            'lutron': ['lutron electronics', 'ลูทรอน'],
            'nest': ['nest labs', 'เนสต์'],
            'honeywell': ['honeywell international', 'ฮันนีเวล'],
            'emerson': ['emerson electric', 'เอเมอร์สัน'],
            'westinghouse': ['westinghouse electric', 'ไวท์ เวสติ้งเฮาส์'],
            'white-westinghouse': ['white westinghouse', 'ไวท์-เวสติ้งเฮาส์'],
            'goldstar': ['gold star', 'โกลด์สตาร์'],
            'kenmore elite': ['kenmore elite appliances', 'เคนมอร์-เอลิต'],
            'amana': ['amana corporation', 'อะมาน่า'],
            'roper': ['roper appliances', 'โรเปอร์'],
            'estate': ['estate appliances', 'เอสเตท'],
            'inglis': ['inglis appliances', 'อิงลิส'],
            'crosley': ['crosley appliances', 'โครสลีย์'],
            'kitchenaid': ['kitchenaid appliances', 'คิทเช่นเอด'],
            'ge profile': ['ge profile appliances', 'จีอี โปรไฟล์'],
            'ge spacemaker': ['ge spacemaker appliances', 'จีอี สปอร์ต'],
            'ge outdoor': ['ge outdoor appliances', 'จีอี เอาท์ดอร์'],
            'hotpoint': ['hotpoint appliances', 'โฮตพอยท์'],
            'hoover': ['hoover company', 'โฮเวอร์'],
            'jotul': ['jotul north america', 'โจท์เทม'],
            'luther': ['luther appliances', 'ลูเธอร์'],
            'contempo': ['contempo appliances', 'คอนเทมโพ'],
            'superba': ['superba appliances', 'ซูเปอร์บา'],
            'frigidaire gallery': ['frigidaire gallery appliances', 'ฟริจิแดร์ แกลเลอรี่'],
            'frigidaire professional': ['frigidaire professional appliances', 'ฟริจิแดร์ โปรเฟสชันนัล'],
            'ge artistry': ['ge artistry appliances', 'จีอี อาทิซาน'],
            'ge harmony': ['ge harmony appliances', 'จีอี ฮาร์โมนี'],
            'ge profile spire': ['ge profile spire appliances', 'จีอี โปรไฟล์ สปีริต'],
            'crosley actress': ['crosley actress appliances', 'โครสลีย์ แอ็คเทรส'],
            'amana oxygen': ['amana oxygen appliances', 'อะมาน่า ออกซิเจน'],
            'whirlpool duet': ['whirlpool duet appliances', 'วิร์ลพูล ดูแอต'],
            'whirlpool cabrio': ['whirlpool cabrio appliances', 'วิร์ลพูล แคบริโอ'],
            'maytag neptune': ['maytag neptune appliances', 'เมย์แทก เนปจูน'],
            'maytag bravo': ['maytag bravo appliances', 'เมย์แทก บราโว'],
            'electrolux iq-touch': ['electrolux iq-touch appliances', 'อิเล็กโทรลักซ์ ไอคิว ทัช'],
            'electrolux perfect steam': ['electrolux perfect steam appliances', 'อิเล็กโทรลักซ์ เพอร์เฟกต์ สตีม'],
            'bosch ascenta': ['bosch ascenta appliances', 'บอช แอสไคท์'],
            'bosch nexxt': ['bosch nexxt appliances', 'บอช เนกซ์ต'],
            'siemens iq': ['siemens iq appliances', 'ซีแมนส์ ไอคิว'],
            'siemens studio': ['siemens studio appliances', 'ซีแมนส์ สตูดิโอ'],
            'haier i-mag': ['haier i-mag appliances', 'ไฮเออร์ ไอแมก'],
            'haier i-curve': ['haier i-curve appliances', 'ไฮเออร์ ไอเคิร์ฟ'],
            'lg tru balance': ['lg tru balance appliances', 'แอลจี ทรูบาลานซ์'],
            'lg steam air': ['lg steam air appliances', 'แอลจี สตีมแอร์'],
            'samsung i-care': ['samsung i-care appliances', 'ซัมซุง ไอแคร์'],
            'samsung ice care': ['samsung ice care appliances', 'ซัมซุง ไอซีแคร์'],
            'toshiba i-cycle': ['toshiba i-cycle appliances', 'โตชิบา ไอไซคิล'],
            'toshiba i-sense': ['toshiba i-sense appliances', 'โตชิบา ไอเซนส์'],
            'panasonic iq': ['panasonic iq appliances', 'ปานาโซนิค ไอคิว'],
            'panasonic i-care': ['panasonic i-care appliances', 'ปานาโซนิค ไอแคร์'],
            'hitachi i-care': ['hitachi i-care appliances', 'ฮิตาชิ ไอแคร์'],
            'hitachi i-sense': ['hitachi i-sense appliances', 'ฮิตาชิ ไอเซนส์'],
            'fujitsu iq': ['fujitsu iq appliances', 'ฟูจิตสึ ไอคิว'],
            'fujitsu i-care': ['fujitsu i-care appliances', 'ฟูจิตสึ ไอแคร์'],
            'carrier iq': ['carrier iq appliances', 'แคเรียร์ ไอคิว'],
            'carrier i-care': ['carrier i-care appliances', 'แคเรียร์ ไอแคร์'],
            'york iq': ['york iq appliances', 'ยอร์ค ไอคิว'],
            'york i-care': ['york i-care appliances', 'ยอร์ค ไอแคร์'],
            'central iq': ['central iq appliances', 'เซ็นทรัล ไอคิว'],
            'central i-care': ['central i-care appliances', 'เซ็นทรัล ไอแคร์'],
            'saijo denki iq': ['saijo denki iq appliances', 'ไซโจ เดนกิ ไอคิว'],
            'saijo denki i-care': ['saijo denki i-care appliances', 'ไซโจ เดนกิ ไอแคร์'],
            'amway iq': ['amway iq appliances', 'แอมเวย์ ไอคิว'],
            'amway i-care': ['amway i-care appliances', 'แอมเวย์ ไอแคร์'],
            'tcl iq': ['tcl iq appliances', 'เทคนิก ไอคิว'],
            'tcl i-care': ['tcl i-care appliances', 'เทคนิก ไอแคร์'],
        }
        
        # Enhanced phonetic patterns
        self.phonetic_patterns = self._build_enhanced_phonetic_patterns()
        
        # Relaxed specification tolerances
        self.spec_tolerances = {
            'size': {'default': 0.05, 'display': 0.02},      # More tolerant
            'capacity': {'default': 0.10, 'cooling': 0.15},  # More tolerant
            'power': {'default': 0.10, 'exact': 0.05},       # More tolerant
            'weight': {'default': 0.10},                     # More tolerant
            'voltage': {'default': 0.05},                    # More tolerant
            'frequency': {'default': 0.01}                   # Keep strict
        }
        
        # Confidence boosting factors
        self.confidence_boosters = {
            'exact_sku_match': 0.15,
            'exact_brand_match': 0.10,
            'phonetic_match': 0.08,
            'semantic_match': 0.06,
            'spec_match': 0.05,
            'cross_validation': 0.03
        }
        
        # Reduced penalty factors
        self.penalty_factors = {
            'price_variance': 0.85,      # Reduced penalty
            'category_mismatch': 0.90,   # Reduced penalty
            'brand_mismatch': 0.85,      # Reduced penalty
            'critical_spec_mismatch': 0.80  # Reduced penalty
        }
        
    def _build_enhanced_phonetic_patterns(self) -> Dict[str, List[str]]:
        """Build enhanced phonetic patterns with more variations"""
        return {
            # Consonants
            'ph': ['พ', 'ภ', 'ฟ', 'p', 'f'],
            'th': ['ท', 'ธ', 'ต', 'ถ', 't', 'd'],
            'ch': ['ช', 'ฉ', 'จ', 'c', 'j'],
            'kh': ['ค', 'ข', 'ก', 'k', 'g'],
            'ng': ['ง', 'n', 'nk'],
            's': ['ส', 'ศ', 'ซ', 'z', 'c'],
            'r': ['ร', 'ล', 'l'],
            'l': ['ล', 'ร', 'r'],
            'n': ['น', 'ณ', 'm'],
            'm': ['ม', 'n'],
            'k': ['ก', 'ค', 'ข', 'g'],
            'g': ['ก', 'ค', 'ข', 'k'],
            't': ['ต', 'ท', 'ธ', 'd'],
            'd': ['ด', 'ต', 'ท', 't'],
            'p': ['ป', 'พ', 'ภ', 'b'],
            'b': ['บ', 'ป', 'พ', 'p'],
            'f': ['ฟ', 'พ', 'ภ', 'p'],
            'v': ['ว', 'w', 'f'],
            'w': ['ว', 'v'],
            'y': ['ย', 'j'],
            'j': ['จ', 'ย', 'y'],
            'z': ['ซ', 'ส', 's'],
            'x': ['ซ', 'ส', 'z'],
            'c': ['ซ', 'ส', 'k'],
            'q': ['ค', 'ก', 'k'],
            'h': ['ห', 'ฮ'],
            
            # Vowels
            'a': ['า', 'ะ', 'ั', 'e', 'o'],
            'i': ['ิ', 'ี', 'e', 'y'],
            'u': ['ุ', 'ู', 'o'],
            'e': ['เ', 'แ', 'a', 'i'],
            'o': ['โ', 'อ', 'a', 'u'],
            'ae': ['แ', 'e', 'a'],
            'ai': ['ไ', 'ใ', 'i', 'y'],
            'ue': ['ื', 'ึ', 'u', 'e'],
            'oe': ['เอ', 'o', 'e'],
            'au': ['เา', 'aw', 'o'],
            'aw': ['อ', 'au', 'o'],
            'oo': ['ู', 'u', 'o'],
            'ee': ['ี', 'i', 'e'],
            'aa': ['า', 'a'],
            'ii': ['ี', 'i'],
            'uu': ['ู', 'u'],
            'eo': ['เอ', 'e', 'o'],
            'ow': ['อ', 'o', 'au'],
            'oy': ['อย', 'oi', 'y'],
            'oi': ['อย', 'oy', 'y'],
            'ia': ['เีย', 'ya', 'i'],
            'ua': ['ัว', 'wa', 'u'],
            'ya': ['ยา', 'ia', 'y'],
            'wa': ['วา', 'ua', 'w'],
            
            # Complex sounds
            'tion': ['ชั่น', 'ชัน', 'ซัน'],
            'sion': ['ซัน', 'ชัน', 'ชั่น'],
            'ing': ['อิง', 'อิ่ง', 'อิ้ง'],
            'ness': ['เนส', 'เนสส์', 'เนส'],
            'ment': ['เมนต์', 'เมน', 'เมนท์'],
            'able': ['เอเบิล', 'เอ็บเบิล', 'เอเบิ้ล'],
            'ible': ['อิเบิล', 'อิ็บเบิล', 'อิเบิ้ล'],
            'ful': ['ฟูล', 'ฟูลล์', 'ฟูล'],
            'less': ['เลส', 'เลสส์', 'เลส'],
            'ness': ['เนส', 'เนสส์', 'เนส'],
            'ment': ['เมนต์', 'เมน', 'เมนท์'],
            'ance': ['แอนส์', 'แอนซ์', 'แอนส'],
            'ence': ['เอนส์', 'เอนซ์', 'เอนส'],
            'ous': ['อัส', 'อัสส์', 'อัส'],
            'ious': ['เอียส', 'เอียสส์', 'เอียส'],
            'eous': ['เอียส', 'เอียสส์', 'เอียส'],
            'ity': ['อิตี้', 'อิตี', 'อิตี้'],
            'ety': ['เอตี้', 'เอตี', 'เอตี้'],
            'ary': ['อารี่', 'อารี', 'อารี่'],
            'ery': ['เอรี่', 'เอรี', 'เอรี่'],
            'ory': ['ออรี่', 'ออรี', 'ออรี่'],
            'ify': ['อิฟาย', 'อิฟาย', 'อิฟาย'],
            'ize': ['ไอซ์', 'ไอซ', 'ไอซ์'],
            'ise': ['ไอส์', 'ไอส', 'ไอส์'],
            'ate': ['เอท', 'เอท', 'เอท'],
            'ite': ['ไอท์', 'ไอท', 'ไอท์'],
            'ute': ['ยูท', 'ยูท', 'ยูท'],
            'ote': ['โอท', 'โอท', 'โอท'],
            'ive': ['อิฟ', 'อิฟ', 'อิฟ'],
            'ave': ['เอฟ', 'เอฟ', 'เอฟ'],
            'ove': ['โอฟ', 'โอฟ', 'โอฟ'],
            'ove': ['อัฟ', 'อัฟ', 'อัฟ'],
            'age': ['เอจ', 'เอจ', 'เอจ'],
            'ege': ['เอจ', 'เอจ', 'เอจ'],
            'ige': ['ไอจ', 'ไอจ', 'ไอจ'],
            'oge': ['โอจ', 'โอจ', 'โอจ'],
            'uge': ['ยูจ', 'ยูจ', 'ยูจ'],
            'ck': ['ค', 'ก', 'k'],
            'sh': ['ช', 'ฉ', 'จ'],
            'zh': ['ซ', 'ส', 'ช'],
            'dj': ['จ', 'ช', 'ด'],
            'tj': ['ช', 'จ', 'ต'],
            'ds': ['ซ', 'ส', 'ด'],
            'ts': ['ส', 'ซ', 'ต'],
            'ps': ['ซ', 'ส', 'ป'],
            'bs': ['ซ', 'ส', 'บ'],
            'fs': ['ซ', 'ส', 'ฟ'],
            'vs': ['ซ', 'ส', 'ว'],
            'ws': ['ซ', 'ส', 'ว'],
            'ys': ['ซ', 'ส', 'ย'],
            'js': ['ซ', 'ส', 'จ'],
            'ks': ['ซ', 'ส', 'ค'],
            'gs': ['ซ', 'ส', 'ก'],
            'hs': ['ซ', 'ส', 'ห'],
            'ls': ['ซ', 'ส', 'ล'],
            'rs': ['ซ', 'ส', 'ร'],
            'ns': ['ซ', 'ส', 'น'],
            'ms': ['ซ', 'ส', 'ม'],
            'zs': ['ซ', 'ส', 'ซ'],
            'xs': ['ซ', 'ส', 'ก'],
            'cs': ['ซ', 'ส', 'ค'],
            'qs': ['ซ', 'ส', 'ค'],
            'sc': ['ซ', 'ส', 'ค'],
            'sk': ['ซ', 'ส', 'ค'],
            'sp': ['ซ', 'ส', 'ป'],
            'st': ['ซ', 'ส', 'ต'],
            'sw': ['ซ', 'ส', 'ว'],
            'sm': ['ซ', 'ส', 'ม'],
            'sn': ['ซ', 'ส', 'น'],
            'sl': ['ซ', 'ส', 'ล'],
            'sr': ['ซ', 'ส', 'ร'],
            'sf': ['ซ', 'ส', 'ฟ'],
            'sv': ['ซ', 'ส', 'ว'],
            'sy': ['ซ', 'ส', 'ย'],
            'sz': ['ซ', 'ส', 'ซ'],
            'sx': ['ซ', 'ส', 'ก'],
            'sq': ['ซ', 'ส', 'ค'],
            'sh': ['ซ', 'ส', 'ช'],
            'sg': ['ซ', 'ส', 'ก'],
            'sb': ['ซ', 'ส', 'บ'],
            'sd': ['ซ', 'ส', 'ด'],
            'sj': ['ซ', 'ส', 'จ'],
            'ss': ['ส', 'ซ', 'ซ'],
            'zz': ['ซ', 'ส', 'ซ'],
            'xx': ['ก', 'ซ', 'ค'],
            'cc': ['ค', 'ก', 'ซ'],
            'qq': ['ค', 'ก', 'ซ'],
            'kk': ['ค', 'ก', 'ค'],
            'gg': ['ก', 'ค', 'ก'],
            'tt': ['ต', 'ท', 'ต'],
            'dd': ['ด', 'ต', 'ด'],
            'pp': ['ป', 'พ', 'ป'],
            'bb': ['บ', 'ป', 'บ'],
            'ff': ['ฟ', 'พ', 'ฟ'],
            'vv': ['ว', 'ฟ', 'ว'],
            'ww': ['ว', 'ว', 'ว'],
            'yy': ['ย', 'ย', 'ย'],
            'jj': ['จ', 'ย', 'จ'],
            'hh': ['ห', 'ฮ', 'ห'],
            'll': ['ล', 'ร', 'ล'],
            'rr': ['ร', 'ล', 'ร'],
            'nn': ['น', 'ณ', 'น'],
            'mm': ['ม', 'น', 'ม'],
        }
        
    def match_products_progressive(
        self,
        product1: Dict[str, Any],
        product2: Dict[str, Any],
        category_hint: Optional[str] = None
    ) -> OptimizedMatchResult:
        """
        Progressive matching with multiple tiers for improved matching rates
        """
        category = category_hint or self._infer_category(product1, product2)
        
        # Try all tiers progressively
        best_result = None
        tier_results = {}
        
        for tier_name, tier_thresholds in self.progressive_tiers.items():
            result = self._match_with_tier(product1, product2, category, tier_name, tier_thresholds)
            tier_results[tier_name] = result
            
            if result.confidence > 0.3:  # Very low threshold for any match
                if best_result is None or result.confidence > best_result.confidence:
                    best_result = result
        
        # If no good match found, use fuzzy tier with boosting
        if best_result is None or best_result.confidence < 0.25:
            best_result = self._fuzzy_match_with_boosting(product1, product2, category)
        
        # Add progressive scoring details
        best_result.progressive_scores = {
            tier: result.confidence for tier, result in tier_results.items()
        }
        
        return best_result
    
    def _match_with_tier(
        self,
        product1: Dict[str, Any],
        product2: Dict[str, Any],
        category: str,
        tier_name: str,
        tier_thresholds: Dict[str, float]
    ) -> OptimizedMatchResult:
        """Match products with specific tier thresholds"""
        
        weights = self.weight_profiles.get(category, self.weight_profiles['general'])
        
        scores = {}
        linguistic_scores = {}
        matched_fields = []
        warnings = []
        
        # 1. SKU matching with tier-specific thresholds
        sku_score, sku_linguistic = self._match_sku_optimized(
            product1.get('sku', ''),
            product2.get('sku', ''),
            product1.get('name', ''),
            product2.get('name', ''),
            tier_thresholds['sku_similarity_min']
        )
        scores['sku'] = sku_score
        linguistic_scores['sku'] = sku_linguistic
        if sku_score > tier_thresholds['sku_similarity_min']:
            matched_fields.append('sku')
        
        # 2. Brand matching with tier-specific thresholds
        brand_score, brand_linguistic = self._match_brand_optimized(
            product1.get('brand', ''),
            product2.get('brand', ''),
            product1.get('name', ''),
            product2.get('name', ''),
            tier_thresholds['brand_similarity_min']
        )
        scores['brand'] = brand_score
        linguistic_scores['brand'] = brand_linguistic
        if brand_score > tier_thresholds['brand_similarity_min']:
            matched_fields.append('brand')
        
        # 3. Name matching with tier-specific thresholds
        name_score, name_linguistic = self._match_names_optimized(
            product1.get('name', ''),
            product2.get('name', ''),
            tier_thresholds['name_similarity_min']
        )
        scores['name'] = name_score
        linguistic_scores['name'] = name_linguistic
        if name_score > tier_thresholds['name_similarity_min']:
            matched_fields.append('name')
        
        # 4. Specification matching with tier-specific thresholds
        spec_score, spec_details = self._match_specifications_optimized(
            product1.get('specs', {}),
            product2.get('specs', {}),
            product1.get('name', ''),
            product2.get('name', ''),
            category,
            tier_thresholds['spec_similarity_min']
        )
        scores['specs'] = spec_score
        if spec_score > tier_thresholds['spec_similarity_min']:
            matched_fields.append('specifications')
        
        # 5. Category matching
        category_score = self._match_category(
            product1.get('category', ''),
            product2.get('category', '')
        )
        scores['category'] = category_score
        if category_score > 0.6:
            matched_fields.append('category')
        
        # Calculate weighted confidence
        base_confidence = sum(
            scores.get(field, 0) * weight
            for field, weight in weights.items()
        )
        
        # Apply confidence boosting
        confidence_boost = self._calculate_confidence_boost(
            scores, linguistic_scores, matched_fields
        )
        
        # Apply reduced penalties
        penalty_multiplier = self._calculate_reduced_penalties(
            product1, product2, scores, tier_thresholds
        )
        
        # Final confidence calculation
        final_confidence = min(1.0, (base_confidence + confidence_boost) * penalty_multiplier)
        
        # Determine match type
        match_type = self._determine_optimized_match_type(final_confidence, scores, tier_name)
        
        # Compile results
        details = {
            'tier': tier_name,
            'sku_score': scores['sku'],
            'brand_score': scores['brand'],
            'name_score': scores['name'],
            'spec_score': scores['specs'],
            'category_score': scores['category'],
            'base_confidence': base_confidence,
            'confidence_boost': confidence_boost,
            'penalty_multiplier': penalty_multiplier,
            'final_confidence': final_confidence,
            'spec_details': spec_details,
            'tier_thresholds': tier_thresholds
        }
        
        return OptimizedMatchResult(
            confidence=final_confidence,
            match_type=match_type,
            details=details,
            matched_fields=matched_fields,
            warnings=warnings,
            linguistic_scores=linguistic_scores,
            progressive_scores={}
        )
    
    def _match_sku_optimized(
        self,
        sku1: str,
        sku2: str,
        name1: str,
        name2: str,
        threshold: float
    ) -> Tuple[float, Dict[str, float]]:
        """Optimized SKU matching with multiple algorithms"""
        
        linguistic_scores = {}
        
        # Direct exact match
        if sku1 and sku2:
            sku1_norm = self.normalizer.normalize_sku(sku1)
            sku2_norm = self.normalizer.normalize_sku(sku2)
            
            if sku1_norm == sku2_norm:
                return 1.0, {'exact': 1.0}
            
            # Enhanced fuzzy matching
            fuzzy_score = self._calculate_enhanced_fuzzy_score(sku1_norm, sku2_norm)
            if fuzzy_score > threshold:
                linguistic_scores['fuzzy'] = fuzzy_score
                return fuzzy_score, linguistic_scores
            
            # Pattern-based matching
            pattern_score = self._match_sku_patterns(sku1_norm, sku2_norm)
            if pattern_score > threshold:
                linguistic_scores['pattern'] = pattern_score
                return pattern_score, linguistic_scores
        
        # Extract from names with better algorithm
        model1 = self._extract_model_from_name(name1)
        model2 = self._extract_model_from_name(name2)
        
        if model1 and model2:
            # Multi-algorithm model matching
            algorithms = [
                ('exact', self._exact_match),
                ('fuzzy', self._calculate_enhanced_fuzzy_score),
                ('phonetic', self._calculate_enhanced_phonetic_similarity),
                ('pattern', self._match_sku_patterns),
                ('semantic', self._semantic_model_match)
            ]
            
            for algo_name, algo_func in algorithms:
                if algo_name == 'exact':
                    score = 1.0 if algo_func(model1, model2) else 0.0
                else:
                    score = algo_func(model1, model2)
                
                if score > threshold:
                    linguistic_scores[algo_name] = score
                    return score * 0.9, linguistic_scores  # Slight penalty for extraction
        
        return 0.0, linguistic_scores
    
    def _match_brand_optimized(
        self,
        brand1: str,
        brand2: str,
        name1: str,
        name2: str,
        threshold: float
    ) -> Tuple[float, Dict[str, float]]:
        """Optimized brand matching with enhanced mapping"""
        
        linguistic_scores = {}
        
        # Extract brands if needed
        if not brand1:
            brand1 = self._extract_brand_from_name(name1)
        if not brand2:
            brand2 = self._extract_brand_from_name(name2)
        
        if not brand1 or not brand2:
            return 0.0, linguistic_scores
        
        # Normalize brands
        brand1_norm = self.normalizer.normalize(brand1)
        brand2_norm = self.normalizer.normalize(brand2)
        
        # Check enhanced brand mapping
        mapping_score = self._check_enhanced_brand_mapping(brand1, brand2)
        if mapping_score > threshold:
            linguistic_scores['mapping'] = mapping_score
            return mapping_score, linguistic_scores
        
        # Multiple matching algorithms
        algorithms = [
            ('exact', lambda x, y: 1.0 if x == y else 0.0),
            ('fuzzy', self._calculate_enhanced_fuzzy_score),
            ('phonetic', self._calculate_enhanced_phonetic_similarity),
            ('transliteration', self._check_enhanced_transliteration),
            ('abbreviation', self._check_abbreviation_match),
            ('levenshtein', self._calculate_levenshtein_similarity)
        ]
        
        best_score = 0.0
        best_algo = None
        
        for algo_name, algo_func in algorithms:
            score = algo_func(brand1_norm, brand2_norm)
            if score > best_score:
                best_score = score
                best_algo = algo_name
        
        if best_score > threshold:
            linguistic_scores[best_algo] = best_score
            return best_score, linguistic_scores
        
        return 0.0, linguistic_scores
    
    def _match_names_optimized(
        self,
        name1: str,
        name2: str,
        threshold: float
    ) -> Tuple[float, Dict[str, float]]:
        """Optimized name matching with multiple algorithms"""
        
        linguistic_scores = {}
        
        if not name1 or not name2:
            return 0.0, linguistic_scores
        
        # Normalize names
        norm1 = self.normalizer.normalize(name1)
        norm2 = self.normalizer.normalize(name2)
        
        # Extract tokens
        tokens1 = set(self.normalizer.extract_tokens(name1))
        tokens2 = set(self.normalizer.extract_tokens(name2))
        
        # Multiple matching algorithms with optimized weights
        algorithms = [
            ('token_weighted', 0.30, self._calculate_weighted_token_similarity),
            ('ngram_multi', 0.25, self._calculate_multi_ngram_similarity),
            ('sequence_lcs', 0.20, self._calculate_lcs_similarity),
            ('semantic_enhanced', 0.15, self._calculate_enhanced_semantic_similarity),
            ('phonetic_cross', 0.10, self._calculate_cross_phonetic_similarity)
        ]
        
        total_score = 0.0
        algorithm_scores = {}
        
        for algo_name, weight, algo_func in algorithms:
            if algo_name in ['token_weighted', 'semantic_enhanced']:
                score = algo_func(tokens1, tokens2)
            else:
                score = algo_func(norm1, norm2)
            
            algorithm_scores[algo_name] = score
            total_score += score * weight
        
        # Apply bonus for consistent high scores
        if sum(1 for score in algorithm_scores.values() if score > 0.7) >= 3:
            total_score *= 1.1  # 10% bonus
        
        linguistic_scores.update(algorithm_scores)
        
        return min(1.0, total_score), linguistic_scores
    
    def _match_specifications_optimized(
        self,
        specs1: Dict[str, Any],
        specs2: Dict[str, Any],
        name1: str,
        name2: str,
        category: str,
        threshold: float
    ) -> Tuple[float, Dict[str, Any]]:
        """Optimized specification matching with better tolerance"""
        
        # Extract specs from names if needed
        if not specs1:
            specs1 = self.normalizer.extract_specifications(name1)
        if not specs2:
            specs2 = self.normalizer.extract_specifications(name2)
        
        if not specs1 and not specs2:
            return 0.6, {}  # Neutral score when no specs available
        
        if not specs1 or not specs2:
            return 0.4, {}  # Slight penalty for missing specs
        
        matched_specs = {}
        total_score = 0.0
        spec_count = 0
        
        # Define critical specs with relaxed handling
        critical_specs = {
            'electronics': ['model', 'power', 'voltage'],
            'appliances': ['capacity', 'power', 'size'],
            'general': ['size', 'model']
        }
        
        category_critical = critical_specs.get(category, critical_specs['general'])
        
        # Enhanced specification matching
        all_specs = set(specs1.keys()).union(specs2.keys())
        
        for spec_name in all_specs:
            val1 = specs1.get(spec_name)
            val2 = specs2.get(spec_name)
            
            # Handle missing specifications more gracefully
            if val1 is None or val2 is None:
                # Don't penalize missing non-critical specs
                if spec_name not in category_critical:
                    continue
                else:
                    # Reduced penalty for missing critical specs
                    matched_specs[spec_name] = {
                        'match': False,
                        'score': 0.3,  # Partial credit
                        'values': [val1, val2],
                        'critical': True,
                        'missing': True
                    }
                    spec_count += 1
                    total_score += 0.3
                continue
            
            spec_count += 1
            is_critical = spec_name in category_critical
            
            # Numeric specifications with enhanced tolerance
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                tolerance = self._get_optimized_tolerance(spec_name, category, val1, val2)
                
                if val1 == val2:
                    score = 1.0
                else:
                    relative_diff = abs(val1 - val2) / max(val1, val2) if max(val1, val2) > 0 else 0
                    
                    if relative_diff <= tolerance:
                        score = 1.0 - (relative_diff / tolerance) * 0.5  # Reduced penalty
                    else:
                        # Graduated penalty instead of zero
                        score = max(0.0, 1.0 - (relative_diff / tolerance) * 0.3)
                
                total_score += score * (1.5 if is_critical else 1.0)
                matched_specs[spec_name] = {
                    'match': score > 0.5,
                    'score': score,
                    'values': [val1, val2],
                    'critical': is_critical,
                    'tolerance': tolerance,
                    'relative_diff': relative_diff if 'relative_diff' in locals() else 0
                }
            
            # String specifications with enhanced matching
            else:
                str_score = self._match_spec_strings_optimized(str(val1), str(val2))
                total_score += str_score * (1.5 if is_critical else 1.0)
                matched_specs[spec_name] = {
                    'match': str_score > 0.5,
                    'score': str_score,
                    'values': [val1, val2],
                    'critical': is_critical
                }
        
        # Calculate final score with reduced penalties
        if spec_count == 0:
            return 0.6, matched_specs
        
        weight_sum = sum(
            1.5 if spec_name in category_critical else 1.0
            for spec_name in matched_specs.keys()
        )
        
        final_score = total_score / weight_sum if weight_sum > 0 else 0.6
        
        # Apply less harsh penalties
        critical_failures = sum(
            1 for spec_name, spec_data in matched_specs.items()
            if spec_data['critical'] and spec_data['score'] < 0.3
        )
        
        if critical_failures > 0:
            penalty = 0.1 * critical_failures  # Reduced penalty
            final_score = max(0.2, final_score - penalty)  # Minimum floor
        
        return final_score, matched_specs
    
    def _calculate_confidence_boost(
        self,
        scores: Dict[str, float],
        linguistic_scores: Dict[str, Dict[str, float]],
        matched_fields: List[str]
    ) -> float:
        """Calculate confidence boost based on match quality"""
        
        boost = 0.0
        
        # Exact matches boost
        if scores.get('sku', 0) >= 0.95:
            boost += self.confidence_boosters['exact_sku_match']
        
        if scores.get('brand', 0) >= 0.95:
            boost += self.confidence_boosters['exact_brand_match']
        
        # Phonetic matches boost
        phonetic_matches = sum(
            1 for field_scores in linguistic_scores.values()
            for score_name, score in field_scores.items()
            if 'phonetic' in score_name and score > 0.8
        )
        if phonetic_matches > 0:
            boost += self.confidence_boosters['phonetic_match'] * min(phonetic_matches, 2)
        
        # Semantic matches boost
        semantic_matches = sum(
            1 for field_scores in linguistic_scores.values()
            for score_name, score in field_scores.items()
            if 'semantic' in score_name and score > 0.7
        )
        if semantic_matches > 0:
            boost += self.confidence_boosters['semantic_match'] * min(semantic_matches, 2)
        
        # Multiple field matches boost
        if len(matched_fields) >= 3:
            boost += self.confidence_boosters['cross_validation']
        
        return min(0.2, boost)  # Cap at 20% boost
    
    def _calculate_reduced_penalties(
        self,
        product1: Dict[str, Any],
        product2: Dict[str, Any],
        scores: Dict[str, float],
        tier_thresholds: Dict[str, float]
    ) -> float:
        """Calculate reduced penalties for better matching rates"""
        
        penalty_multiplier = 1.0
        
        # Price variance penalty (reduced)
        price1 = product1.get('price', 0)
        price2 = product2.get('price', 0)
        
        if price1 and price2:
            try:
                p1, p2 = float(price1), float(price2)
                if p1 > 0 and p2 > 0:
                    variance = abs(p1 - p2) / max(p1, p2)
                    max_variance = tier_thresholds.get('price_variance_max', 0.5)
                    
                    if variance > max_variance:
                        penalty = 1.0 - (variance - max_variance) * 0.3  # Reduced penalty
                        penalty_multiplier *= max(0.7, penalty)  # Minimum 70%
            except (ValueError, TypeError):
                penalty_multiplier *= 0.95  # Small penalty for invalid prices
        
        # Category mismatch penalty (reduced)
        if scores.get('category', 0) < 0.3:
            penalty_multiplier *= self.penalty_factors['category_mismatch']
        
        # Brand mismatch penalty (reduced)
        if scores.get('brand', 0) < 0.3:
            penalty_multiplier *= self.penalty_factors['brand_mismatch']
        
        return penalty_multiplier
    
    def _fuzzy_match_with_boosting(
        self,
        product1: Dict[str, Any],
        product2: Dict[str, Any],
        category: str
    ) -> OptimizedMatchResult:
        """Last resort fuzzy matching with aggressive boosting"""
        
        # Extract all comparable strings
        strings1 = self._extract_all_strings(product1)
        strings2 = self._extract_all_strings(product2)
        
        # Find best string matches
        best_matches = []
        for s1 in strings1:
            for s2 in strings2:
                if len(s1) > 3 and len(s2) > 3:  # Skip very short strings
                    score = self._calculate_enhanced_fuzzy_score(s1, s2)
                    if score > 0.3:
                        best_matches.append((s1, s2, score))
        
        # Calculate fuzzy confidence
        if best_matches:
            best_matches.sort(key=lambda x: x[2], reverse=True)
            fuzzy_confidence = sum(match[2] for match in best_matches[:3]) / 3
            
            # Apply aggressive boosting
            boosted_confidence = min(0.6, fuzzy_confidence * 1.5)
            
            match_type = self._determine_optimized_match_type(boosted_confidence, {}, 'fuzzy')
            
            return OptimizedMatchResult(
                confidence=boosted_confidence,
                match_type=match_type,
                details={
                    'fuzzy_matches': best_matches[:3],
                    'fuzzy_confidence': fuzzy_confidence,
                    'boosted_confidence': boosted_confidence,
                    'match_source': 'fuzzy_boosting'
                },
                matched_fields=['fuzzy_string_matches'],
                warnings=['Low confidence fuzzy match'],
                linguistic_scores={'fuzzy': {'best_score': best_matches[0][2] if best_matches else 0}},
                progressive_scores={}
            )
        
        # No matches found
        return OptimizedMatchResult(
            confidence=0.0,
            match_type='none',
            details={'match_source': 'no_match'},
            matched_fields=[],
            warnings=['No matches found'],
            linguistic_scores={},
            progressive_scores={}
        )
    
    # Helper methods for optimized matching
    def _extract_all_strings(self, product: Dict[str, Any]) -> List[str]:
        """Extract all meaningful strings from product"""
        strings = []
        
        # Add core fields
        for field in ['name', 'brand', 'sku', 'category', 'description']:
            value = product.get(field, '')
            if value and len(str(value)) > 2:
                strings.append(str(value))
        
        # Add specifications
        specs = product.get('specs', {})
        if isinstance(specs, dict):
            for spec_value in specs.values():
                if isinstance(spec_value, str) and len(spec_value) > 2:
                    strings.append(spec_value)
        
        # Normalize all strings
        return [self.normalizer.normalize(s) for s in strings]
    
    def _calculate_enhanced_fuzzy_score(self, s1: str, s2: str) -> float:
        """Enhanced fuzzy scoring with multiple algorithms"""
        if not s1 or not s2:
            return 0.0
        
        # Multiple similarity algorithms
        scores = [
            SequenceMatcher(None, s1.lower(), s2.lower()).ratio(),
            self._calculate_jaro_winkler(s1, s2),
            self._calculate_cosine_similarity(s1, s2),
            self._calculate_jaccard_similarity(s1, s2)
        ]
        
        # Remove None values and calculate weighted average
        valid_scores = [score for score in scores if score is not None]
        if not valid_scores:
            return 0.0
        
        # Weighted average (sequence matcher gets higher weight)
        weights = [0.4, 0.3, 0.2, 0.1][:len(valid_scores)]
        weighted_score = sum(score * weight for score, weight in zip(valid_scores, weights))
        
        return weighted_score
    
    def _calculate_jaro_winkler(self, s1: str, s2: str) -> float:
        """Calculate Jaro-Winkler similarity"""
        if not s1 or not s2:
            return 0.0
        
        # Simplified Jaro-Winkler implementation
        if s1 == s2:
            return 1.0
        
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Calculate matches
        match_distance = (max(len1, len2) // 2) - 1
        s1_matches = [False] * len1
        s2_matches = [False] * len2
        
        matches = 0
        transpositions = 0
        
        # Identify matches
        for i in range(len1):
            start = max(0, i - match_distance)
            end = min(i + match_distance + 1, len2)
            
            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break
        
        if matches == 0:
            return 0.0
        
        # Calculate transpositions
        k = 0
        for i in range(len1):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
        
        jaro = (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3
        
        # Winkler modification
        prefix = 0
        for i in range(min(len1, len2, 4)):
            if s1[i] == s2[i]:
                prefix += 1
            else:
                break
        
        return jaro + (0.1 * prefix * (1 - jaro))
    
    def _calculate_cosine_similarity(self, s1: str, s2: str) -> float:
        """Calculate cosine similarity of character n-grams"""
        if not s1 or not s2:
            return 0.0
        
        # Generate character bigrams
        def get_bigrams(text):
            return [text[i:i+2] for i in range(len(text) - 1)]
        
        bigrams1 = get_bigrams(s1.lower())
        bigrams2 = get_bigrams(s2.lower())
        
        if not bigrams1 or not bigrams2:
            return 0.0
        
        # Count occurrences
        count1 = Counter(bigrams1)
        count2 = Counter(bigrams2)
        
        # Calculate dot product
        dot_product = sum(count1[gram] * count2[gram] for gram in count1 if gram in count2)
        
        # Calculate magnitudes
        magnitude1 = sum(count * count for count in count1.values()) ** 0.5
        magnitude2 = sum(count * count for count in count2.values()) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _calculate_jaccard_similarity(self, s1: str, s2: str) -> float:
        """Calculate Jaccard similarity of character sets"""
        if not s1 or not s2:
            return 0.0
        
        set1 = set(s1.lower())
        set2 = set(s2.lower())
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _determine_optimized_match_type(
        self,
        confidence: float,
        scores: Dict[str, float],
        tier: str
    ) -> str:
        """Determine match type with optimized thresholds"""
        
        # Tier-specific adjustments
        tier_adjustments = {
            'strict': 0.0,
            'moderate': -0.05,
            'relaxed': -0.10,
            'fuzzy': -0.15
        }
        
        adjustment = tier_adjustments.get(tier, 0.0)
        
        # Apply adjusted thresholds
        for match_type, base_threshold in sorted(self.thresholds.items(), key=lambda x: -x[1]):
            adjusted_threshold = base_threshold + adjustment
            if confidence >= adjusted_threshold:
                return match_type
        
        return 'none'
    
    def find_best_matches_optimized(
        self,
        product: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        min_confidence: float = 0.25,  # Much lower threshold
        max_results: int = 10,
        category_hint: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], OptimizedMatchResult]]:
        """
        Find best matches with optimized algorithms for higher matching rates
        """
        matches = []
        
        for candidate in candidates:
            # Skip same product
            if product.get('id') == candidate.get('id'):
                continue
            
            # Skip same retailer unless allowed
            if product.get('retailer_code') == candidate.get('retailer_code'):
                continue
            
            result = self.match_products_progressive(product, candidate, category_hint)
            
            if result.confidence >= min_confidence:
                matches.append((candidate, result))
        
        # Sort by confidence
        matches.sort(key=lambda x: x[1].confidence, reverse=True)
        
        return matches[:max_results]
    
    # Additional helper methods (implement as needed)
    def _exact_match(self, s1: str, s2: str) -> bool:
        """Check exact string match"""
        return s1.lower() == s2.lower()
    
    def _extract_model_from_name(self, name: str) -> str:
        """Extract model number from product name"""
        # Enhanced model extraction patterns
        patterns = [
            r'[A-Z]{2,4}[-_]?[0-9]{2,6}[A-Z]*',  # Standard model pattern
            r'[0-9]{4,6}[A-Z]+',                  # Number followed by letters
            r'[A-Z]+[0-9]{3,5}',                  # Letters followed by numbers
            r'[A-Z]{1,2}[0-9]{2,4}[A-Z]{1,2}',   # Mixed pattern
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, name.upper())
            if matches:
                return matches[0]
        
        return ''
    
    def _extract_brand_from_name(self, name: str) -> str:
        """Extract brand from product name using enhanced mapping"""
        name_lower = name.lower()
        
        # Check against enhanced brand mapping
        for brand, variations in self.enhanced_brand_mapping.items():
            if brand in name_lower:
                return brand
            for variation in variations:
                if variation in name_lower:
                    return brand
        
        # Fallback to first word
        words = name.split()
        return words[0] if words else ''
    
    def _check_enhanced_brand_mapping(self, brand1: str, brand2: str) -> float:
        """Check brands against enhanced mapping"""
        brand1_lower = brand1.lower()
        brand2_lower = brand2.lower()
        
        # Direct mapping check
        for base_brand, variations in self.enhanced_brand_mapping.items():
            brand1_matches = brand1_lower == base_brand or brand1_lower in variations
            brand2_matches = brand2_lower == base_brand or brand2_lower in variations
            
            if brand1_matches and brand2_matches:
                return 1.0
        
        return 0.0
    
    def _calculate_enhanced_phonetic_similarity(self, s1: str, s2: str) -> float:
        """Enhanced phonetic similarity calculation"""
        if not s1 or not s2:
            return 0.0
        
        # Use enhanced phonetic patterns
        score = 0.0
        matches = 0
        
        for pattern, variations in self.phonetic_patterns.items():
            if pattern in s1.lower() or pattern in s2.lower():
                for variation in variations:
                    if variation in s1 or variation in s2:
                        matches += 1
                        break
        
        if matches > 0:
            score = min(1.0, matches / (min(len(s1), len(s2)) * 0.3))
        
        return score
    
    def _check_enhanced_transliteration(self, s1: str, s2: str) -> float:
        """Enhanced transliteration checking"""
        # More comprehensive transliteration variations
        variations = [
            ('ph', 'f'), ('th', 't'), ('ch', 'c'), ('kh', 'k'),
            ('ng', 'n'), ('ae', 'a'), ('ue', 'u'), ('oe', 'o'),
            ('ai', 'i'), ('ei', 'i'), ('ou', 'u'), ('au', 'o'),
            ('z', 's'), ('v', 'w'), ('x', 's'), ('q', 'k'),
            ('c', 'k'), ('j', 'y'), ('y', 'i'), ('w', 'v'),
            ('double_consonants', 'single')
        ]
        
        s1_lower = s1.lower()
        s2_lower = s2.lower()
        
        max_score = 0.0
        
        for var1, var2 in variations:
            if var1 == 'double_consonants':
                # Handle double consonants
                s1_variant = re.sub(r'([bcdfghjklmnpqrstvwxyz])\1+', r'\1', s1_lower)
                s2_variant = re.sub(r'([bcdfghjklmnpqrstvwxyz])\1+', r'\1', s2_lower)
            else:
                s1_variant = s1_lower.replace(var1, var2)
                s2_variant = s2_lower.replace(var1, var2)
            
            # Calculate similarity for this variant
            score = self._calculate_enhanced_fuzzy_score(s1_variant, s2_variant)
            max_score = max(max_score, score)
        
        return max_score
    
    def _check_abbreviation_match(self, s1: str, s2: str) -> float:
        """Check if one string is abbreviation of another"""
        if not s1 or not s2:
            return 0.0
        
        # Check if shorter string is abbreviation of longer
        short, long = (s1, s2) if len(s1) <= len(s2) else (s2, s1)
        
        if len(short) < 2 or len(long) < 4:
            return 0.0
        
        # Extract first letters of words from long string
        long_words = re.findall(r'\b\w+', long.lower())
        abbreviation = ''.join(word[0] for word in long_words)
        
        if short.lower() == abbreviation:
            return 0.9
        
        # Check partial match
        matches = sum(1 for i, char in enumerate(short.lower()) 
                     if i < len(abbreviation) and char == abbreviation[i])
        
        if matches >= len(short) * 0.8:
            return 0.7
        
        return 0.0
    
    def _calculate_levenshtein_similarity(self, s1: str, s2: str) -> float:
        """Calculate Levenshtein distance similarity"""
        if not s1 or not s2:
            return 0.0
        
        if s1 == s2:
            return 1.0
        
        len1, len2 = len(s1), len(s2)
        
        # Create matrix
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize first row and column
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if s1[i-1] == s2[j-1]:
                    cost = 0
                else:
                    cost = 1
                
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        distance = matrix[len1][len2]
        max_len = max(len1, len2)
        
        return 1.0 - (distance / max_len) if max_len > 0 else 0.0
    
    def _get_optimized_tolerance(self, spec_name: str, category: str, val1: float, val2: float) -> float:
        """Get optimized tolerance based on specification and values"""
        base_tolerance = self.spec_tolerances.get(spec_name, {}).get('default', 0.05)
        
        # Adjust tolerance based on value magnitude
        avg_val = (val1 + val2) / 2
        
        # Larger values can have larger absolute differences
        if avg_val > 1000:
            base_tolerance *= 1.5
        elif avg_val > 100:
            base_tolerance *= 1.2
        
        # Category-specific adjustments
        if category == 'general':
            base_tolerance *= 1.3  # More tolerant for general items
        elif category == 'appliances':
            base_tolerance *= 1.1  # Slightly more tolerant
        
        return base_tolerance
    
    def _match_spec_strings_optimized(self, s1: str, s2: str) -> float:
        """Optimized string specification matching"""
        if not s1 or not s2:
            return 0.0
        
        # Normalize specifications
        s1_norm = self.normalizer.normalize_specification(s1)
        s2_norm = self.normalizer.normalize_specification(s2)
        
        if s1_norm == s2_norm:
            return 1.0
        
        # Try multiple matching algorithms
        scores = [
            self._calculate_enhanced_fuzzy_score(s1_norm, s2_norm),
            self._calculate_enhanced_phonetic_similarity(s1_norm, s2_norm),
            self._check_enhanced_transliteration(s1_norm, s2_norm)
        ]
        
        return max(scores)
    
    def _match_sku_patterns(self, sku1: str, sku2: str) -> float:
        """Match SKU patterns with enhanced recognition"""
        pattern1 = self._extract_enhanced_sku_pattern(sku1)
        pattern2 = self._extract_enhanced_sku_pattern(sku2)
        
        if not pattern1 or not pattern2:
            return 0.0
        
        # Compare patterns
        matches = 0
        total = len(set(pattern1.keys()) | set(pattern2.keys()))
        
        for key in pattern1:
            if key in pattern2:
                if pattern1[key] == pattern2[key]:
                    matches += 1
                elif self._calculate_enhanced_fuzzy_score(pattern1[key], pattern2[key]) > 0.8:
                    matches += 0.8
        
        return matches / total if total > 0 else 0.0
    
    def _extract_enhanced_sku_pattern(self, sku: str) -> Dict[str, str]:
        """Extract enhanced SKU pattern components"""
        pattern = {}
        
        # Extract prefix (letters at start)
        prefix_match = re.match(r'^([A-Z]+)', sku.upper())
        if prefix_match:
            pattern['prefix'] = prefix_match.group(1)
        
        # Extract main numbers
        main_numbers = re.findall(r'\d+', sku)
        if main_numbers:
            pattern['main_numbers'] = '-'.join(main_numbers)
        
        # Extract suffix (letters at end)
        suffix_match = re.search(r'([A-Z]+)$', sku.upper())
        if suffix_match and suffix_match.group(1) != pattern.get('prefix'):
            pattern['suffix'] = suffix_match.group(1)
        
        # Extract special characters
        special_chars = re.findall(r'[^A-Za-z0-9]', sku)
        if special_chars:
            pattern['separators'] = ''.join(set(special_chars))
        
        return pattern
    
    def _semantic_model_match(self, model1: str, model2: str) -> float:
        """Semantic model matching based on common patterns"""
        # Extract semantic components
        components1 = self._extract_semantic_components(model1)
        components2 = self._extract_semantic_components(model2)
        
        if not components1 or not components2:
            return 0.0
        
        # Calculate component similarity
        matches = 0
        total = len(set(components1.keys()) | set(components2.keys()))
        
        for key in components1:
            if key in components2:
                if components1[key] == components2[key]:
                    matches += 1
                elif abs(float(components1[key]) - float(components2[key])) / max(float(components1[key]), float(components2[key])) < 0.1:
                    matches += 0.8
        
        return matches / total if total > 0 else 0.0
    
    def _extract_semantic_components(self, model: str) -> Dict[str, str]:
        """Extract semantic components from model"""
        components = {}
        
        # Extract capacity (BTU, tons, etc.)
        capacity_match = re.search(r'(\d+)\s*(btu|ton|hp|watt|w)', model.lower())
        if capacity_match:
            components['capacity'] = capacity_match.group(1)
            components['capacity_unit'] = capacity_match.group(2)
        
        # Extract voltage
        voltage_match = re.search(r'(\d+)\s*v', model.lower())
        if voltage_match:
            components['voltage'] = voltage_match.group(1)
        
        # Extract frequency
        freq_match = re.search(r'(\d+)\s*hz', model.lower())
        if freq_match:
            components['frequency'] = freq_match.group(1)
        
        # Extract series/generation
        series_match = re.search(r'(series|gen|generation)\s*(\d+)', model.lower())
        if series_match:
            components['series'] = series_match.group(2)
        
        return components
    
    def _calculate_weighted_token_similarity(self, tokens1: Set[str], tokens2: Set[str]) -> float:
        """Calculate weighted token similarity"""
        if not tokens1 or not tokens2:
            return 0.0
        
        # Weight important tokens
        important_words = {'inverter', 'smart', 'digital', 'premium', 'pro', 'plus', 'eco', 'energy', 'saving'}
        
        weighted_intersection = 0
        weighted_union = 0
        
        all_tokens = tokens1 | tokens2
        
        for token in all_tokens:
            weight = 2.0 if token in important_words else 1.0
            
            if token in tokens1 and token in tokens2:
                weighted_intersection += weight
            
            if token in tokens1 or token in tokens2:
                weighted_union += weight
        
        return weighted_intersection / weighted_union if weighted_union > 0 else 0.0
    
    def _calculate_multi_ngram_similarity(self, s1: str, s2: str) -> float:
        """Calculate multi-size n-gram similarity"""
        if not s1 or not s2:
            return 0.0
        
        scores = []
        
        for n in [2, 3, 4]:  # Different n-gram sizes
            ngrams1 = self._get_ngrams(s1, n)
            ngrams2 = self._get_ngrams(s2, n)
            
            if ngrams1 and ngrams2:
                intersection = len(ngrams1 & ngrams2)
                union = len(ngrams1 | ngrams2)
                scores.append(intersection / union if union > 0 else 0.0)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _get_ngrams(self, text: str, n: int) -> Set[str]:
        """Get n-grams from text"""
        if len(text) < n:
            return {text}
        return {text[i:i+n] for i in range(len(text) - n + 1)}
    
    def _calculate_lcs_similarity(self, s1: str, s2: str) -> float:
        """Calculate LCS-based similarity"""
        if not s1 or not s2:
            return 0.0
        
        # Convert to token sequences
        tokens1 = s1.split()
        tokens2 = s2.split()
        
        lcs_length = self._longest_common_subsequence(tokens1, tokens2)
        max_length = max(len(tokens1), len(tokens2))
        
        return lcs_length / max_length if max_length > 0 else 0.0
    
    def _longest_common_subsequence(self, seq1: List[str], seq2: List[str]) -> int:
        """Find longest common subsequence length"""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i-1] == seq2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def _calculate_enhanced_semantic_similarity(self, tokens1: Set[str], tokens2: Set[str]) -> float:
        """Enhanced semantic similarity calculation"""
        if not tokens1 or not tokens2:
            return 0.0
        
        # Enhanced semantic groups
        semantic_groups = {
            'cooling': {'air', 'conditioner', 'ac', 'cooling', 'แอร์', 'เครื่องปรับอากาศ', 'cool', 'cold'},
            'heating': {'heat', 'heating', 'heater', 'warm', 'hot', 'เครื่องทำความร้อน', 'ฮีตเตอร์'},
            'inverter': {'inverter', 'อินเวอร์เตอร์', 'อินเวอเตอร์', 'ประหยัดไฟ', 'energy', 'saving', 'efficient'},
            'smart': {'smart', 'สมาร์ท', 'wifi', 'iot', 'app', 'digital', 'intelligent', 'auto'},
            'capacity': {'btu', 'ton', 'hp', 'บีทียู', 'ตัน', 'แรงม้า', 'watt', 'kilowatt', 'power'},
            'premium': {'premium', 'pro', 'plus', 'advanced', 'พรีเมียม', 'โปร', 'deluxe', 'luxury'},
            'eco': {'eco', 'green', 'environment', 'ประหยัด', 'เป็นมิตรกับสิ่งแวดล้อม', 'ecological'},
            'quiet': {'quiet', 'silent', 'low', 'noise', 'เงียบ', 'เสียงเบา', 'whisper'},
            'fast': {'fast', 'quick', 'rapid', 'speed', 'เร็ว', 'รวดเร็ว', 'ไว', 'turbo'},
            'compact': {'compact', 'small', 'mini', 'portable', 'เล็ก', 'พกพา', 'ขนาดเล็ก'}
        }
        
        # Find semantic matches
        groups1 = set()
        groups2 = set()
        
        for group, keywords in semantic_groups.items():
            if any(token in keywords for token in tokens1):
                groups1.add(group)
            if any(token in keywords for token in tokens2):
                groups2.add(group)
        
        if not groups1 and not groups2:
            return 0.5  # Neutral when no semantic info
        
        if groups1 and groups2:
            intersection = len(groups1 & groups2)
            union = len(groups1 | groups2)
            return intersection / union if union > 0 else 0.0
        
        return 0.0
    
    def _calculate_cross_phonetic_similarity(self, s1: str, s2: str) -> float:
        """Calculate cross-language phonetic similarity"""
        # Check if different languages
        is_thai1 = self.normalizer.is_thai_text(s1)
        is_thai2 = self.normalizer.is_thai_text(s2)
        
        if is_thai1 == is_thai2:
            return 0.0  # Same language, no cross-phonetic bonus
        
        # Apply enhanced phonetic matching
        return self._calculate_enhanced_phonetic_similarity(s1, s2)
    
    def _infer_category(self, product1: Dict[str, Any], product2: Dict[str, Any]) -> str:
        """Infer category from product data"""
        # Check explicit categories
        cat1 = product1.get('category', '').lower()
        cat2 = product2.get('category', '').lower()
        
        # Enhanced category keywords
        category_keywords = {
            'electronics': [
                'air conditioner', 'แอร์', 'tv', 'television', 'refrigerator', 'ตู้เย็น',
                'washer', 'washing machine', 'เครื่องซักผ้า', 'computer', 'คอมพิวเตอร์',
                'smartphone', 'tablet', 'laptop', 'monitor', 'speaker', 'headphone',
                'camera', 'projector', 'printer', 'scanner', 'router', 'modem'
            ],
            'appliances': [
                'kitchen', 'ครัว', 'home', 'บ้าน', 'appliance', 'เครื่องใช้',
                'microwave', 'oven', 'stove', 'dishwasher', 'vacuum', 'iron',
                'blender', 'mixer', 'toaster', 'coffee maker', 'rice cooker',
                'water heater', 'fan', 'humidifier', 'dehumidifier'
            ],
            'tools': [
                'drill', 'saw', 'hammer', 'screwdriver', 'wrench', 'pliers',
                'tool', 'เครื่องมือ', 'workshop', 'repair', 'maintenance',
                'electric tool', 'power tool', 'hand tool', 'construction'
            ]
        }
        
        all_text = ' '.join([
            cat1, cat2,
            product1.get('name', '').lower(),
            product2.get('name', '').lower(),
            product1.get('description', '').lower(),
            product2.get('description', '').lower()
        ])
        
        # Find best category match
        best_category = 'general'
        best_score = 0
        
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in all_text)
            if score > best_score:
                best_score = score
                best_category = category
        
        return best_category
    
    def _match_category(self, cat1: str, cat2: str) -> float:
        """Enhanced category matching"""
        if not cat1 or not cat2:
            return 0.5  # Neutral when missing
        
        # Normalize categories
        cat1_norm = self.normalizer.normalize(cat1)
        cat2_norm = self.normalizer.normalize(cat2)
        
        if cat1_norm == cat2_norm:
            return 1.0
        
        # Check if one is subcategory of another
        if cat1_norm in cat2_norm or cat2_norm in cat1_norm:
            return 0.8
        
        # Token-based similarity
        tokens1 = set(self.normalizer.extract_tokens(cat1))
        tokens2 = set(self.normalizer.extract_tokens(cat2))
        
        if tokens1 and tokens2:
            intersection = len(tokens1 & tokens2)
            union = len(tokens1 | tokens2)
            return intersection / union if union > 0 else 0.0
        
        return 0.0