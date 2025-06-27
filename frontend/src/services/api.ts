import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Product APIs
export const productApi = {
  search: (params: any) => api.post('/products/search', params),
  getById: (id: string) => api.get(`/products/${id}`),
  getPriceHistory: (id: string, days: number = 30) => 
    api.get(`/products/${id}/price-history?days=${days}`),
  rescrape: (id: string) => api.post(`/products/${id}/rescrape`),
  getBrands: () => api.get('/products/filters/brands'),
  getCategories: () => api.get('/products/filters/categories'),
};

// Scraping APIs
export const scrapingApi = {
  createJob: (data: any) => api.post('/scraping/jobs', data),
  listJobs: (status?: string) => 
    api.get('/scraping/jobs', { params: { status } }),
  getJob: (id: string) => api.get(`/scraping/jobs/${id}`),
  cancelJob: (id: string) => api.post(`/scraping/jobs/${id}/cancel`),
  discoverUrls: (url: string, maxPages: number = 5) => 
    api.post('/scraping/discover', { url, max_pages: maxPages }),
};

// Analytics APIs
export const analyticsApi = {
  getDashboard: () => api.get('/analytics/dashboard'),
  getProductTrends: (days: number = 30) => 
    api.get(`/analytics/products/trends?days=${days}`),
  getScrapingPerformance: (days: number = 30) => 
    api.get(`/analytics/scraping/performance?days=${days}`),
};

// Config APIs
export const configApi = {
  get: () => api.get('/config'),
  update: (data: any) => api.patch('/config', data),
  reset: () => api.post('/config/reset'),
};

export default api;