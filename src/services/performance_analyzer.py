"""
Performance Analysis Service
Analyzes system performance bottlenecks and provides optimization recommendations
"""

import time
import psutil
import logging
import statistics
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import json
import threading
from collections import defaultdict, deque
import gc
import tracemalloc

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any]


@dataclass
class BottleneckAnalysis:
    """Analysis of performance bottlenecks"""
    component: str
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    current_performance: float
    target_performance: float
    impact_score: float
    recommendations: List[str]
    evidence: Dict[str, Any]


@dataclass
class PerformanceReport:
    """Complete performance analysis report"""
    timestamp: datetime
    overall_score: float
    bottlenecks: List[BottleneckAnalysis]
    metrics: Dict[str, List[PerformanceMetric]]
    recommendations: List[str]
    system_stats: Dict[str, Any]


class PerformanceAnalyzer:
    """Analyzes system performance and identifies optimization opportunities"""
    
    def __init__(self):
        """Initialize performance analyzer"""
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.active_monitors = {}
        self.performance_targets = {
            # Component performance targets (seconds)
            'fuzzy_matching_per_comparison': 0.001,
            'semantic_similarity_per_comparison': 0.0005,
            'confidence_calculation_per_comparison': 0.002,
            'advanced_matching_per_comparison': 0.005,
            'database_query_per_product': 0.01,
            'text_normalization_per_text': 0.0001,
            'sku_extraction_per_text': 0.0002,
            'brand_normalization_per_text': 0.0001,
            
            # Throughput targets (operations per second)
            'matching_throughput_ops_per_sec': 100,
            'batch_processing_products_per_sec': 50,
            'database_reads_per_sec': 1000,
            'cache_hit_rate_percentage': 80,
            
            # Resource targets
            'memory_usage_mb': 512,
            'cpu_usage_percentage': 70,
            'database_connection_count': 10,
        }
        
        # Severity thresholds (multipliers of target)
        self.severity_thresholds = {
            'low': 1.2,      # 20% over target
            'medium': 1.5,   # 50% over target  
            'high': 2.0,     # 100% over target
            'critical': 3.0  # 200% over target
        }
        
        self.monitoring_active = False
        
    def start_monitoring(self):
        """Start continuous performance monitoring"""
        self.monitoring_active = True
        
        # Start memory tracking
        tracemalloc.start()
        
        # Start background monitoring thread
        monitor_thread = threading.Thread(target=self._background_monitor, daemon=True)
        monitor_thread.start()
        
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        tracemalloc.stop()
        logger.info("Performance monitoring stopped")
    
    def _background_monitor(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Sleep for monitoring interval
                time.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
    
    def _collect_system_metrics(self):
        """Collect system-level performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self._record_metric("system_cpu_usage", cpu_percent, "percentage")
            
            # Memory usage
            memory = psutil.virtual_memory()
            self._record_metric("system_memory_usage", memory.percent, "percentage")
            self._record_metric("system_memory_available", memory.available / (1024**2), "MB")
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self._record_metric("disk_read_bytes_per_sec", disk_io.read_bytes, "bytes/s")
                self._record_metric("disk_write_bytes_per_sec", disk_io.write_bytes, "bytes/s")
            
            # Network I/O
            net_io = psutil.net_io_counters()
            if net_io:
                self._record_metric("network_sent_bytes_per_sec", net_io.bytes_sent, "bytes/s")
                self._record_metric("network_recv_bytes_per_sec", net_io.bytes_recv, "bytes/s")
            
            # Process-specific metrics
            process = psutil.Process()
            self._record_metric("process_memory_rss", process.memory_info().rss / (1024**2), "MB")
            self._record_metric("process_cpu_percent", process.cpu_percent(), "percentage")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _record_metric(self, name: str, value: float, unit: str, context: Dict = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            context=context or {}
        )
        
        self.metrics_history[name].append(metric)
    
    def benchmark_component(self, component_name: str, test_function, 
                          iterations: int = 100, *args, **kwargs) -> Dict[str, float]:
        """Benchmark a specific component"""
        logger.info(f"Benchmarking {component_name} ({iterations} iterations)")
        
        times = []
        memory_usage = []
        
        # Warm up
        for _ in range(min(10, iterations // 10)):
            test_function(*args, **kwargs)
        
        # Clear garbage before testing
        gc.collect()
        
        # Benchmark
        for i in range(iterations):
            # Memory before
            memory_before = self._get_memory_usage()
            
            # Time the operation
            start_time = time.perf_counter()
            result = test_function(*args, **kwargs)
            end_time = time.perf_counter()
            
            # Memory after
            memory_after = self._get_memory_usage()
            
            execution_time = end_time - start_time
            memory_delta = memory_after - memory_before
            
            times.append(execution_time)
            memory_usage.append(memory_delta)
            
            # Record metrics
            self._record_metric(
                f"{component_name}_execution_time",
                execution_time,
                "seconds",
                {"iteration": i, "result_type": type(result).__name__}
            )
        
        # Calculate statistics
        stats = {
            'mean_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_time': statistics.stdev(times) if len(times) > 1 else 0,
            'p95_time': self._percentile(times, 95),
            'p99_time': self._percentile(times, 99),
            'mean_memory': statistics.mean(memory_usage),
            'max_memory': max(memory_usage),
            'iterations': iterations
        }
        
        logger.info(f"{component_name} benchmark complete: "
                   f"mean={stats['mean_time']:.4f}s, "
                   f"p95={stats['p95_time']:.4f}s, "
                   f"memory={stats['mean_memory']:.2f}MB")
        
        return stats
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024**2)
        except:
            return 0.0
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def analyze_bottlenecks(self, components: List[str] = None) -> List[BottleneckAnalysis]:
        """Analyze performance bottlenecks"""
        bottlenecks = []
        
        # Get components to analyze
        if components is None:
            components = [
                'fuzzy_matching', 'semantic_similarity', 'confidence_calculation',
                'advanced_matching', 'database_query', 'text_normalization',
                'sku_extraction', 'brand_normalization'
            ]
        
        for component in components:
            # Analyze component performance
            bottleneck = self._analyze_component_performance(component)
            if bottleneck:
                bottlenecks.append(bottleneck)
        
        # Sort by impact score (highest first)
        bottlenecks.sort(key=lambda x: x.impact_score, reverse=True)
        
        return bottlenecks
    
    def _analyze_component_performance(self, component: str) -> Optional[BottleneckAnalysis]:
        """Analyze performance of a specific component"""
        metric_name = f"{component}_execution_time"
        target_key = f"{component}_per_comparison"
        
        # Get recent metrics
        recent_metrics = list(self.metrics_history.get(metric_name, []))[-100:]
        
        if not recent_metrics:
            return None
        
        # Calculate current performance
        recent_times = [m.value for m in recent_metrics]
        current_performance = statistics.mean(recent_times)
        
        # Get target performance
        target_performance = self.performance_targets.get(target_key, 0.001)
        
        # Calculate severity
        performance_ratio = current_performance / target_performance
        severity = self._calculate_severity(performance_ratio)
        
        if severity == 'low' and performance_ratio < 1.2:
            return None  # Performance is acceptable
        
        # Calculate impact score
        impact_score = self._calculate_impact_score(component, performance_ratio, recent_metrics)
        
        # Generate recommendations
        recommendations = self._generate_component_recommendations(component, performance_ratio)
        
        # Gather evidence
        evidence = {
            'current_mean': current_performance,
            'current_p95': self._percentile(recent_times, 95),
            'current_max': max(recent_times),
            'sample_size': len(recent_times),
            'performance_ratio': performance_ratio,
            'recent_trend': self._calculate_trend(recent_times)
        }
        
        return BottleneckAnalysis(
            component=component,
            issue_type='performance_degradation',
            severity=severity,
            current_performance=current_performance,
            target_performance=target_performance,
            impact_score=impact_score,
            recommendations=recommendations,
            evidence=evidence
        )
    
    def _calculate_severity(self, performance_ratio: float) -> str:
        """Calculate severity based on performance ratio"""
        if performance_ratio >= self.severity_thresholds['critical']:
            return 'critical'
        elif performance_ratio >= self.severity_thresholds['high']:
            return 'high'
        elif performance_ratio >= self.severity_thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_impact_score(self, component: str, performance_ratio: float, 
                              recent_metrics: List[PerformanceMetric]) -> float:
        """Calculate impact score for bottleneck prioritization"""
        # Base score from performance degradation
        degradation_score = min(performance_ratio - 1.0, 3.0) * 100
        
        # Usage frequency weight
        usage_weight = len(recent_metrics) / 100.0  # Higher if used frequently
        
        # Component importance weight
        importance_weights = {
            'advanced_matching': 1.0,
            'fuzzy_matching': 0.8,
            'semantic_similarity': 0.8,
            'confidence_calculation': 0.7,
            'database_query': 0.9,
            'text_normalization': 0.6,
            'sku_extraction': 0.7,
            'brand_normalization': 0.5
        }
        
        importance_weight = importance_weights.get(component, 0.5)
        
        # Trend weight (increasing performance issues are worse)
        recent_times = [m.value for m in recent_metrics[-20:]]
        trend = self._calculate_trend(recent_times)
        trend_weight = 1.0 + max(0, trend) * 0.5  # Positive trend increases impact
        
        impact_score = degradation_score * usage_weight * importance_weight * trend_weight
        
        return min(impact_score, 100.0)  # Cap at 100
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend in values (positive = increasing, negative = decreasing)"""
        if len(values) < 3:
            return 0.0
        
        # Simple linear regression slope
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _generate_component_recommendations(self, component: str, 
                                          performance_ratio: float) -> List[str]:
        """Generate optimization recommendations for component"""
        recommendations = []
        
        base_recommendations = {
            'fuzzy_matching': [
                "Implement result caching for repeated string pairs",
                "Use faster string distance algorithms for initial filtering",
                "Parallelize batch fuzzy matching operations",
                "Pre-compile regex patterns for better performance"
            ],
            'semantic_similarity': [
                "Cache TF-IDF vectors for frequently accessed texts",
                "Use approximate similarity for initial filtering",
                "Implement incremental model training",
                "Optimize vector operations with NumPy optimizations"
            ],
            'confidence_calculation': [
                "Cache confidence scores for identical product pairs",
                "Optimize factor calculation order by computational cost",
                "Use lookup tables for common confidence patterns",
                "Parallelize independent factor calculations"
            ],
            'advanced_matching': [
                "Implement multi-level caching strategy",
                "Use early termination for low-confidence matches",
                "Optimize component integration order",
                "Add result preprocessing and filtering"
            ],
            'database_query': [
                "Add database indices for frequently queried columns",
                "Implement query result caching",
                "Use connection pooling for database access",
                "Optimize SQL queries with query analysis"
            ],
            'text_normalization': [
                "Cache normalization results for repeated texts",
                "Optimize regex pattern matching",
                "Use compiled patterns for better performance",
                "Implement batch text processing"
            ]
        }
        
        component_recs = base_recommendations.get(component, [])
        
        # Add severity-specific recommendations
        if performance_ratio > 2.0:
            recommendations.extend([
                f"URGENT: {component} performance is critically degraded",
                "Consider disabling non-essential features temporarily",
                "Investigate potential memory leaks or resource exhaustion"
            ])
        elif performance_ratio > 1.5:
            recommendations.extend([
                f"HIGH PRIORITY: Optimize {component} immediately",
                "Review recent code changes for performance regressions"
            ])
        
        recommendations.extend(component_recs[:3])  # Add top 3 specific recommendations
        
        return recommendations
    
    def generate_performance_report(self) -> PerformanceReport:
        """Generate comprehensive performance report"""
        logger.info("Generating performance report")
        
        # Analyze bottlenecks
        bottlenecks = self.analyze_bottlenecks()
        
        # Calculate overall performance score
        overall_score = self._calculate_overall_score(bottlenecks)
        
        # Aggregate metrics by category
        metrics_by_category = self._aggregate_metrics()
        
        # Generate high-level recommendations
        recommendations = self._generate_overall_recommendations(bottlenecks, overall_score)
        
        # Collect system statistics
        system_stats = self._collect_system_stats()
        
        report = PerformanceReport(
            timestamp=datetime.now(),
            overall_score=overall_score,
            bottlenecks=bottlenecks,
            metrics=metrics_by_category,
            recommendations=recommendations,
            system_stats=system_stats
        )
        
        logger.info(f"Performance report generated: score={overall_score:.1f}, "
                   f"bottlenecks={len(bottlenecks)}")
        
        return report
    
    def _calculate_overall_score(self, bottlenecks: List[BottleneckAnalysis]) -> float:
        """Calculate overall performance score (0-100)"""
        if not bottlenecks:
            return 95.0  # Good performance, but room for improvement
        
        # Start with perfect score and deduct for bottlenecks
        score = 100.0
        
        for bottleneck in bottlenecks:
            # Deduct points based on severity and impact
            severity_deductions = {
                'low': 2,
                'medium': 5,
                'high': 10,
                'critical': 20
            }
            
            base_deduction = severity_deductions.get(bottleneck.severity, 5)
            impact_multiplier = min(bottleneck.impact_score / 50.0, 2.0)
            
            deduction = base_deduction * impact_multiplier
            score -= deduction
        
        return max(score, 0.0)
    
    def _aggregate_metrics(self) -> Dict[str, List[PerformanceMetric]]:
        """Aggregate metrics by category"""
        categories = {
            'execution_times': [],
            'system_resources': [],
            'throughput': [],
            'memory_usage': []
        }
        
        for metric_name, metrics in self.metrics_history.items():
            recent_metrics = list(metrics)[-50:]  # Last 50 metrics
            
            if 'execution_time' in metric_name:
                categories['execution_times'].extend(recent_metrics)
            elif any(term in metric_name for term in ['cpu', 'memory', 'disk', 'network']):
                categories['system_resources'].extend(recent_metrics)
            elif 'throughput' in metric_name or 'ops_per_sec' in metric_name:
                categories['throughput'].extend(recent_metrics)
            elif 'memory' in metric_name:
                categories['memory_usage'].extend(recent_metrics)
        
        return categories
    
    def _generate_overall_recommendations(self, bottlenecks: List[BottleneckAnalysis], 
                                        overall_score: float) -> List[str]:
        """Generate high-level performance recommendations"""
        recommendations = []
        
        if overall_score >= 90:
            recommendations.append("🎉 Excellent performance! System is well-optimized.")
            recommendations.append("Continue monitoring for performance regressions.")
        elif overall_score >= 75:
            recommendations.append("✅ Good performance with minor optimization opportunities.")
        elif overall_score >= 60:
            recommendations.append("⚠️  Moderate performance issues detected - optimization recommended.")
        else:
            recommendations.append("🚨 CRITICAL: Significant performance degradation detected!")
            recommendations.append("Immediate optimization required to maintain system usability.")
        
        # Add bottleneck-specific recommendations
        if bottlenecks:
            critical_bottlenecks = [b for b in bottlenecks if b.severity == 'critical']
            high_bottlenecks = [b for b in bottlenecks if b.severity == 'high']
            
            if critical_bottlenecks:
                recommendations.append(f"🔥 URGENT: Address {len(critical_bottlenecks)} critical bottlenecks immediately")
                for bottleneck in critical_bottlenecks[:2]:  # Top 2 critical
                    recommendations.append(f"  • {bottleneck.component}: {bottleneck.recommendations[0]}")
            
            if high_bottlenecks:
                recommendations.append(f"⚡ HIGH PRIORITY: Optimize {len(high_bottlenecks)} high-impact components")
                for bottleneck in high_bottlenecks[:3]:  # Top 3 high-impact
                    recommendations.append(f"  • {bottleneck.component}: {bottleneck.recommendations[0]}")
        
        # Add general optimization recommendations
        recommendations.extend([
            "Implement comprehensive caching strategy for repeated operations",
            "Consider database query optimization and indexing",
            "Monitor memory usage patterns for potential leaks",
            "Set up automated performance regression testing"
        ])
        
        return recommendations
    
    def _collect_system_stats(self) -> Dict[str, Any]:
        """Collect current system statistics"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_total_gb': memory.total / (1024**3),
                'memory_available_gb': memory.available / (1024**3),
                'memory_percent': memory.percent,
                'disk_total_gb': disk.total / (1024**3),
                'disk_free_gb': disk.free / (1024**3),
                'disk_percent': (disk.used / disk.total) * 100,
                'process_count': len(psutil.pids()),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
        except Exception as e:
            logger.error(f"Error collecting system stats: {e}")
            return {}
    
    def save_report(self, report: PerformanceReport, filepath: str = None):
        """Save performance report to file"""
        if filepath is None:
            timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")
            filepath = f"performance_report_{timestamp}.json"
        
        try:
            # Convert report to JSON-serializable format
            report_data = {
                'timestamp': report.timestamp.isoformat(),
                'overall_score': report.overall_score,
                'bottlenecks': [asdict(b) for b in report.bottlenecks],
                'recommendations': report.recommendations,
                'system_stats': report.system_stats,
                'metrics_summary': {
                    category: len(metrics) 
                    for category, metrics in report.metrics.items()
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Performance report saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving performance report: {e}")


# Example usage and testing
if __name__ == "__main__":
    import sys
    import os
    
    # Add src to path for testing
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    # Test performance analyzer
    analyzer = PerformanceAnalyzer()
    
    print("🔍 Performance Analysis Demo")
    print("=" * 50)
    
    # Start monitoring
    analyzer.start_monitoring()
    
    try:
        # Simulate some operations for benchmarking
        def dummy_operation(size=1000):
            """Dummy operation for testing"""
            data = list(range(size))
            result = sum(x * x for x in data)
            return result
        
        # Benchmark the dummy operation
        stats = analyzer.benchmark_component(
            "dummy_operation", 
            dummy_operation, 
            iterations=50,
            size=1000
        )
        
        print(f"Benchmark Results:")
        print(f"  Mean time: {stats['mean_time']:.4f}s")
        print(f"  P95 time: {stats['p95_time']:.4f}s")
        print(f"  Memory usage: {stats['mean_memory']:.2f}MB")
        
        # Wait for some monitoring data
        time.sleep(2)
        
        # Generate performance report
        report = analyzer.generate_performance_report()
        
        print(f"\nPerformance Report:")
        print(f"  Overall Score: {report.overall_score:.1f}/100")
        print(f"  Bottlenecks Found: {len(report.bottlenecks)}")
        
        if report.bottlenecks:
            print(f"  Top Bottleneck: {report.bottlenecks[0].component} "
                  f"({report.bottlenecks[0].severity})")
        
        print(f"  Recommendations: {len(report.recommendations)}")
        for i, rec in enumerate(report.recommendations[:3], 1):
            print(f"    {i}. {rec}")
        
        # Save report
        analyzer.save_report(report, "demo_performance_report.json")
        
    finally:
        # Stop monitoring
        analyzer.stop_monitoring()
    
    print("\n✅ Performance analysis demo completed")