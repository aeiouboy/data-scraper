"""
Database Query Optimization Service
Optimizes database queries for product matching operations
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import json
import hashlib
from functools import wraps

from src.services.supabase_service import SupabaseService as SupabaseClient

logger = logging.getLogger(__name__)


@dataclass
class QueryOptimization:
    """Database query optimization recommendation"""
    table_name: str
    optimization_type: str  # 'index', 'query_rewrite', 'batch_operation', 'caching'
    description: str
    sql_statement: Optional[str]
    expected_improvement: str
    priority: str  # 'low', 'medium', 'high', 'critical'
    estimated_impact: float  # 0-100


@dataclass
class QueryPerformance:
    """Query performance metrics"""
    query_hash: str
    execution_time: float
    rows_affected: int
    timestamp: datetime
    query_type: str
    table_name: str


class DatabaseOptimizer:
    """Optimizes database operations for product matching"""
    
    def __init__(self, db_client: Optional[SupabaseClient] = None):
        """Initialize database optimizer"""
        self.db = db_client or SupabaseClient()
        self.query_cache = {}
        self.query_performance = defaultdict(list)
        self.optimization_rules = self._load_optimization_rules()
        
        # Query patterns for optimization
        self.common_queries = {
            'product_search_by_name': {
                'pattern': "SELECT * FROM products WHERE name ILIKE %s",
                'optimization': 'gin_index_on_name',
                'table': 'products'
            },
            'product_search_by_brand': {
                'pattern': "SELECT * FROM products WHERE brand = %s",
                'optimization': 'btree_index_on_brand',
                'table': 'products'
            },
            'product_search_by_category': {
                'pattern': "SELECT * FROM products WHERE category = %s",
                'optimization': 'btree_index_on_category',
                'table': 'products'
            },
            'product_matches_by_confidence': {
                'pattern': "SELECT * FROM product_matches WHERE confidence >= %s",
                'optimization': 'btree_index_on_confidence',
                'table': 'product_matches'
            },
            'recent_products': {
                'pattern': "SELECT * FROM products WHERE created_at >= %s",
                'optimization': 'btree_index_on_created_at',
                'table': 'products'
            }
        }
        
        # Index recommendations
        self.recommended_indexes = [
            {
                'table': 'products',
                'index_name': 'idx_products_name_gin',
                'columns': ['name'],
                'type': 'GIN',
                'sql': "CREATE INDEX CONCURRENTLY idx_products_name_gin ON products USING gin(name gin_trgm_ops);",
                'purpose': 'Fast text search on product names',
                'estimated_improvement': '70-90% faster text searches'
            },
            {
                'table': 'products',
                'index_name': 'idx_products_brand_category',
                'columns': ['brand', 'category'],
                'type': 'BTREE',
                'sql': "CREATE INDEX CONCURRENTLY idx_products_brand_category ON products (brand, category);",
                'purpose': 'Fast filtering by brand and category combination',
                'estimated_improvement': '60-80% faster brand/category queries'
            },
            {
                'table': 'products',
                'index_name': 'idx_products_retailer_created',
                'columns': ['retailer', 'created_at'],
                'type': 'BTREE',
                'sql': "CREATE INDEX CONCURRENTLY idx_products_retailer_created ON products (retailer, created_at);",
                'purpose': 'Fast queries for recent products by retailer',
                'estimated_improvement': '50-70% faster retailer-specific queries'
            },
            {
                'table': 'product_matches',
                'index_name': 'idx_matches_confidence_status',
                'columns': ['confidence', 'match_status'],
                'type': 'BTREE',
                'sql': "CREATE INDEX CONCURRENTLY idx_matches_confidence_status ON product_matches (confidence, match_status);",
                'purpose': 'Fast filtering of matches by confidence and status',
                'estimated_improvement': '40-60% faster match queries'
            },
            {
                'table': 'product_matches',
                'index_name': 'idx_matches_product_ids',
                'columns': ['product1_id', 'product2_id'],
                'type': 'BTREE',
                'sql': "CREATE INDEX CONCURRENTLY idx_matches_product_ids ON product_matches (product1_id, product2_id);",
                'purpose': 'Fast lookup of specific product matches',
                'estimated_improvement': '80-95% faster specific match lookups'
            },
            {
                'table': 'scrape_jobs',
                'index_name': 'idx_scrape_jobs_status_created',
                'columns': ['status', 'created_at'],
                'type': 'BTREE',
                'sql': "CREATE INDEX CONCURRENTLY idx_scrape_jobs_status_created ON scrape_jobs (status, created_at);",
                'purpose': 'Fast monitoring of scraping job status',
                'estimated_improvement': '50-70% faster job monitoring queries'
            }
        ]
    
    def _load_optimization_rules(self) -> Dict[str, Any]:
        """Load database optimization rules"""
        return {
            'max_query_time': 1.0,  # seconds
            'max_rows_without_index': 10000,
            'min_cache_hit_rate': 0.8,
            'max_connection_pool_size': 20,
            'query_timeout': 30.0,  # seconds
            'batch_size_threshold': 100,
            'index_usage_threshold': 0.1  # 10% of queries should benefit
        }
    
    def monitor_query(self, query_type: str, table_name: str = None):
        """Decorator to monitor query performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.perf_counter() - start_time
                    
                    # Record performance
                    self._record_query_performance(
                        query_type=query_type,
                        table_name=table_name or 'unknown',
                        execution_time=execution_time,
                        rows_affected=self._count_result_rows(result)
                    )
                    
                    # Check for optimization opportunities
                    if execution_time > self.optimization_rules['max_query_time']:
                        logger.warning(f"Slow query detected: {query_type} took {execution_time:.3f}s")
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.perf_counter() - start_time
                    logger.error(f"Query failed: {query_type} after {execution_time:.3f}s - {e}")
                    raise
            
            return wrapper
        return decorator
    
    def _record_query_performance(self, query_type: str, table_name: str, 
                                 execution_time: float, rows_affected: int):
        """Record query performance metrics"""
        query_hash = hashlib.md5(f"{query_type}_{table_name}".encode()).hexdigest()
        
        performance = QueryPerformance(
            query_hash=query_hash,
            execution_time=execution_time,
            rows_affected=rows_affected,
            timestamp=datetime.now(),
            query_type=query_type,
            table_name=table_name
        )
        
        self.query_performance[query_hash].append(performance)
        
        # Keep only recent performance data (last 1000 queries per type)
        if len(self.query_performance[query_hash]) > 1000:
            self.query_performance[query_hash] = self.query_performance[query_hash][-1000:]
    
    def _count_result_rows(self, result) -> int:
        """Count rows in query result"""
        try:
            if hasattr(result, 'data') and isinstance(result.data, list):
                return len(result.data)
            elif isinstance(result, list):
                return len(result)
            elif hasattr(result, '__len__'):
                return len(result)
            else:
                return 1
        except:
            return 0
    
    def get_optimized_product_query(self, filters: Dict[str, Any], 
                                   limit: int = None, offset: int = None) -> Dict[str, Any]:
        """Get optimized query for product search"""
        query_builder = self.db.client.table('products')
        
        # Apply filters efficiently
        if 'name' in filters:
            # Use text search for name queries
            name_query = filters['name']
            if len(name_query) > 3:  # Use full-text search for longer queries
                query_builder = query_builder.textSearch('name', name_query)
            else:
                query_builder = query_builder.ilike('name', f'%{name_query}%')
        
        if 'brand' in filters:
            query_builder = query_builder.eq('brand', filters['brand'])
        
        if 'category' in filters:
            query_builder = query_builder.eq('category', filters['category'])
        
        if 'retailer' in filters:
            query_builder = query_builder.eq('retailer', filters['retailer'])
        
        if 'price_min' in filters:
            query_builder = query_builder.gte('price', filters['price_min'])
        
        if 'price_max' in filters:
            query_builder = query_builder.lte('price', filters['price_max'])
        
        if 'created_after' in filters:
            query_builder = query_builder.gte('created_at', filters['created_after'])
        
        # Apply pagination
        if limit:
            query_builder = query_builder.limit(limit)
        
        if offset:
            query_builder = query_builder.offset(offset)
        
        # Order for consistent results
        query_builder = query_builder.order('created_at', desc=True)
        
        return query_builder
    
    def get_optimized_matches_query(self, product_id: str = None, 
                                   min_confidence: float = None,
                                   match_status: str = None) -> Dict[str, Any]:
        """Get optimized query for product matches"""
        query_builder = self.db.client.table('product_matches')
        
        if product_id:
            # Use OR condition for product matching
            query_builder = query_builder.or_(
                f'product1_id.eq.{product_id},product2_id.eq.{product_id}'
            )
        
        if min_confidence is not None:
            query_builder = query_builder.gte('confidence', min_confidence)
        
        if match_status:
            query_builder = query_builder.eq('match_status', match_status)
        
        # Order by confidence descending
        query_builder = query_builder.order('confidence', desc=True)
        
        return query_builder
    
    def batch_insert_products(self, products: List[Dict[str, Any]], 
                             batch_size: int = 1000) -> List[Any]:
        """Optimized batch insert for products"""
        results = []
        
        # Split into batches
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            
            try:
                # Use upsert for better performance with conflicts
                result = self.db.client.table('products').upsert(
                    batch,
                    on_conflict='id'  # Assuming id is the primary key
                ).execute()
                
                results.extend(result.data if result.data else [])
                
                logger.info(f"Batch inserted {len(batch)} products (batch {i//batch_size + 1})")
                
            except Exception as e:
                logger.error(f"Batch insert failed for batch {i//batch_size + 1}: {e}")
                
                # Fall back to individual inserts for failed batch
                for product in batch:
                    try:
                        single_result = self.db.client.table('products').insert(product).execute()
                        if single_result.data:
                            results.extend(single_result.data)
                    except Exception as single_error:
                        logger.error(f"Failed to insert single product {product.get('id', 'unknown')}: {single_error}")
        
        return results
    
    def batch_update_matches(self, matches: List[Dict[str, Any]], 
                            batch_size: int = 500) -> List[Any]:
        """Optimized batch update for product matches"""
        results = []
        
        for i in range(0, len(matches), batch_size):
            batch = matches[i:i + batch_size]
            
            try:
                result = self.db.client.table('product_matches').upsert(
                    batch,
                    on_conflict='product1_id,product2_id'
                ).execute()
                
                results.extend(result.data if result.data else [])
                
                logger.info(f"Batch updated {len(batch)} matches")
                
            except Exception as e:
                logger.error(f"Batch update failed: {e}")
        
        return results
    
    def analyze_query_performance(self) -> List[QueryOptimization]:
        """Analyze query performance and suggest optimizations"""
        optimizations = []
        
        for query_hash, performances in self.query_performance.items():
            if not performances:
                continue
            
            # Calculate statistics
            recent_performances = performances[-100:]  # Last 100 executions
            avg_time = sum(p.execution_time for p in recent_performances) / len(recent_performances)
            max_time = max(p.execution_time for p in recent_performances)
            
            # Check if optimization is needed
            if avg_time > self.optimization_rules['max_query_time']:
                optimization = self._suggest_query_optimization(recent_performances[0], avg_time, max_time)
                if optimization:
                    optimizations.append(optimization)
        
        # Add index recommendations
        optimizations.extend(self._suggest_index_optimizations())
        
        # Sort by priority and impact
        optimizations.sort(key=lambda x: (
            {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[x.priority],
            x.estimated_impact
        ), reverse=True)
        
        return optimizations
    
    def _suggest_query_optimization(self, sample_performance: QueryPerformance, 
                                   avg_time: float, max_time: float) -> Optional[QueryOptimization]:
        """Suggest optimization for specific query"""
        query_type = sample_performance.query_type
        table_name = sample_performance.table_name
        
        # Determine optimization type and priority
        if max_time > 5.0:
            priority = 'critical'
        elif avg_time > 2.0:
            priority = 'high'
        elif avg_time > 1.0:
            priority = 'medium'
        else:
            priority = 'low'
        
        # Generate optimization recommendations
        optimizations = {
            'product_search': {
                'type': 'index',
                'description': f'Add GIN index for text search on {table_name}',
                'sql': f"CREATE INDEX CONCURRENTLY idx_{table_name}_name_gin ON {table_name} USING gin(name gin_trgm_ops);",
                'improvement': f'Expected 70-90% improvement (currently {avg_time:.3f}s avg)'
            },
            'product_filter': {
                'type': 'index',
                'description': f'Add composite index for filtering on {table_name}',
                'sql': f"CREATE INDEX CONCURRENTLY idx_{table_name}_filter ON {table_name} (brand, category, retailer);",
                'improvement': f'Expected 50-70% improvement (currently {avg_time:.3f}s avg)'
            },
            'match_lookup': {
                'type': 'query_rewrite',
                'description': 'Optimize match lookup query structure',
                'sql': None,
                'improvement': f'Expected 40-60% improvement through query optimization'
            }
        }
        
        # Map query types to optimizations
        optimization_mapping = {
            'product_search_by_name': 'product_search',
            'product_search_by_brand': 'product_filter',
            'product_search_by_category': 'product_filter',
            'product_matches_lookup': 'match_lookup'
        }
        
        opt_key = optimization_mapping.get(query_type, 'product_filter')
        opt_config = optimizations[opt_key]
        
        return QueryOptimization(
            table_name=table_name,
            optimization_type=opt_config['type'],
            description=opt_config['description'],
            sql_statement=opt_config['sql'],
            expected_improvement=opt_config['improvement'],
            priority=priority,
            estimated_impact=min(100.0, (avg_time / 0.1) * 10)  # Scale impact based on slowness
        )
    
    def _suggest_index_optimizations(self) -> List[QueryOptimization]:
        """Suggest database index optimizations"""
        optimizations = []
        
        for index_config in self.recommended_indexes:
            # Check if index might already exist (simplified check)
            if not self._index_likely_exists(index_config['table'], index_config['columns']):
                optimization = QueryOptimization(
                    table_name=index_config['table'],
                    optimization_type='index',
                    description=index_config['purpose'],
                    sql_statement=index_config['sql'],
                    expected_improvement=index_config['estimated_improvement'],
                    priority='high' if 'gin' in index_config['sql'].lower() else 'medium',
                    estimated_impact=75.0 if 'gin' in index_config['sql'].lower() else 50.0
                )
                optimizations.append(optimization)
        
        return optimizations
    
    def _index_likely_exists(self, table: str, columns: List[str]) -> bool:
        """Simple heuristic to check if index might exist"""
        # This is a simplified check - in production, you'd query the database schema
        # For now, assume indexes don't exist
        return False
    
    def implement_optimization(self, optimization: QueryOptimization) -> bool:
        """Implement a database optimization"""
        if optimization.optimization_type == 'index' and optimization.sql_statement:
            return self._create_index(optimization.sql_statement)
        elif optimization.optimization_type == 'query_rewrite':
            logger.info(f"Query rewrite optimization noted for {optimization.table_name}")
            return True
        elif optimization.optimization_type == 'batch_operation':
            logger.info(f"Batch operation optimization noted for {optimization.table_name}")
            return True
        else:
            logger.warning(f"Unknown optimization type: {optimization.optimization_type}")
            return False
    
    def _create_index(self, sql_statement: str) -> bool:
        """Create database index"""
        try:
            # Note: Supabase doesn't directly support DDL through the client
            # This would typically be done through the Supabase dashboard or SQL editor
            logger.info(f"Index creation SQL generated: {sql_statement}")
            logger.info("Please execute this SQL in your Supabase dashboard:")
            logger.info(f"  {sql_statement}")
            
            # In a real implementation, you might use a direct database connection
            # or store these for batch execution by a DBA
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        optimizations = self.analyze_query_performance()
        
        # Calculate statistics
        total_queries = sum(len(perfs) for perfs in self.query_performance.values())
        avg_query_time = 0
        slow_queries = 0
        
        if total_queries > 0:
            all_times = []
            for perfs in self.query_performance.values():
                for perf in perfs[-100:]:  # Recent performances
                    all_times.append(perf.execution_time)
                    if perf.execution_time > self.optimization_rules['max_query_time']:
                        slow_queries += 1
            
            if all_times:
                avg_query_time = sum(all_times) / len(all_times)
        
        # Categorize optimizations
        critical_opts = [o for o in optimizations if o.priority == 'critical']
        high_opts = [o for o in optimizations if o.priority == 'high']
        medium_opts = [o for o in optimizations if o.priority == 'medium']
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'performance_summary': {
                'total_queries_analyzed': total_queries,
                'average_query_time': avg_query_time,
                'slow_queries_count': slow_queries,
                'slow_queries_percentage': (slow_queries / max(total_queries, 1)) * 100
            },
            'optimizations': {
                'total_recommendations': len(optimizations),
                'critical_priority': len(critical_opts),
                'high_priority': len(high_opts),
                'medium_priority': len(medium_opts),
                'estimated_total_impact': sum(o.estimated_impact for o in optimizations)
            },
            'top_recommendations': [
                {
                    'table': opt.table_name,
                    'type': opt.optimization_type,
                    'description': opt.description,
                    'priority': opt.priority,
                    'impact': opt.estimated_impact,
                    'sql': opt.sql_statement
                }
                for opt in optimizations[:5]  # Top 5 recommendations
            ],
            'index_recommendations': [
                opt for opt in optimizations 
                if opt.optimization_type == 'index'
            ][:3]  # Top 3 index recommendations
        }
        
        return report
    
    def clear_performance_data(self):
        """Clear collected performance data"""
        self.query_performance.clear()
        logger.info("Performance data cleared")


# Example usage and testing
if __name__ == "__main__":
    # Test database optimizer
    optimizer = DatabaseOptimizer()
    
    print("🗄️  Database Optimization Demo")
    print("=" * 50)
    
    # Simulate some query performance data
    import random
    
    for i in range(50):
        # Simulate various query types with different performance characteristics
        query_types = ['product_search_by_name', 'product_search_by_brand', 'product_matches_lookup']
        tables = ['products', 'product_matches']
        
        for query_type in query_types:
            execution_time = random.uniform(0.01, 2.0)  # Random execution time
            rows_affected = random.randint(1, 1000)
            table_name = random.choice(tables)
            
            optimizer._record_query_performance(
                query_type=query_type,
                table_name=table_name,
                execution_time=execution_time,
                rows_affected=rows_affected
            )
    
    # Analyze performance and get recommendations
    optimizations = optimizer.analyze_query_performance()
    
    print(f"Query Performance Analysis:")
    print(f"  Total optimization recommendations: {len(optimizations)}")
    
    if optimizations:
        print(f"\nTop 3 Recommendations:")
        for i, opt in enumerate(optimizations[:3], 1):
            print(f"  {i}. {opt.description}")
            print(f"     Priority: {opt.priority}")
            print(f"     Impact: {opt.estimated_impact:.1f}")
            if opt.sql_statement:
                print(f"     SQL: {opt.sql_statement[:80]}...")
            print()
    
    # Generate full optimization report
    report = optimizer.get_optimization_report()
    
    print(f"Optimization Report Summary:")
    print(f"  Queries analyzed: {report['performance_summary']['total_queries_analyzed']}")
    print(f"  Average query time: {report['performance_summary']['average_query_time']:.4f}s")
    print(f"  Slow queries: {report['performance_summary']['slow_queries_count']}")
    print(f"  Total recommendations: {report['optimizations']['total_recommendations']}")
    print(f"  Critical priority: {report['optimizations']['critical_priority']}")
    print(f"  High priority: {report['optimizations']['high_priority']}")
    
    print("\n✅ Database optimization demo completed")