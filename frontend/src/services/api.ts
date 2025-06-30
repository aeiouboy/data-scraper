import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add retry functionality
let retryCount = 0;
const MAX_RETRY_COUNT = 3;
const RETRY_DELAY = 1000; // Start with 1 second

// Response interceptor with retry logic
api.interceptors.response.use(
  (response) => {
    // Reset retry count on success
    retryCount = 0;
    return response;
  },
  async (error) => {
    const config = error.config;
    
    // Handle unauthorized
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
      return Promise.reject(error);
    }
    
    // Retry logic for network errors and 5xx errors
    const shouldRetry = !error.response || (error.response.status >= 500 && error.response.status < 600);
    
    if (shouldRetry && retryCount < MAX_RETRY_COUNT && config && !config._retry) {
      retryCount++;
      config._retry = true;
      
      // Exponential backoff
      const delay = RETRY_DELAY * Math.pow(2, retryCount - 1);
      
      console.log(`Retrying request (attempt ${retryCount}/${MAX_RETRY_COUNT}) after ${delay}ms...`);
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
      
      // Retry the request
      return api(config);
    }
    
    // Reset retry count after max retries
    if (retryCount >= MAX_RETRY_COUNT) {
      retryCount = 0;
    }
    
    return Promise.reject(error);
  }
);

// Multi-Retailer Product APIs
export const productApi = {
  search: (params: any) => api.post('/products/search', params),
  getById: (id: string) => api.get(`/products/${id}`),
  getPriceHistory: (id: string, days: number = 30) => 
    api.get(`/products/${id}/price-history?days=${days}`),
  rescrape: (id: string) => api.post(`/products/${id}/rescrape`),
  getBrands: (retailerCode?: string) => api.get('/products/filters/brands', { 
    params: retailerCode ? { retailer_code: retailerCode } : {} 
  }),
  getCategories: (retailerCode?: string) => api.get('/products/filters/categories', { 
    params: retailerCode ? { retailer_code: retailerCode } : {} 
  }),
  getProductMatches: (productId: string) => api.get(`/products/${productId}/matches`),
  getPriceComparisons: (params: any) => api.get('/products/price-comparisons', { params }),
  getByRetailer: (retailerCode: string, params: any) => 
    api.post('/products/search', { ...params, retailer_code: retailerCode }),
};

// Retailer Management APIs
export const retailerApi = {
  getAll: () => api.get('/retailers'),
  getById: (code: string) => api.get(`/retailers/${code}`),
  getStats: (code: string) => api.get(`/retailers/${code}/stats`),
  getSummary: () => api.get('/retailers/summary'),
  getMonitoringDistribution: () => api.get('/retailers/monitoring-distribution'),
  getCategories: (code: string) => api.get(`/retailers/${code}/categories`),
};

// Multi-Retailer Scraping APIs
export const scrapingApi = {
  createJob: (data: any) => api.post('/scraping/jobs', data),
  createMultiRetailerJob: (retailers: string[], options: any) => 
    api.post('/scraping/jobs/multi-retailer', { retailers, ...options }),
  listJobs: (status?: string, retailer?: string) => 
    api.get('/scraping/jobs', { params: { status, retailer_code: retailer } }),
  getJob: (id: string) => api.get(`/scraping/jobs/${id}`),
  cancelJob: (id: string) => api.post(`/scraping/jobs/${id}/cancel`),
  discoverUrls: (url: string, maxPages: number = 5) => 
    api.post('/scraping/discover', { url, max_pages: maxPages }),
  getRetailerProgress: () => api.get('/scraping/progress/retailers'),
  getMonitoringSchedule: () => api.get('/scraping/monitoring/schedule'),
  submitJob: (data: any) => api.post('/scraping/jobs', data),
  getJobs: () => api.get('/scraping/jobs'),
  // Monitoring endpoints
  getHealthMetrics: () => api.get('/monitoring/health'),
  getRetailerHealth: () => api.get('/monitoring/retailers'),
  getJobMetrics: () => api.get('/monitoring/metrics'),
  getAlerts: () => api.get('/monitoring/alerts'),
  // Note: Category health is accessed via categoryApi.getHealth() or retailer-specific endpoints
};

// Enhanced Analytics APIs
export const analyticsApi = {
  getDashboard: (retailer?: string) => api.get('/analytics/dashboard', { 
    params: retailer ? { retailer_code: retailer } : {} 
  }),
  getMultiRetailerDashboard: () => api.get('/analytics/dashboard/multi-retailer'),
  getProductTrends: (days: number = 30, retailer?: string) => 
    api.get(`/analytics/products/trends?days=${days}`, {
      params: retailer ? { retailer_code: retailer } : {}
    }),
  getScrapingPerformance: (days: number = 30) => 
    api.get(`/analytics/scraping/performance?days=${days}`),
  getRetailerComparison: () => api.get('/analytics/retailers/comparison'),
  getPriceDistribution: (retailer?: string) => api.get('/analytics/prices/distribution', {
    params: retailer ? { retailer_code: retailer } : {}
  }),
  getMonitoringEfficiency: () => api.get('/analytics/monitoring/efficiency'),
};

// Price Comparison APIs
export const priceComparisonApi = {
  getTopSavings: (limit: number = 50) => api.get(`/price-comparisons/top-savings?limit=${limit}`),
  getByCategory: (category: string) => api.get(`/price-comparisons/category/${category}`),
  getRetailerCompetitiveness: () => api.get('/price-comparisons/retailer-competitiveness'),
  getProductMatch: (productId: string) => api.get(`/price-comparisons/product/${productId}`),
  createMatch: (masterProductId: string, matchedProductIds: string[]) => 
    api.post('/price-comparisons/matches', { master_product_id: masterProductId, matched_product_ids: matchedProductIds }),
  refreshMatches: () => api.post('/price-comparisons/refresh'),
};

// Config APIs
export const configApi = {
  get: () => api.get('/config'),
  update: (data: any) => api.patch('/config', data),
  reset: () => api.post('/config/reset'),
};

// Category Monitoring APIs
export const categoryApi = {
  // Get health for specific retailer (no general health endpoint)
  getHealth: (retailerCode: string) => api.get(`/categories/health/${retailerCode}`),
  
  // Get category changes
  getChanges: (params?: { 
    retailer_code?: string; 
    days?: number; 
    change_type?: string;
  }) => api.get('/categories/changes', { params }),
  
  // Get category tree structure for a retailer
  getTree: (retailerCode: string) => api.get(`/categories/tree/${retailerCode}`),
  
  // Get category statistics
  getStats: (params?: {
    retailer_code?: string;
  }) => api.get('/categories/stats', { params }),
  
  // Trigger category monitoring
  triggerMonitor: (retailerCode?: string) => api.post('/categories/monitor', null, {
    params: retailerCode ? { retailer_code: retailerCode } : {}
  }),
  
  // Trigger category discovery
  triggerDiscovery: (params: {
    retailer_code: string;
    max_depth?: number;
    max_categories?: number;
  }) => api.get('/categories/discover', { params }),
  
  // Verify category validity
  verifyCategory: (categoryId: string) => api.post(`/categories/verify/${categoryId}`),
  
  // Activate/deactivate categories
  activateCategory: (categoryId: string) => api.put(`/categories/${categoryId}/activate`),
  deactivateCategory: (categoryId: string) => api.put(`/categories/${categoryId}/deactivate`),
  
  // Import categories
  importCategories: (retailerCode: string, categories: any[]) => 
    api.post('/categories/import', { retailer_code: retailerCode, categories }),
};

// Schedule APIs
export const scheduleApi = {
  // Get all schedules
  getAll: (params?: { task_type?: string; enabled?: boolean }) => 
    api.get('/monitoring/schedules', { params }),
  
  // Get specific schedule
  getById: (id: string) => api.get(`/monitoring/schedules/${id}`),
  
  // Create new schedule
  create: (data: any) => api.post('/monitoring/schedules', data),
  
  // Update schedule
  update: (id: string, data: any) => api.put(`/monitoring/schedules/${id}`, data),
  
  // Toggle enable/disable
  toggle: (id: string, enabled: boolean) => 
    api.post(`/monitoring/schedules/${id}/toggle`, null, { params: { enabled } }),
  
  // Delete schedule
  delete: (id: string) => api.delete(`/monitoring/schedules/${id}`),
  
  // Get execution history
  getHistory: (id: string, params?: { limit?: number; offset?: number; status?: string }) => 
    api.get(`/monitoring/schedules/${id}/history`, { params }),
  
  // Run schedule now
  runNow: (id: string) => api.post(`/monitoring/schedules/${id}/run`),
  
  // Get statistics
  getStats: () => api.get('/monitoring/schedules/stats/summary'),
};

export default api;