import axios from 'axios';
import { productApi, retailerApi, scrapingApi, analyticsApi } from '../../services/api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('API Services', () => {
  let mockApiInstance: any;

  beforeEach(() => {
    // Create a mock instance with all axios methods
    mockApiInstance = {
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      patch: jest.fn(),
      delete: jest.fn(),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
    };

    mockedAxios.create.mockReturnValue(mockApiInstance);
  });

  afterEach(() => {
    jest.clearAllMocks();
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
  });
});