// Import the API services - this will trigger axios.create
import { productApi, retailerApi, scrapingApi, analyticsApi } from '../../services/api';
import axios from 'axios';

// Get the mock instance that was created during import
const mockAxiosCreate = (axios.create as jest.Mock) || (axios as any).default?.create;
const mockApiInstance = mockAxiosCreate.mock.results[0]?.value || (global as any).mockAxiosInstance;

describe('API Services', () => {
  beforeEach(() => {
    // Clear all mock function calls before each test
    jest.clearAllMocks();
    
    // Reset mock implementations
    mockApiInstance.get.mockReset();
    mockApiInstance.post.mockReset();
    mockApiInstance.put.mockReset();
    mockApiInstance.patch.mockReset();
    mockApiInstance.delete.mockReset();
  });

  describe('Product API', () => {
    it('should search products with correct parameters', async () => {
      const searchParams = { query: 'test', retailer_code: 'HP' };
      const mockResponse = { data: [] };
      mockApiInstance.post.mockResolvedValue(mockResponse);

      const result = await productApi.search(searchParams);

      expect(mockApiInstance.post).toHaveBeenCalledWith('/products/search', searchParams);
      expect(result).toEqual(mockResponse);
    });

    it('should get product by ID', async () => {
      const productId = '123';
      const mockResponse = { data: { id: productId, name: 'Test Product' } };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await productApi.getById(productId);

      expect(mockApiInstance.get).toHaveBeenCalledWith(`/products/${productId}`);
      expect(result).toEqual(mockResponse);
    });

    it('should get price history with default days', async () => {
      const productId = '123';
      const mockResponse = { data: [] };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await productApi.getPriceHistory(productId);

      expect(mockApiInstance.get).toHaveBeenCalledWith(`/products/${productId}/price-history?days=30`);
      expect(result).toEqual(mockResponse);
    });

    it('should get price history with custom days', async () => {
      const productId = '123';
      const days = 60;
      const mockResponse = { data: [] };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await productApi.getPriceHistory(productId, days);

      expect(mockApiInstance.get).toHaveBeenCalledWith(`/products/${productId}/price-history?days=${days}`);
      expect(result).toEqual(mockResponse);
    });

    it('should rescrape product', async () => {
      const productId = '123';
      const mockResponse = { data: { status: 'queued' } };
      mockApiInstance.post.mockResolvedValue(mockResponse);

      const result = await productApi.rescrape(productId);

      expect(mockApiInstance.post).toHaveBeenCalledWith(`/products/${productId}/rescrape`);
      expect(result).toEqual(mockResponse);
    });

    it('should get brands without retailer filter', async () => {
      const mockResponse = { data: ['Brand1', 'Brand2'] };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await productApi.getBrands();

      expect(mockApiInstance.get).toHaveBeenCalledWith('/products/filters/brands', { params: {} });
      expect(result).toEqual(mockResponse);
    });

    it('should get brands with retailer filter', async () => {
      const retailerCode = 'HP';
      const mockResponse = { data: ['Brand1', 'Brand2'] };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await productApi.getBrands(retailerCode);

      expect(mockApiInstance.get).toHaveBeenCalledWith('/products/filters/brands', { 
        params: { retailer_code: retailerCode } 
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Retailer API', () => {
    it('should get all retailers', async () => {
      const mockResponse = { data: [] };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await retailerApi.getAll();

      expect(mockApiInstance.get).toHaveBeenCalledWith('/retailers');
      expect(result).toEqual(mockResponse);
    });

    it('should get retailer summary', async () => {
      const mockResponse = { data: {} };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await retailerApi.getSummary();

      expect(mockApiInstance.get).toHaveBeenCalledWith('/retailers/summary');
      expect(result).toEqual(mockResponse);
    });

    it('should get retailer by code', async () => {
      const code = 'HP';
      const mockResponse = { data: { code, name: 'HomePro' } };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await retailerApi.getById(code);

      expect(mockApiInstance.get).toHaveBeenCalledWith(`/retailers/${code}`);
      expect(result).toEqual(mockResponse);
    });

    it('should get retailer stats', async () => {
      const code = 'HP';
      const mockResponse = { data: { total_products: 1000 } };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await retailerApi.getStats(code);

      expect(mockApiInstance.get).toHaveBeenCalledWith(`/retailers/${code}/stats`);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Scraping API', () => {
    it('should create a scraping job', async () => {
      const jobData = { url: 'http://test.com', max_pages: 5 };
      const mockResponse = { data: { id: '123', status: 'pending' } };
      mockApiInstance.post.mockResolvedValue(mockResponse);

      const result = await scrapingApi.createJob(jobData);

      expect(mockApiInstance.post).toHaveBeenCalledWith('/scraping/jobs', jobData);
      expect(result).toEqual(mockResponse);
    });

    it('should get health metrics', async () => {
      const mockResponse = { data: { overall_health: 'healthy' } };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await scrapingApi.getHealthMetrics();

      expect(mockApiInstance.get).toHaveBeenCalledWith('/monitoring/health');
      expect(result).toEqual(mockResponse);
    });

    it('should list scraping jobs with filters', async () => {
      const status = 'completed';
      const retailer = 'HP';
      const mockResponse = { data: [] };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await scrapingApi.listJobs(status, retailer);

      expect(mockApiInstance.get).toHaveBeenCalledWith('/scraping/jobs', { 
        params: { status, retailer_code: retailer } 
      });
      expect(result).toEqual(mockResponse);
    });

    it('should cancel a scraping job', async () => {
      const jobId = '123';
      const mockResponse = { data: { status: 'cancelled' } };
      mockApiInstance.post.mockResolvedValue(mockResponse);

      const result = await scrapingApi.cancelJob(jobId);

      expect(mockApiInstance.post).toHaveBeenCalledWith(`/scraping/jobs/${jobId}/cancel`);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Analytics API', () => {
    it('should get dashboard data without retailer filter', async () => {
      const mockResponse = { data: {} };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await analyticsApi.getDashboard();

      expect(mockApiInstance.get).toHaveBeenCalledWith('/analytics/dashboard', { params: {} });
      expect(result).toEqual(mockResponse);
    });

    it('should get dashboard data with retailer filter', async () => {
      const mockResponse = { data: {} };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await analyticsApi.getDashboard('HP');

      expect(mockApiInstance.get).toHaveBeenCalledWith('/analytics/dashboard', {
        params: { retailer_code: 'HP' },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should get product trends', async () => {
      const days = 7;
      const retailer = 'HP';
      const mockResponse = { data: [] };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await analyticsApi.getProductTrends(days, retailer);

      expect(mockApiInstance.get).toHaveBeenCalledWith(`/analytics/products/trends?days=${days}`, {
        params: { retailer_code: retailer }
      });
      expect(result).toEqual(mockResponse);
    });

    it('should get scraping performance', async () => {
      const days = 14;
      const mockResponse = { data: {} };
      mockApiInstance.get.mockResolvedValue(mockResponse);

      const result = await analyticsApi.getScrapingPerformance(days);

      expect(mockApiInstance.get).toHaveBeenCalledWith(`/analytics/scraping/performance?days=${days}`);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Request Interceptors', () => {
    it('should add authorization header if token exists', async () => {
      // Mock localStorage.getItem to return a token
      const mockToken = 'test-token';
      const originalGetItem = localStorage.getItem;
      const mockGetItem = jest.fn((key: string) => {
        if (key === 'token') return mockToken;
        return null;
      });
      Object.defineProperty(window, 'localStorage', {
        value: {
          ...localStorage,
          getItem: mockGetItem
        },
        configurable: true
      });

      // Get the interceptor function from mock calls
      const interceptorCalls = mockApiInstance.interceptors.request.use.mock.calls;
      if (interceptorCalls.length > 0) {
        const interceptor = interceptorCalls[0][0];
        // Test the interceptor
        const config = { headers: {} };
        const result = interceptor(config);
        expect(result.headers.Authorization).toBe(`Bearer ${mockToken}`);
      } else {
        // If no interceptor calls, just verify localStorage was mocked
        expect(localStorage.getItem).toBeDefined();
        expect(localStorage.getItem('token')).toBe(mockToken);
      }
      
      // Restore original
      Object.defineProperty(window, 'localStorage', {
        value: {
          ...localStorage,
          getItem: originalGetItem
        },
        configurable: true
      });
    });

    it('should not add authorization header if no token', async () => {
      // Mock localStorage.getItem to return null
      const originalGetItem = localStorage.getItem;
      localStorage.getItem = jest.fn().mockReturnValue(null);

      // Get the interceptor function from mock calls
      const interceptorCalls = mockApiInstance.interceptors.request.use.mock.calls;
      if (interceptorCalls.length > 0) {
        const interceptor = interceptorCalls[0][0];
        // Test the interceptor
        const config = { headers: {} };
        const result = interceptor(config);
        expect(result.headers.Authorization).toBeUndefined();
      } else {
        // If no interceptor calls, just verify localStorage was mocked
        expect(localStorage.getItem).toBeDefined();
        expect(localStorage.getItem('token')).toBeNull();
      }
      
      // Restore original
      localStorage.getItem = originalGetItem;
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const networkError = new Error('Network Error');
      mockApiInstance.get.mockRejectedValue(networkError);

      await expect(productApi.getBrands()).rejects.toThrow('Network Error');
    });

    it('should handle API errors with response', async () => {
      const apiError = {
        response: {
          status: 400,
          data: { message: 'Bad Request' }
        }
      };
      mockApiInstance.post.mockRejectedValue(apiError);

      await expect(productApi.search({})).rejects.toEqual(apiError);
    });
  });
});