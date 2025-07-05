import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback } from 'react';
import axios from 'axios';

// Types
interface CategoryHealth {
  category_id: string;
  category_name: string;
  health_score: number;
  total_products: number;
  active_products: number;
  inactive_products: number;
  avg_price: number;
  last_updated: string;
  issues: CategoryIssue[];
}

interface CategoryIssue {
  type: 'high_inactive_rate' | 'price_anomaly' | 'low_inventory' | 'stale_data';
  severity: 'low' | 'medium' | 'high';
  message: string;
  affected_products: number;
}

interface CategoryChange {
  id: string;
  category_id: string;
  category_name: string;
  change_type: 'price_increase' | 'price_decrease' | 'new_products' | 'discontinued';
  change_date: string;
  details: {
    previous_value?: number;
    current_value?: number;
    product_count?: number;
    percentage_change?: number;
  };
}

interface CategoryStats {
  category_id: string;
  category_name: string;
  metrics: {
    total_products: number;
    avg_price: number;
    price_range: {
      min: number;
      max: number;
    };
    inventory_health: number;
    update_frequency: number;
    top_brands: Array<{
      brand: string;
      product_count: number;
    }>;
  };
  trends: {
    price_trend: 'increasing' | 'decreasing' | 'stable';
    inventory_trend: 'increasing' | 'decreasing' | 'stable';
    demand_indicator: number;
  };
}

interface MonitoringTrigger {
  category_id: string;
  trigger_type: 'price_threshold' | 'inventory_alert' | 'update_frequency';
  threshold_value: number;
  comparison: 'above' | 'below' | 'equals';
  notification_method: 'email' | 'webhook' | 'in_app';
  is_active: boolean;
}

interface MonitoringFilters {
  healthScoreThreshold?: number;
  hasIssues?: boolean;
  categories?: string[];
  sortBy?: 'health_score' | 'total_products' | 'last_updated';
  sortOrder?: 'asc' | 'desc';
}

interface TimeRange {
  start: Date;
  end: Date;
  preset?: '24h' | '7d' | '30d' | 'custom';
}

// API client configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Type for retailer stats from API
interface RetailerStatsData {
  active: number;
  inactive: number;
  total: number;
  total_products?: number;
}

// API functions
const fetchCategoryHealth = async (filters?: MonitoringFilters): Promise<CategoryHealth[]> => {
  // Note: The backend doesn't have a unified category health endpoint
  // We'll need to fetch from multiple endpoints and combine the data
  const [statsResponse, changesResponse] = await Promise.all([
    apiClient.get('/categories/stats'),
    apiClient.get('/categories/changes', { params: { days: 1 } })
  ]);
  
  // Transform the data to match CategoryHealth interface
  const stats = statsResponse.data.retailer_stats || {};
  // const changes = changesResponse.data.changes || [];
  
  const healthData: CategoryHealth[] = [];
  
  for (const [retailerCode, retailerStats] of Object.entries(stats as Record<string, RetailerStatsData>)) {
    // Calculate health score based on available metrics
    const activeRate = retailerStats.active / retailerStats.total;
    const healthScore = activeRate * 100;
    
    // Determine issues
    const issues: CategoryIssue[] = [];
    if (activeRate < 0.8) {
      issues.push({
        type: 'high_inactive_rate',
        severity: activeRate < 0.5 ? 'high' : 'medium',
        message: `${Math.round((1 - activeRate) * 100)}% of categories are inactive`,
        affected_products: retailerStats.inactive
      });
    }
    
    healthData.push({
      category_id: retailerCode,
      category_name: retailerCode,
      health_score: healthScore,
      total_products: retailerStats.total_products || 0,
      active_products: retailerStats.active || 0,
      inactive_products: retailerStats.inactive || 0,
      avg_price: 0, // Not available in current API
      last_updated: new Date().toISOString(),
      issues
    });
  }
  
  return healthData;
};

const fetchCategoryChanges = async (
  timeRange: TimeRange,
  categoryId?: string
): Promise<CategoryChange[]> => {
  // Calculate days difference
  const days = Math.ceil((timeRange.end.getTime() - timeRange.start.getTime()) / (1000 * 60 * 60 * 24));
  
  const params = {
    days: days,
    retailer_code: categoryId, // Using retailer_code instead of category_id
  };
  const response = await apiClient.get('/categories/changes', { params });
  
  // Transform the response to match CategoryChange interface
  const changes = response.data.changes || [];
  return changes.map((change: any) => ({
    id: change.id || `${change.category_id}_${change.change_date}`,
    category_id: change.category_id,
    category_name: change.category_name || change.category_id,
    change_type: change.change_type,
    change_date: change.change_date || change.detected_at,
    details: change.details || {
      previous_value: change.old_value,
      current_value: change.new_value,
      product_count: change.product_count,
      percentage_change: change.percentage_change
    }
  }));
};

const fetchCategoryStats = async (categoryId: string): Promise<CategoryStats> => {
  // Fetch from multiple endpoints to build comprehensive stats
  const [healthResponse, statsResponse] = await Promise.all([
    apiClient.get(`/categories/health/${categoryId}`),
    apiClient.get('/categories/stats', { params: { retailer_code: categoryId } })
  ]);
  
  const health = healthResponse.data;
  const stats = statsResponse.data.retailer_stats?.[categoryId] || {};
  
  // Transform to CategoryStats interface
  return {
    category_id: categoryId,
    category_name: categoryId,
    metrics: {
      total_products: stats.total_products || 0,
      avg_price: health.avg_price || 0,
      price_range: {
        min: health.min_price || 0,
        max: health.max_price || 0
      },
      inventory_health: health.inventory_health || 0,
      update_frequency: health.update_frequency || 0,
      top_brands: health.top_brands || []
    },
    trends: {
      price_trend: health.price_trend || 'stable',
      inventory_trend: health.inventory_trend || 'stable',
      demand_indicator: health.demand_indicator || 0
    }
  };
};

const fetchMonitoringTriggers = async (categoryId?: string): Promise<MonitoringTrigger[]> => {
  // The backend doesn't have a triggers endpoint, return empty array for now
  // This would need to be implemented in the backend
  console.warn('Monitoring triggers endpoint not implemented in backend');
  return [];
};

const createMonitoringTrigger = async (trigger: Omit<MonitoringTrigger, 'is_active'>): Promise<MonitoringTrigger> => {
  // The backend doesn't have a triggers endpoint
  console.warn('Create monitoring trigger endpoint not implemented in backend');
  throw new Error('Monitoring triggers not implemented');
};

const updateMonitoringTrigger = async (
  triggerId: string,
  updates: Partial<MonitoringTrigger>
): Promise<MonitoringTrigger> => {
  // The backend doesn't have a triggers endpoint
  console.warn('Update monitoring trigger endpoint not implemented in backend');
  throw new Error('Monitoring triggers not implemented');
};

const deleteMonitoringTrigger = async (triggerId: string): Promise<void> => {
  // The backend doesn't have a triggers endpoint
  console.warn('Delete monitoring trigger endpoint not implemented in backend');
  throw new Error('Monitoring triggers not implemented');
};

const triggerManualMonitoring = async (categoryId: string): Promise<{ job_id: string; status: string }> => {
  // Use the category monitor endpoint
  const response = await apiClient.post('/categories/monitor', null, {
    params: { retailer_code: categoryId }
  });
  return {
    job_id: response.data.job_id || 'manual-trigger',
    status: 'started'
  };
};

// Custom hook
export const useCategoryMonitoring = (initialFilters?: MonitoringFilters) => {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<MonitoringFilters>(initialFilters || {});
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<TimeRange>({
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
    end: new Date(),
    preset: '7d',
  });

  // Queries
  const {
    data: categoryHealth,
    isLoading: isLoadingHealth,
    error: healthError,
    refetch: refetchHealth,
  } = useQuery({
    queryKey: ['categoryHealth', filters],
    queryFn: () => fetchCategoryHealth(filters),
    refetchInterval: 60000, // Refetch every minute
    staleTime: 30000, // Consider data stale after 30 seconds
  });

  const {
    data: categoryChanges,
    isLoading: isLoadingChanges,
    error: changesError,
    refetch: refetchChanges,
  } = useQuery({
    queryKey: ['categoryChanges', timeRange, selectedCategory],
    queryFn: () => fetchCategoryChanges(timeRange, selectedCategory || undefined),
    enabled: true,
  });

  const {
    data: categoryStats,
    isLoading: isLoadingStats,
    error: statsError,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ['categoryStats', selectedCategory],
    queryFn: () => fetchCategoryStats(selectedCategory!),
    enabled: !!selectedCategory,
  });

  const {
    data: monitoringTriggers,
    isLoading: isLoadingTriggers,
    error: triggersError,
    refetch: refetchTriggers,
  } = useQuery({
    queryKey: ['monitoringTriggers', selectedCategory],
    queryFn: () => fetchMonitoringTriggers(selectedCategory || undefined),
  });

  // Mutations
  const createTriggerMutation = useMutation({
    mutationFn: createMonitoringTrigger,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoringTriggers'] });
    },
  });

  const updateTriggerMutation = useMutation({
    mutationFn: ({ triggerId, updates }: { triggerId: string; updates: Partial<MonitoringTrigger> }) =>
      updateMonitoringTrigger(triggerId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoringTriggers'] });
    },
  });

  const deleteTriggerMutation = useMutation({
    mutationFn: deleteMonitoringTrigger,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoringTriggers'] });
    },
  });

  const triggerMonitoringMutation = useMutation({
    mutationFn: triggerManualMonitoring,
    onSuccess: () => {
      // Invalidate related queries after triggering monitoring
      queryClient.invalidateQueries({ queryKey: ['categoryHealth'] });
      queryClient.invalidateQueries({ queryKey: ['categoryChanges'] });
      queryClient.invalidateQueries({ queryKey: ['categoryStats'] });
    },
  });

  // Utility functions
  const updateFilters = useCallback((newFilters: Partial<MonitoringFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  const updateTimeRange = useCallback((newTimeRange: Partial<TimeRange>) => {
    setTimeRange(prev => {
      const updated = { ...prev, ...newTimeRange };
      
      // Handle preset changes
      if (newTimeRange.preset && newTimeRange.preset !== 'custom') {
        const now = new Date();
        switch (newTimeRange.preset) {
          case '24h':
            updated.start = new Date(now.getTime() - 24 * 60 * 60 * 1000);
            updated.end = now;
            break;
          case '7d':
            updated.start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            updated.end = now;
            break;
          case '30d':
            updated.start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
            updated.end = now;
            break;
        }
      }
      
      return updated;
    });
  }, []);

  const getCategoryHealthScore = useCallback((categoryId: string): number | null => {
    const category = categoryHealth?.find(c => c.category_id === categoryId);
    return category?.health_score || null;
  }, [categoryHealth]);

  const getCategoriesWithIssues = useCallback((): CategoryHealth[] => {
    return categoryHealth?.filter(c => c.issues.length > 0) || [];
  }, [categoryHealth]);

  const getHighSeverityIssues = useCallback((): CategoryIssue[] => {
    const allIssues: CategoryIssue[] = [];
    categoryHealth?.forEach(category => {
      allIssues.push(...category.issues.filter(issue => issue.severity === 'high'));
    });
    return allIssues;
  }, [categoryHealth]);

  const refreshAll = useCallback(async () => {
    await Promise.all([
      refetchHealth(),
      refetchChanges(),
      selectedCategory && refetchStats(),
      refetchTriggers(),
    ]);
  }, [refetchHealth, refetchChanges, refetchStats, refetchTriggers, selectedCategory]);

  // Aggregate statistics
  const aggregateStats = {
    totalCategories: categoryHealth?.length || 0,
    categoriesWithIssues: getCategoriesWithIssues().length,
    averageHealthScore: categoryHealth ? categoryHealth.reduce((sum, c) => sum + c.health_score, 0) / categoryHealth.length : 0,
    totalProducts: categoryHealth?.reduce((sum, c) => sum + c.total_products, 0) || 0,
    highSeverityIssues: getHighSeverityIssues().length,
  };

  return {
    // State
    filters,
    selectedCategory,
    timeRange,
    
    // Data
    categoryHealth,
    categoryChanges,
    categoryStats,
    monitoringTriggers,
    aggregateStats,
    
    // Loading states
    isLoading: isLoadingHealth || isLoadingChanges || isLoadingStats || isLoadingTriggers,
    isLoadingHealth,
    isLoadingChanges,
    isLoadingStats,
    isLoadingTriggers,
    
    // Errors
    error: healthError || changesError || statsError || triggersError,
    healthError,
    changesError,
    statsError,
    triggersError,
    
    // Actions
    setSelectedCategory,
    updateFilters,
    updateTimeRange,
    refreshAll,
    
    // Trigger management
    createTrigger: createTriggerMutation.mutate,
    updateTrigger: updateTriggerMutation.mutate,
    deleteTrigger: deleteTriggerMutation.mutate,
    triggerMonitoring: triggerMonitoringMutation.mutate,
    
    // Mutation states
    isCreatingTrigger: createTriggerMutation.isPending,
    isUpdatingTrigger: updateTriggerMutation.isPending,
    isDeletingTrigger: deleteTriggerMutation.isPending,
    isTriggeringMonitoring: triggerMonitoringMutation.isPending,
    
    // Utility functions
    getCategoryHealthScore,
    getCategoriesWithIssues,
    getHighSeverityIssues,
  };
};

// Export types for use in components
export type {
  CategoryHealth,
  CategoryIssue,
  CategoryChange,
  CategoryStats,
  MonitoringTrigger,
  MonitoringFilters,
  TimeRange,
};