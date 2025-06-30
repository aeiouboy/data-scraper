export interface Category {
  id: string;
  name: string;
  slug: string;
  parent_id?: string;
  level: number;
  path: string;
  product_count: number;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryHealth {
  category_id: string;
  category_name: string;
  category_path: string;
  health_score: number;
  status: 'healthy' | 'warning' | 'critical';
  total_products: number;
  active_products: number;
  stale_products: number;
  missing_price_products: number;
  out_of_stock_products: number;
  last_scrape_success_rate: number;
  avg_price_staleness_hours: number;
  issues: CategoryIssue[];
  recommendations: string[];
  last_checked: string;
  trend: 'improving' | 'stable' | 'declining';
}

export interface CategoryIssue {
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: 'stale_data' | 'low_success_rate' | 'missing_prices' | 'high_out_of_stock' | 'inactive_products';
  message: string;
  affected_count: number;
  threshold_exceeded: number;
}

export interface CategoryChange {
  id: string;
  category_id: string;
  category_name: string;
  change_type: 'price_increase' | 'price_decrease' | 'new_product' | 'product_removed' | 'back_in_stock' | 'out_of_stock';
  product_id?: string;
  product_name?: string;
  product_sku?: string;
  old_value?: string | number;
  new_value?: string | number;
  change_percentage?: number;
  detected_at: string;
  processed: boolean;
}

export interface CategoryStats {
  category_id: string;
  category_name: string;
  total_products: number;
  active_products: number;
  average_price: number;
  min_price: number;
  max_price: number;
  price_range: {
    min: number;
    max: number;
    currency: string;
  };
  brand_distribution: BrandCount[];
  price_distribution: PriceRange[];
  stock_status: StockStatus;
  last_updated: string;
}

export interface BrandCount {
  brand: string;
  count: number;
  percentage: number;
}

export interface PriceRange {
  range: string;
  min: number;
  max: number;
  count: number;
  percentage: number;
}

export interface StockStatus {
  in_stock: number;
  out_of_stock: number;
  limited_stock: number;
  unknown: number;
}

export interface CategoryMonitoringJob {
  id: string;
  category_id: string;
  category_name: string;
  job_type: 'health_check' | 'price_monitoring' | 'inventory_check' | 'full_scan';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  products_checked?: number;
  issues_found?: number;
  changes_detected?: number;
  error_message?: string;
  next_run_at?: string;
  created_by: string;
  metadata?: Record<string, any>;
}

export interface CategoryMonitoringConfig {
  category_id: string;
  enabled: boolean;
  check_interval_hours: number;
  price_change_threshold_percentage: number;
  health_score_threshold: number;
  notifications: NotificationConfig;
  monitoring_rules: MonitoringRule[];
}

export interface NotificationConfig {
  email_enabled: boolean;
  email_recipients: string[];
  webhook_enabled: boolean;
  webhook_url?: string;
  slack_enabled: boolean;
  slack_channel?: string;
  notification_types: NotificationType[];
}

export type NotificationType = 
  | 'price_drop'
  | 'price_increase'
  | 'out_of_stock'
  | 'back_in_stock'
  | 'new_product'
  | 'health_degradation'
  | 'scraping_failure';

export interface MonitoringRule {
  id: string;
  rule_type: 'price_change' | 'inventory' | 'data_freshness' | 'success_rate';
  condition: 'greater_than' | 'less_than' | 'equals' | 'between';
  threshold_value: number;
  threshold_unit?: string;
  action: 'notify' | 'escalate' | 'auto_rescrape';
  active: boolean;
}

export interface CategoryHealthTrend {
  category_id: string;
  timestamp: string;
  health_score: number;
  total_products: number;
  active_products: number;
  success_rate: number;
  avg_staleness_hours: number;
}

export interface CategoryAlert {
  id: string;
  category_id: string;
  category_name: string;
  alert_type: NotificationType;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  details?: Record<string, any>;
  created_at: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  resolved: boolean;
  resolved_at?: string;
}

export interface CategoryComparison {
  base_category: CategoryStats;
  compare_categories: CategoryStats[];
  metrics: ComparisonMetric[];
  insights: string[];
  generated_at: string;
}

export interface ComparisonMetric {
  metric_name: string;
  base_value: number;
  compare_values: { category_id: string; value: number; difference: number; percentage_change: number }[];
  unit?: string;
  higher_is_better: boolean;
}

export interface CategoryFilter {
  search?: string;
  parent_id?: string;
  level?: number;
  active?: boolean;
  health_status?: ('healthy' | 'warning' | 'critical')[];
  min_products?: number;
  max_products?: number;
  sort_by?: 'name' | 'product_count' | 'health_score' | 'last_updated';
  sort_order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export interface CategoryTreeNode extends Category {
  children?: CategoryTreeNode[];
  expanded?: boolean;
  health?: CategoryHealth;
}