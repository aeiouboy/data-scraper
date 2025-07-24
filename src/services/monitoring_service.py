"""
Comprehensive Monitoring and Alerting Service
Real-time monitoring of system performance with automated alerts
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
import schedule

from src.services.performance_analyzer import PerformanceAnalyzer
from src.services.cache_manager import CacheManager
from src.services.batch_processor import BatchProcessor
from src.services.validation_pipeline import ValidationPipeline

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CACHE_MISS_RATE = "cache_miss_rate"
    QUEUE_OVERFLOW = "queue_overflow"
    VALIDATION_FAILURE = "validation_failure"
    MEMORY_USAGE = "memory_usage"
    DATABASE_SLOW = "database_slow"
    SYSTEM_ERROR = "system_error"
    MATCHING_ACCURACY = "matching_accuracy"


@dataclass
class Alert:
    """Alert definition"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    component: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_message: Optional[str] = None


@dataclass
class AlertRule:
    """Alert rule configuration"""
    rule_id: str
    alert_type: AlertType
    severity: AlertSeverity
    metric_name: str
    threshold: float
    comparison: str  # 'greater_than', 'less_than', 'equals'
    time_window_minutes: int = 5
    min_occurrences: int = 1
    enabled: bool = True
    component: str = "system"
    message_template: str = "Alert: {metric_name} is {current_value} (threshold: {threshold})"


@dataclass
class MonitoringConfig:
    """Monitoring system configuration"""
    monitoring_interval_seconds: int = 30
    alert_check_interval_seconds: int = 60
    history_retention_hours: int = 24
    enable_email_alerts: bool = False
    enable_webhook_alerts: bool = False
    email_config: Dict[str, Any] = field(default_factory=dict)
    webhook_config: Dict[str, Any] = field(default_factory=dict)
    slack_config: Dict[str, Any] = field(default_factory=dict)


class MonitoringService:
    """Comprehensive monitoring and alerting service"""
    
    def __init__(self, config: MonitoringConfig = None):
        """Initialize monitoring service"""
        self.config = config or MonitoringConfig()
        
        # Components to monitor
        self.performance_analyzer = PerformanceAnalyzer()
        self.cache_manager = None  # Will be set externally
        self.batch_processor = None  # Will be set externally
        self.validation_pipeline = None  # Will be set externally
        
        # Alert management
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = deque(maxlen=10000)
        self.metrics_history = defaultdict(lambda: deque(maxlen=2000))
        
        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        self.alert_thread = None
        
        # Statistics
        self.stats = {
            'alerts_triggered': 0,
            'alerts_resolved': 0,
            'monitoring_cycles': 0,
            'last_monitoring_time': None,
            'uptime_start': datetime.now()
        }
        
        # Initialize default alert rules
        self._setup_default_alert_rules()
    
    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule(
                rule_id="high_memory_usage",
                alert_type=AlertType.MEMORY_USAGE,
                severity=AlertSeverity.WARNING,
                metric_name="memory_usage_percent",
                threshold=80.0,
                comparison="greater_than",
                time_window_minutes=5,
                min_occurrences=2,
                component="system",
                message_template="High memory usage: {current_value:.1f}% (threshold: {threshold}%)"
            ),
            AlertRule(
                rule_id="low_cache_hit_rate",
                alert_type=AlertType.CACHE_MISS_RATE,
                severity=AlertSeverity.WARNING,
                metric_name="cache_hit_rate",
                threshold=0.7,
                comparison="less_than",
                time_window_minutes=10,
                min_occurrences=3,
                component="cache",
                message_template="Low cache hit rate: {current_value:.1%} (threshold: {threshold:.1%})"
            ),
            AlertRule(
                rule_id="slow_matching_performance",
                alert_type=AlertType.PERFORMANCE_DEGRADATION,
                severity=AlertSeverity.ERROR,
                metric_name="avg_matching_time",
                threshold=5.0,
                comparison="greater_than",
                time_window_minutes=5,
                min_occurrences=3,
                component="matching",
                message_template="Slow matching performance: {current_value:.2f}s (threshold: {threshold}s)"
            ),
            AlertRule(
                rule_id="validation_accuracy_drop",
                alert_type=AlertType.MATCHING_ACCURACY,
                severity=AlertSeverity.CRITICAL,
                metric_name="validation_accuracy",
                threshold=0.85,
                comparison="less_than",
                time_window_minutes=15,
                min_occurrences=1,
                component="validation",
                message_template="Matching accuracy dropped: {current_value:.1%} (threshold: {threshold:.1%})"
            ),
            AlertRule(
                rule_id="batch_queue_overflow",
                alert_type=AlertType.QUEUE_OVERFLOW,
                severity=AlertSeverity.ERROR,
                metric_name="queue_utilization",
                threshold=0.9,
                comparison="greater_than",
                time_window_minutes=5,
                min_occurrences=2,
                component="batch_processor",
                message_template="Batch queue overflow: {current_value:.1%} full (threshold: {threshold:.1%})"
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
    
    def set_components(self, cache_manager: CacheManager = None,
                      batch_processor: BatchProcessor = None,
                      validation_pipeline: ValidationPipeline = None):
        """Set component references for monitoring"""
        if cache_manager:
            self.cache_manager = cache_manager
        if batch_processor:
            self.batch_processor = batch_processor
        if validation_pipeline:
            self.validation_pipeline = validation_pipeline
    
    def start_monitoring(self):
        """Start the monitoring service"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start performance analyzer
        self.performance_analyzer.start_monitoring()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="MonitoringService",
            daemon=True
        )
        self.monitor_thread.start()
        
        # Start alert checking thread
        self.alert_thread = threading.Thread(
            target=self._alert_loop,
            name="AlertService",
            daemon=True
        )
        self.alert_thread.start()
        
        logger.info("Monitoring service started")
    
    def stop_monitoring(self):
        """Stop the monitoring service"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        
        # Stop performance analyzer
        self.performance_analyzer.stop_monitoring()
        
        # Wait for threads to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        if self.alert_thread:
            self.alert_thread.join(timeout=5.0)
        
        logger.info("Monitoring service stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                start_time = time.time()
                
                # Collect metrics from all components
                self._collect_all_metrics()
                
                # Update statistics
                self.stats['monitoring_cycles'] += 1
                self.stats['last_monitoring_time'] = datetime.now()
                
                # Calculate sleep time
                elapsed = time.time() - start_time
                sleep_time = max(0, self.config.monitoring_interval_seconds - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.config.monitoring_interval_seconds)
    
    def _alert_loop(self):
        """Alert checking loop"""
        while self.monitoring_active:
            try:
                start_time = time.time()
                
                # Check all alert rules
                self._check_alert_rules()
                
                # Resolve alerts that are no longer triggered
                self._check_alert_resolution()
                
                # Calculate sleep time
                elapsed = time.time() - start_time
                sleep_time = max(0, self.config.alert_check_interval_seconds - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Alert loop error: {e}")
                time.sleep(self.config.alert_check_interval_seconds)
    
    def _collect_all_metrics(self):
        """Collect metrics from all monitored components"""
        timestamp = datetime.now()
        
        # System metrics (from performance analyzer)
        try:
            system_metrics = self._get_system_metrics()
            for metric_name, value in system_metrics.items():
                self._record_metric(metric_name, value, timestamp)
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
        
        # Cache metrics
        if self.cache_manager:
            try:
                cache_stats = self.cache_manager.get_comprehensive_stats()
                cache_metrics = {
                    'cache_hit_rate': cache_stats.hit_rate,
                    'cache_memory_usage_mb': cache_stats.memory_usage_mb,
                    'cache_entry_count': cache_stats.entry_count
                }
                for metric_name, value in cache_metrics.items():
                    self._record_metric(metric_name, value, timestamp)
            except Exception as e:
                logger.error(f"Error collecting cache metrics: {e}")
        
        # Batch processor metrics
        if self.batch_processor:
            try:
                batch_stats = self.batch_processor.get_batch_stats()
                batch_metrics = {
                    'queue_utilization': batch_stats.queue_utilization,
                    'worker_utilization': batch_stats.worker_utilization,
                    'batch_throughput': batch_stats.throughput_items_per_second,
                    'avg_batch_processing_time': batch_stats.avg_processing_time
                }
                for metric_name, value in batch_metrics.items():
                    self._record_metric(metric_name, value, timestamp)
            except Exception as e:
                logger.error(f"Error collecting batch processor metrics: {e}")
        
        # Validation metrics
        if self.validation_pipeline:
            try:
                # Get recent validation results
                recent_validations = self.validation_pipeline.get_validation_history(days=1)
                if recent_validations:
                    latest_validation = recent_validations[0]
                    validation_metrics = {
                        'validation_accuracy': latest_validation.accuracy,
                        'validation_precision': latest_validation.precision,
                        'validation_recall': latest_validation.recall,
                        'validation_f1_score': latest_validation.f1_score
                    }
                    for metric_name, value in validation_metrics.items():
                        self._record_metric(metric_name, value, timestamp)
            except Exception as e:
                logger.error(f"Error collecting validation metrics: {e}")
    
    def _get_system_metrics(self) -> Dict[str, float]:
        """Get system-level metrics"""
        import psutil
        
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info().rss / (1024**2)  # MB
            process_cpu = process.cpu_percent()
            
            return {
                'memory_usage_percent': memory.percent,
                'memory_available_mb': memory.available / (1024**2),
                'cpu_usage_percent': cpu_percent,
                'process_memory_mb': process_memory,
                'process_cpu_percent': process_cpu
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def _record_metric(self, metric_name: str, value: float, timestamp: datetime):
        """Record a metric value"""
        metric_entry = {
            'value': value,
            'timestamp': timestamp
        }
        
        self.metrics_history[metric_name].append(metric_entry)
        
        # Clean old metrics (keep only recent data)
        cutoff_time = timestamp - timedelta(hours=self.config.history_retention_hours)
        while (self.metrics_history[metric_name] and 
               self.metrics_history[metric_name][0]['timestamp'] < cutoff_time):
            self.metrics_history[metric_name].popleft()
    
    def _check_alert_rules(self):
        """Check all alert rules against current metrics"""
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            try:
                # Get recent metric values
                recent_values = self._get_recent_metric_values(
                    rule.metric_name, 
                    rule.time_window_minutes
                )
                
                if len(recent_values) < rule.min_occurrences:
                    continue
                
                # Check if threshold is exceeded
                violations = 0
                current_value = None
                
                for value in recent_values:
                    if self._check_threshold(value, rule.threshold, rule.comparison):
                        violations += 1
                        current_value = value
                
                # Trigger alert if enough violations
                if violations >= rule.min_occurrences:
                    self._trigger_alert(rule, current_value)
                
            except Exception as e:
                logger.error(f"Error checking alert rule {rule_id}: {e}")
    
    def _get_recent_metric_values(self, metric_name: str, minutes: int) -> List[float]:
        """Get recent metric values within time window"""
        if metric_name not in self.metrics_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_values = []
        
        for entry in reversed(self.metrics_history[metric_name]):
            if entry['timestamp'] >= cutoff_time:
                recent_values.append(entry['value'])
            else:
                break
        
        return recent_values
    
    def _check_threshold(self, value: float, threshold: float, comparison: str) -> bool:
        """Check if value violates threshold"""
        if comparison == "greater_than":
            return value > threshold
        elif comparison == "less_than":
            return value < threshold
        elif comparison == "equals":
            return abs(value - threshold) < 0.001
        else:
            return False
    
    def _trigger_alert(self, rule: AlertRule, current_value: float):
        """Trigger an alert"""
        alert_id = f"{rule.rule_id}_{int(time.time())}"
        
        # Check if similar alert is already active
        for active_alert in self.active_alerts.values():
            if (active_alert.alert_type == rule.alert_type and 
                active_alert.component == rule.component and
                not active_alert.resolved):
                return  # Don't duplicate alerts
        
        # Create new alert
        alert = Alert(
            alert_id=alert_id,
            alert_type=rule.alert_type,
            severity=rule.severity,
            title=f"{rule.component.title()} Alert: {rule.alert_type.value}",
            message=rule.message_template.format(
                metric_name=rule.metric_name,
                current_value=current_value,
                threshold=rule.threshold
            ),
            timestamp=datetime.now(),
            component=rule.component,
            metrics={rule.metric_name: current_value},
            threshold_value=rule.threshold,
            current_value=current_value
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Update statistics
        self.stats['alerts_triggered'] += 1
        
        # Send notifications
        self._send_alert_notifications(alert)
        
        logger.warning(f"Alert triggered: {alert.title} - {alert.message}")
    
    def _check_alert_resolution(self):
        """Check if active alerts should be resolved"""
        for alert_id, alert in list(self.active_alerts.items()):
            if alert.resolved:
                continue
            
            # Find corresponding rule
            rule = None
            for r in self.alert_rules.values():
                if (r.alert_type == alert.alert_type and 
                    r.component == alert.component):
                    rule = r
                    break
            
            if not rule:
                continue
            
            # Check if condition is no longer violated
            recent_values = self._get_recent_metric_values(
                rule.metric_name, 
                rule.time_window_minutes
            )
            
            if len(recent_values) < rule.min_occurrences:
                continue
            
            violations = sum(
                1 for value in recent_values 
                if self._check_threshold(value, rule.threshold, rule.comparison)
            )
            
            # Resolve alert if condition is no longer met
            if violations < rule.min_occurrences:
                self._resolve_alert(alert_id, "Condition no longer violated")
    
    def _resolve_alert(self, alert_id: str, resolution_message: str):
        """Resolve an active alert"""
        if alert_id not in self.active_alerts:
            return
        
        alert = self.active_alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.now()
        alert.resolution_message = resolution_message
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        # Update statistics
        self.stats['alerts_resolved'] += 1
        
        logger.info(f"Alert resolved: {alert.title} - {resolution_message}")
    
    def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications via configured channels"""
        try:
            # Email notifications
            if self.config.enable_email_alerts and self.config.email_config:
                self._send_email_alert(alert)
            
            # Webhook notifications
            if self.config.enable_webhook_alerts and self.config.webhook_config:
                self._send_webhook_alert(alert)
            
            # Slack notifications
            if self.config.slack_config.get('webhook_url'):
                self._send_slack_alert(alert)
                
        except Exception as e:
            logger.error(f"Error sending alert notifications: {e}")
    
    def _send_email_alert(self, alert: Alert):
        """Send email alert notification"""
        email_config = self.config.email_config
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = ', '.join(email_config['to_emails'])
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            # Create email body
            body = f"""
Alert Details:
- Type: {alert.alert_type.value}
- Severity: {alert.severity.value}
- Component: {alert.component}
- Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- Message: {alert.message}

Current Value: {alert.current_value}
Threshold: {alert.threshold_value}

Alert ID: {alert.alert_id}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port'])
            if email_config.get('use_tls'):
                server.starttls()
            if email_config.get('username'):
                server.login(email_config['username'], email_config['password'])
            
            server.sendmail(msg['From'], email_config['to_emails'], msg.as_string())
            server.quit()
            
            logger.info(f"Email alert sent for {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _send_webhook_alert(self, alert: Alert):
        """Send webhook alert notification"""
        webhook_config = self.config.webhook_config
        
        try:
            payload = {
                'alert_id': alert.alert_id,
                'alert_type': alert.alert_type.value,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'component': alert.component,
                'timestamp': alert.timestamp.isoformat(),
                'current_value': alert.current_value,
                'threshold_value': alert.threshold_value,
                'metrics': alert.metrics
            }
            
            response = requests.post(
                webhook_config['url'],
                json=payload,
                headers=webhook_config.get('headers', {}),
                timeout=10
            )
            
            response.raise_for_status()
            logger.info(f"Webhook alert sent for {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def _send_slack_alert(self, alert: Alert):
        """Send Slack alert notification"""
        slack_config = self.config.slack_config
        
        try:
            # Choose color based on severity
            color_map = {
                AlertSeverity.INFO: "good",
                AlertSeverity.WARNING: "warning", 
                AlertSeverity.ERROR: "danger",
                AlertSeverity.CRITICAL: "#ff0000"
            }
            
            payload = {
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "warning"),
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Component",
                                "value": alert.component,
                                "short": True
                            },
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Current Value",
                                "value": str(alert.current_value),
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": str(alert.threshold_value),
                                "short": True
                            }
                        ],
                        "footer": "RIS Monitoring",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            response = requests.post(
                slack_config['webhook_url'],
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            logger.info(f"Slack alert sent for {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        uptime = datetime.now() - self.stats['uptime_start']
        
        return {
            'monitoring_active': self.monitoring_active,
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': str(uptime),
            'monitoring_cycles': self.stats['monitoring_cycles'],
            'last_monitoring_time': self.stats['last_monitoring_time'].isoformat() if self.stats['last_monitoring_time'] else None,
            'alerts_triggered': self.stats['alerts_triggered'],
            'alerts_resolved': self.stats['alerts_resolved'],
            'active_alerts_count': len(self.active_alerts),
            'alert_rules_count': len([r for r in self.alert_rules.values() if r.enabled]),
            'components_monitored': {
                'performance_analyzer': True,
                'cache_manager': self.cache_manager is not None,
                'batch_processor': self.batch_processor is not None,
                'validation_pipeline': self.validation_pipeline is not None
            }
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [asdict(alert) for alert in self.active_alerts.values()]
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_alerts = [
            asdict(alert) for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]
        
        return sorted(recent_alerts, key=lambda x: x['timestamp'], reverse=True)
    
    def get_metric_history(self, metric_name: str, hours: int = 1) -> List[Dict[str, Any]]:
        """Get metric history"""
        if metric_name not in self.metrics_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            {
                'value': entry['value'],
                'timestamp': entry['timestamp'].isoformat()
            }
            for entry in self.metrics_history[metric_name]
            if entry['timestamp'] >= cutoff_time
        ]
    
    def add_alert_rule(self, rule: AlertRule):
        """Add or update an alert rule"""
        self.alert_rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.rule_id}")
    
    def remove_alert_rule(self, rule_id: str):
        """Remove an alert rule"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
    
    def enable_alert_rule(self, rule_id: str, enabled: bool):
        """Enable or disable an alert rule"""
        if rule_id in self.alert_rules:
            self.alert_rules[rule_id].enabled = enabled
            logger.info(f"Alert rule {rule_id} {'enabled' if enabled else 'disabled'}")


# Example usage and testing
if __name__ == "__main__":
    # Test monitoring service
    monitoring = MonitoringService()
    
    print("📊 Monitoring Service Demo")
    print("=" * 50)
    
    # Start monitoring
    monitoring.start_monitoring()
    
    try:
        # Wait for some monitoring cycles
        print("Collecting metrics...")
        time.sleep(10)
        
        # Get monitoring status
        status = monitoring.get_monitoring_status()
        print(f"\nMonitoring Status:")
        print(f"  Active: {status['monitoring_active']}")
        print(f"  Uptime: {status['uptime_formatted']}")
        print(f"  Monitoring cycles: {status['monitoring_cycles']}")
        print(f"  Alert rules: {status['alert_rules_count']}")
        print(f"  Active alerts: {status['active_alerts_count']}")
        
        # Get some metric history
        memory_history = monitoring.get_metric_history('memory_usage_percent', hours=1)
        if memory_history:
            print(f"\nRecent Memory Usage:")
            for entry in memory_history[-3:]:  # Last 3 entries
                print(f"  {entry['timestamp']}: {entry['value']:.1f}%")
        
        # Check for active alerts
        active_alerts = monitoring.get_active_alerts()
        if active_alerts:
            print(f"\nActive Alerts:")
            for alert in active_alerts:
                print(f"  {alert['severity']}: {alert['title']}")
                print(f"    {alert['message']}")
        else:
            print(f"\nNo active alerts")
        
        # Get alert history
        alert_history = monitoring.get_alert_history(hours=1)
        print(f"\nAlert History (last hour): {len(alert_history)} alerts")
        
        # Add a custom alert rule
        custom_rule = AlertRule(
            rule_id="custom_test_rule",
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.INFO,
            metric_name="cpu_usage_percent",
            threshold=50.0,
            comparison="greater_than",
            time_window_minutes=1,
            min_occurrences=1,
            component="test",
            message_template="Test alert: CPU usage is {current_value:.1f}%"
        )
        
        monitoring.add_alert_rule(custom_rule)
        print(f"\nAdded custom alert rule: {custom_rule.rule_id}")
        
    finally:
        # Stop monitoring
        monitoring.stop_monitoring()
    
    print("\n✅ Monitoring service demo completed")