#!/usr/bin/env python3
"""
Phase 3 Performance Optimization Integration Tests
Tests all optimization components working together
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add src to Python path
project_root = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_performance_analyzer():
    """Test performance analysis functionality"""
    print("🔍 Testing Performance Analyzer...")
    
    try:
        from src.services.performance_analyzer import PerformanceAnalyzer
        
        analyzer = PerformanceAnalyzer()
        
        # Start monitoring
        analyzer.start_monitoring()
        
        # Simulate some operations for benchmarking
        def test_operation(iterations=100):
            """Test operation for benchmarking"""
            result = 0
            for i in range(iterations):
                result += i * i
            return result
        
        # Benchmark the operation
        stats = analyzer.benchmark_component(
            "test_operation",
            test_operation,
            iterations=20
        )
        
        print(f"  ✅ Benchmark completed:")
        print(f"    Mean time: {stats['mean_time']:.4f}s")
        print(f"    P95 time: {stats['p95_time']:.4f}s")
        print(f"    Memory usage: {stats['mean_memory']:.2f}MB")
        
        # Let it collect some data
        time.sleep(2)
        
        # Generate performance report
        report = analyzer.generate_performance_report()
        
        print(f"  ✅ Performance report generated:")
        print(f"    Overall score: {report.overall_score:.1f}/100")
        print(f"    Bottlenecks found: {len(report.bottlenecks)}")
        print(f"    Recommendations: {len(report.recommendations)}")
        
        # Stop monitoring
        analyzer.stop_monitoring()
        
        # Verify report structure
        assert hasattr(report, 'overall_score')
        assert hasattr(report, 'bottlenecks')
        assert hasattr(report, 'recommendations')
        assert 0 <= report.overall_score <= 100
        
        print("  ✅ Performance Analyzer: PASSED")
        return True
        
    except Exception as e:
        print(f"  ❌ Performance Analyzer: FAILED - {e}")
        return False

def test_database_optimizer():
    """Test database optimization functionality"""
    print("\n🗄️  Testing Database Optimizer...")
    
    try:
        from src.services.database_optimizer import DatabaseOptimizer
        
        # Mock database client for testing
        class MockSupabaseClient:
            def __init__(self):
                self.client = self
                
            def table(self, table_name):
                return self
                
            def upsert(self, data, **kwargs):
                return self
                
            def insert(self, data):
                return self
                
            def execute(self):
                return type('MockResult', (), {'data': [{'id': f'test_{i}'} for i in range(len(data) if 'data' in locals() else 10)]})()
        
        optimizer = DatabaseOptimizer(MockSupabaseClient())
        
        # Simulate some query performance data
        for i in range(20):
            execution_time = 0.1 + (i * 0.01)  # Gradually increasing time
            optimizer._record_query_performance(
                query_type='product_search_by_name',
                table_name='products',
                execution_time=execution_time,
                rows_affected=100 + i
            )
        
        # Analyze performance
        optimizations = optimizer.analyze_query_performance()
        
        print(f"  ✅ Query analysis completed:")
        print(f"    Optimizations found: {len(optimizations)}")
        
        if optimizations:
            top_opt = optimizations[0]
            print(f"    Top optimization: {top_opt.description}")
            print(f"    Priority: {top_opt.priority}")
            print(f"    Impact: {top_opt.estimated_impact:.1f}")
        
        # Test batch operations
        test_products = [
            {'id': f'test_product_{i}', 'name': f'Test Product {i}', 'price': 100 + i}
            for i in range(10)
        ]
        
        batch_results = optimizer.batch_insert_products(test_products, batch_size=5)
        
        print(f"  ✅ Batch insert test:")
        print(f"    Processed: {len(batch_results)} products")
        
        # Generate optimization report
        report = optimizer.get_optimization_report()
        
        print(f"  ✅ Optimization report:")
        print(f"    Total queries: {report['performance_summary']['total_queries_analyzed']}")
        print(f"    Recommendations: {report['optimizations']['total_recommendations']}")
        
        # Verify results
        assert isinstance(optimizations, list)
        assert isinstance(report, dict)
        assert 'performance_summary' in report
        assert 'optimizations' in report
        
        print("  ✅ Database Optimizer: PASSED")
        return True
        
    except Exception as e:
        print(f"  ❌ Database Optimizer: FAILED - {e}")
        return False

def test_cache_manager():
    """Test caching functionality"""
    print("\n💾 Testing Cache Manager...")
    
    try:
        from src.services.cache_manager import CacheManager
        
        cache_manager = CacheManager()
        
        # Test caching decorator
        @cache_manager.cache_function('test_category')
        def expensive_operation(x: int) -> int:
            """Simulate expensive operation"""
            time.sleep(0.01)  # Simulate processing time
            return x * x * x
        
        # Test cache miss and hit
        start_time = time.time()
        result1 = expensive_operation(5)
        first_time = time.time() - start_time
        
        start_time = time.time()
        result2 = expensive_operation(5)  # Should be cached
        second_time = time.time() - start_time
        
        print(f"  ✅ Cache decorator test:")
        print(f"    First call (miss): {first_time:.4f}s")
        print(f"    Second call (hit): {second_time:.4f}s")
        print(f"    Speedup: {first_time / max(second_time, 0.0001):.1f}x")
        
        assert result1 == result2 == 125
        assert second_time < first_time
        
        # Test manual caching
        cache_manager.put('manual_test', {'data': 'test_value'}, 'test_key')
        cached_data = cache_manager.get('manual_test', 'test_key')
        
        print(f"  ✅ Manual cache test:")
        print(f"    Cached data: {cached_data}")
        
        assert cached_data == {'data': 'test_value'}
        
        # Test cache statistics
        stats = cache_manager.get_comprehensive_stats()
        
        print(f"  ✅ Cache statistics:")
        print(f"    Total requests: {stats.total_requests}")
        print(f"    Hit rate: {stats.hit_rate:.1%}")
        print(f"    Memory usage: {stats.memory_usage_mb:.2f}MB")
        
        # Test cache optimization analysis
        optimization_report = cache_manager.optimize_cache_configuration()
        
        print(f"  ✅ Cache optimization:")
        print(f"    Recommendations: {optimization_report['recommendations_count']}")
        
        # Verify results
        assert 0 <= stats.hit_rate <= 1
        assert stats.memory_usage_mb >= 0
        assert isinstance(optimization_report, dict)
        
        print("  ✅ Cache Manager: PASSED")
        return True
        
    except Exception as e:
        print(f"  ❌ Cache Manager: FAILED - {e}")
        return False

def test_batch_processor():
    """Test batch processing functionality"""
    print("\n⚡ Testing Batch Processor...")
    
    try:
        from src.services.batch_processor import BatchProcessor, BatchConfig
        
        # Configure for testing
        config = BatchConfig(
            max_workers=2,
            max_queue_size=100,
            batch_size=50,
            chunk_size=5,
            timeout_seconds=30
        )
        
        processor = BatchProcessor(config)
        
        # Start workers
        processor.start_workers()
        
        try:
            # Test text normalization batch
            text_data = [
                f"Test text {i} for normalization"
                for i in range(20)
            ]
            
            job_id = processor.submit_job('text_normalization', text_data)
            print(f"  ✅ Submitted text normalization job: {job_id}")
            
            # Test similarity calculation batch
            similarity_data = [
                (f"text_{i}", f"text_{i+1}")
                for i in range(10)
            ]
            
            similarity_job_id = processor.submit_job('similarity_calculation', similarity_data)
            print(f"  ✅ Submitted similarity job: {similarity_job_id}")
            
            # Wait for jobs to complete
            max_wait = 15  # seconds
            start_wait = time.time()
            
            while time.time() - start_wait < max_wait:
                text_status = processor.get_job_status(job_id) if job_id else None
                sim_status = processor.get_job_status(similarity_job_id) if similarity_job_id else None
                
                if (text_status and text_status['status'] == 'completed' and
                    sim_status and sim_status['status'] == 'completed'):
                    break
                
                time.sleep(0.5)
            
            # Check final status
            if job_id:
                final_status = processor.get_job_status(job_id)
                if final_status:
                    print(f"  ✅ Text normalization job:")
                    print(f"    Status: {final_status['status']}")
                    print(f"    Progress: {final_status['progress']:.1%}")
                    print(f"    Results: {final_status['results_count']}")
                    
                    if final_status['status'] == 'completed':
                        results = processor.get_job_results(job_id)
                        print(f"    Sample result: {results[0] if results else 'None'}")
            
            # Get batch statistics
            stats = processor.get_batch_stats()
            
            print(f"  ✅ Batch processing statistics:")
            print(f"    Total jobs: {stats.total_jobs}")
            print(f"    Completed: {stats.completed_jobs}")
            print(f"    Failed: {stats.failed_jobs}")
            print(f"    Throughput: {stats.throughput_items_per_second:.1f} items/s")
            print(f"    Queue utilization: {stats.queue_utilization:.1%}")
            print(f"    Worker utilization: {stats.worker_utilization:.1%}")
            
            # Test optimization recommendations
            optimization_report = processor.optimize_configuration()
            
            print(f"  ✅ Batch optimization:")
            print(f"    Recommendations: {optimization_report['recommendations_count']}")
            
            # Verify results
            assert stats.total_jobs >= 2  # At least our 2 submitted jobs
            assert 0 <= stats.queue_utilization <= 1
            assert 0 <= stats.worker_utilization <= 1
            
        finally:
            # Stop workers
            processor.stop_workers()
        
        print("  ✅ Batch Processor: PASSED")
        return True
        
    except Exception as e:
        print(f"  ❌ Batch Processor: FAILED - {e}")
        return False

def test_monitoring_service():
    """Test monitoring and alerting functionality"""
    print("\n📊 Testing Monitoring Service...")
    
    try:
        from src.services.monitoring_service import MonitoringService, AlertRule, AlertType, AlertSeverity
        
        monitoring = MonitoringService()
        
        # Start monitoring
        monitoring.start_monitoring()
        
        try:
            # Wait for some monitoring cycles
            time.sleep(3)
            
            # Get monitoring status
            status = monitoring.get_monitoring_status()
            
            print(f"  ✅ Monitoring status:")
            print(f"    Active: {status['monitoring_active']}")
            print(f"    Uptime: {status['uptime_formatted']}")
            print(f"    Monitoring cycles: {status['monitoring_cycles']}")
            print(f"    Alert rules: {status['alert_rules_count']}")
            
            # Get metric history
            memory_history = monitoring.get_metric_history('memory_usage_percent', hours=1)
            
            print(f"  ✅ Metric collection:")
            print(f"    Memory metrics collected: {len(memory_history)}")
            
            if memory_history:
                latest_memory = memory_history[-1]
                print(f"    Latest memory usage: {latest_memory['value']:.1f}%")
            
            # Add a test alert rule
            test_rule = AlertRule(
                rule_id="test_high_memory",
                alert_type=AlertType.MEMORY_USAGE,
                severity=AlertSeverity.WARNING,
                metric_name="memory_usage_percent",
                threshold=1.0,  # Very low threshold to trigger alert
                comparison="greater_than",
                time_window_minutes=1,
                min_occurrences=1,
                component="test",
                message_template="Test alert: Memory usage is {current_value:.1f}%"
            )
            
            monitoring.add_alert_rule(test_rule)
            print(f"  ✅ Added test alert rule")
            
            # Wait for potential alert
            time.sleep(3)
            
            # Check for alerts
            active_alerts = monitoring.get_active_alerts()
            alert_history = monitoring.get_alert_history(hours=1)
            
            print(f"  ✅ Alert system:")
            print(f"    Active alerts: {len(active_alerts)}")
            print(f"    Alert history: {len(alert_history)}")
            
            if active_alerts:
                alert = active_alerts[0]
                print(f"    Sample alert: {alert['title']}")
                print(f"    Severity: {alert['severity']}")
            
            # Verify monitoring functionality
            assert status['monitoring_active'] == True
            assert status['monitoring_cycles'] > 0
            assert isinstance(memory_history, list)
            assert isinstance(active_alerts, list)
            assert isinstance(alert_history, list)
            
        finally:
            # Stop monitoring
            monitoring.stop_monitoring()
        
        print("  ✅ Monitoring Service: PASSED")
        return True
        
    except Exception as e:
        print(f"  ❌ Monitoring Service: FAILED - {e}")
        return False

def test_integrated_optimization():
    """Test all optimization components working together"""
    print("\n🚀 Testing Integrated Optimization...")
    
    try:
        from src.services.cache_manager import CacheManager
        from src.services.batch_processor import BatchProcessor, BatchConfig
        from src.services.monitoring_service import MonitoringService
        from src.services.performance_analyzer import PerformanceAnalyzer
        
        # Initialize all components
        cache_manager = CacheManager()
        
        batch_config = BatchConfig(max_workers=2, chunk_size=3)
        batch_processor = BatchProcessor(batch_config, cache_manager)
        
        monitoring = MonitoringService()
        monitoring.set_components(cache_manager, batch_processor)
        
        performance_analyzer = PerformanceAnalyzer()
        
        print("  ✅ All components initialized")
        
        # Start all services
        batch_processor.start_workers()
        monitoring.start_monitoring()
        performance_analyzer.start_monitoring()
        
        try:
            # Test integrated workflow
            print("  🔄 Testing integrated workflow...")
            
            # 1. Submit batch jobs that use caching
            test_data = [f"integration_test_{i}" for i in range(15)]
            job_id = batch_processor.submit_job('text_normalization', test_data)
            
            # 2. Wait for processing
            time.sleep(5)
            
            # 3. Check results across all systems
            
            # Batch processor status
            if job_id:
                job_status = batch_processor.get_job_status(job_id)
                print(f"    Batch job status: {job_status['status'] if job_status else 'unknown'}")
            
            # Cache performance
            cache_stats = cache_manager.get_comprehensive_stats()
            print(f"    Cache hit rate: {cache_stats.hit_rate:.1%}")
            print(f"    Cache memory: {cache_stats.memory_usage_mb:.2f}MB")
            
            # Monitoring metrics
            monitoring_status = monitoring.get_monitoring_status()
            print(f"    Monitoring cycles: {monitoring_status['monitoring_cycles']}")
            
            # Performance analysis
            performance_report = performance_analyzer.generate_performance_report()
            print(f"    Performance score: {performance_report.overall_score:.1f}/100")
            
            # 4. Test optimization recommendations
            cache_optimization = cache_manager.optimize_cache_configuration()
            batch_optimization = batch_processor.optimize_configuration()
            
            total_recommendations = (
                cache_optimization['recommendations_count'] +
                batch_optimization['recommendations_count']
            )
            
            print(f"  ✅ Integration test results:")
            print(f"    Cache hit rate: {cache_stats.hit_rate:.1%}")
            print(f"    Performance score: {performance_report.overall_score:.1f}")
            print(f"    Total optimizations: {total_recommendations}")
            print(f"    Monitoring active: {monitoring_status['monitoring_active']}")
            
            # Verify integration
            assert cache_stats.total_requests > 0
            assert monitoring_status['monitoring_active']
            assert performance_report.overall_score >= 0
            
        finally:
            # Stop all services
            batch_processor.stop_workers()
            monitoring.stop_monitoring()
            performance_analyzer.stop_monitoring()
        
        print("  ✅ Integrated Optimization: PASSED")
        return True
        
    except Exception as e:
        print(f"  ❌ Integrated Optimization: FAILED - {e}")
        return False

def test_performance_improvements():
    """Test actual performance improvements"""
    print("\n⚡ Testing Performance Improvements...")
    
    try:
        from src.services.cache_manager import CacheManager
        
        # Test without caching
        def slow_operation(x):
            time.sleep(0.001)  # Simulate 1ms operation
            return x * x
        
        # Measure without caching
        start_time = time.time()
        results_no_cache = []
        for i in range(50):
            results_no_cache.append(slow_operation(i))
        time_no_cache = time.time() - start_time
        
        # Test with caching
        cache_manager = CacheManager()
        
        @cache_manager.cache_function('performance_test')
        def cached_slow_operation(x):
            time.sleep(0.001)  # Simulate 1ms operation
            return x * x
        
        # First run (cache misses)
        start_time = time.time()
        results_first_run = []
        for i in range(50):
            results_first_run.append(cached_slow_operation(i))
        time_first_run = time.time() - start_time
        
        # Second run (cache hits)
        start_time = time.time()
        results_second_run = []
        for i in range(50):
            results_second_run.append(cached_slow_operation(i))
        time_second_run = time.time() - start_time
        
        # Calculate improvements
        cache_speedup = time_first_run / max(time_second_run, 0.001)
        overall_speedup = time_no_cache / max(time_second_run, 0.001)
        
        print(f"  ✅ Performance test results:")
        print(f"    No cache: {time_no_cache:.4f}s")
        print(f"    First run (miss): {time_first_run:.4f}s")
        print(f"    Second run (hit): {time_second_run:.4f}s")
        print(f"    Cache speedup: {cache_speedup:.1f}x")
        print(f"    Overall speedup: {overall_speedup:.1f}x")
        
        # Verify results are correct
        assert results_no_cache == results_first_run == results_second_run
        assert cache_speedup > 5  # Should be significantly faster
        
        # Test cache statistics
        cache_stats = cache_manager.get_comprehensive_stats()
        
        print(f"  ✅ Cache performance:")
        print(f"    Hit rate: {cache_stats.hit_rate:.1%}")
        print(f"    Total requests: {cache_stats.total_requests}")
        print(f"    Cache hits: {cache_stats.cache_hits}")
        
        # Verify cache effectiveness
        assert cache_stats.hit_rate > 0.4  # At least 40% hit rate
        assert cache_stats.cache_hits > 0
        
        print("  ✅ Performance Improvements: PASSED")
        return True
        
    except Exception as e:
        print(f"  ❌ Performance Improvements: FAILED - {e}")
        return False

def main():
    """Run all Phase 3 optimization tests"""
    print("🚀 Phase 3 Performance Optimization Test Suite")
    print("=" * 60)
    
    test_functions = [
        test_performance_analyzer,
        test_database_optimizer,
        test_cache_manager,
        test_batch_processor,
        test_monitoring_service,
        test_performance_improvements,
        test_integrated_optimization
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ {test_func.__name__}: FAILED - {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Phase 3 Test Results: {passed} PASSED, {failed} FAILED")
    
    if failed == 0:
        print("🎉 All Phase 3 optimization components working correctly!")
        print("✅ Performance optimization system ready for production!")
        
        print("\n🚀 Phase 3 Achievements:")
        print("  ✅ Performance Analysis & Bottleneck Detection")
        print("  ✅ Database Query Optimization") 
        print("  ✅ Multi-Level Caching System")
        print("  ✅ High-Performance Batch Processing")
        print("  ✅ Real-Time Monitoring & Alerting")
        print("  ✅ Integrated Optimization Pipeline")
        print("  ✅ Significant Performance Improvements")
        
    else:
        print(f"⚠️  {failed} test(s) failed - review implementation before production")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)