import * as api from '../services/api';

export const setupRetailerApiMocks = () => {
  // Mock getCategories
  (api.retailerApi.getCategories as jest.Mock).mockResolvedValue({
    data: [
      { code: 'LIG', name: 'Lighting', product_count: 100 },
      { code: 'FUR', name: 'Furniture', product_count: 200 },
      { code: 'ELE', name: 'Electrical', product_count: 150 },
    ]
  });
  
  // Mock getMonitoringDistribution
  (api.retailerApi.getMonitoringDistribution as jest.Mock).mockResolvedValue({
    data: {
      HP: { total: 100, ultra_critical: 20, high_value: 30, standard: 40, low_priority: 10 },
      TWD: { total: 80, ultra_critical: 15, high_value: 25, standard: 30, low_priority: 10 },
    }
  });
  // Mock retailer API calls for RetailerContext
  (api.retailerApi.getAll as jest.Mock).mockResolvedValue({
    data: [
      { 
        code: 'HP', 
        name: 'HomePro', 
        base_url: 'https://homepro.co.th',
        market_position: 'Leader',
        estimated_products: 50000,
        is_active: true 
      },
      { 
        code: 'TWD', 
        name: 'Thai Watsadu', 
        base_url: 'https://thaiwatsadu.com',
        market_position: 'Major',
        estimated_products: 40000,
        is_active: true 
      },
      { 
        code: 'GH', 
        name: 'Global House', 
        base_url: 'https://globalhouse.co.th',
        market_position: 'Major',
        estimated_products: 35000,
        is_active: true 
      },
    ],
  });
  
  (api.retailerApi.getSummary as jest.Mock).mockResolvedValue({
    data: [
      { 
        code: 'HP', 
        name: 'HomePro',
        market_position: 'Leader',
        actual_products: 1000,
        in_stock_products: 900,
        priced_products: 950,
        avg_price: 500,
        min_price: 10,
        max_price: 10000,
        ultra_critical_count: 100,
        high_value_count: 200,
        standard_count: 600,
        low_priority_count: 100,
        category_coverage_percentage: 85,
        brand_coverage_percentage: 90,
        last_scraped_at: '2023-12-01T10:00:00Z'
      },
      { 
        code: 'TWD', 
        name: 'Thai Watsadu',
        market_position: 'Major',
        actual_products: 800,
        in_stock_products: 750,
        priced_products: 780,
        avg_price: 450,
        min_price: 15,
        max_price: 8000,
        ultra_critical_count: 80,
        high_value_count: 150,
        standard_count: 500,
        low_priority_count: 70,
        category_coverage_percentage: 80,
        brand_coverage_percentage: 85,
        last_scraped_at: '2023-12-01T09:00:00Z'
      },
    ],
  });
  
  // Mock other common retailer API methods
  (api.retailerApi.getById as jest.Mock).mockImplementation((code: string) => {
    const retailers = [
      { code: 'HP', name: 'HomePro', is_active: true },
      { code: 'TWD', name: 'Thai Watsadu', is_active: true },
      { code: 'GH', name: 'Global House', is_active: true },
    ];
    const retailer = retailers.find(r => r.code === code);
    return Promise.resolve({ data: retailer || null });
  });
  
  (api.retailerApi.getStats as jest.Mock).mockResolvedValue({
    data: {
      retailer_code: 'HP',
      retailer_name: 'HomePro',
      total_products: 1000,
      in_stock_products: 900,
      average_price: 500,
      unique_categories: 50,
      unique_brands: 100,
      price_distribution: {
        '0-100': 100,
        '100-500': 300,
        '500-1000': 300,
        '1000+': 300
      },
      top_categories: [
        { name: 'Tools', count: 200 },
        { name: 'Paint', count: 150 },
        { name: 'Electrical', count: 100 }
      ]
    }
  });
};

export const setupScrapingApiMocks = () => {
  (api.scrapingApi.createJob as jest.Mock).mockResolvedValue({
    data: {
      id: 'test-job-id',
      job_type: 'category',
      status: 'pending',
      created_at: new Date().toISOString()
    }
  });
  
  (api.scrapingApi.listJobs as jest.Mock).mockResolvedValue({
    data: {
      jobs: [],
      total: 0,
      active_jobs: 0,
      completed_jobs: 0,
      failed_jobs: 0
    }
  });
  
  (api.scrapingApi.getHealthMetrics as jest.Mock).mockResolvedValue({
    data: {
      overall_health: 'healthy',
      success_rate_24h: 95,
      success_rate_7d: 93,
      avg_response_time: 1.2,
      total_jobs_24h: 100,
      failed_jobs_24h: 5,
      active_jobs: 2,
      queue_size: 0,
      last_updated: new Date().toISOString()
    }
  });
  
  (api.scrapingApi.getJob as jest.Mock).mockResolvedValue({
    data: {
      id: 'test-job-id',
      status: 'running',
      progress: 50
    }
  });
  
  (api.scrapingApi.cancelJob as jest.Mock).mockResolvedValue({
    data: { success: true }
  });
  
  (api.scrapingApi.createMultiRetailerJob as jest.Mock).mockResolvedValue({
    data: { job_ids: ['job1', 'job2'] }
  });
  
  (api.scrapingApi.discoverUrls as jest.Mock).mockResolvedValue({
    data: { urls: [] }
  });
  
  (api.scrapingApi.getRetailerProgress as jest.Mock).mockResolvedValue({
    data: []
  });
  
  (api.scrapingApi.getMonitoringSchedule as jest.Mock).mockResolvedValue({
    data: []
  });
  
  (api.scrapingApi.submitJob as jest.Mock).mockResolvedValue({
    data: { id: 'test-job-id' }
  });
  
  (api.scrapingApi.getJobs as jest.Mock).mockResolvedValue({
    data: []
  });
  
  (api.scrapingApi.getRetailerHealth as jest.Mock).mockResolvedValue({
    data: []
  });
  
  (api.scrapingApi.getJobMetrics as jest.Mock).mockResolvedValue({
    data: []
  });
  
  (api.scrapingApi.getAlerts as jest.Mock).mockResolvedValue({
    data: []
  });
};

export const setupProductApiMocks = () => {
  (api.productApi.search as jest.Mock).mockResolvedValue({
    data: {
      products: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0
    }
  });
  
  (api.productApi.getBrands as jest.Mock).mockResolvedValue({
    data: ['Brand A', 'Brand B', 'Brand C']
  });
  
  (api.productApi.getCategories as jest.Mock).mockResolvedValue({
    data: ['Category 1', 'Category 2', 'Category 3']
  });
  
  (api.productApi.getById as jest.Mock).mockResolvedValue({
    data: {
      id: 'test-product-id',
      sku: 'TEST-SKU',
      name: 'Test Product',
      current_price: 100,
      original_price: 120,
      discount_percentage: 16.67,
      brand: 'Test Brand',
      category: 'Test Category',
      availability: 'in_stock',
      url: 'https://example.com/product',
      images: ['https://example.com/image.jpg'],
      last_scraped: new Date().toISOString()
    }
  });
  
  (api.productApi.getPriceHistory as jest.Mock).mockResolvedValue({
    data: []
  });
  
  (api.productApi.rescrape as jest.Mock).mockResolvedValue({
    data: { success: true }
  });
  
  (api.productApi.getProductMatches as jest.Mock).mockResolvedValue({
    data: []
  });
  
  (api.productApi.getPriceComparisons as jest.Mock).mockResolvedValue({
    data: []
  });
  
  (api.productApi.getByRetailer as jest.Mock).mockResolvedValue({
    data: {
      products: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0
    }
  });
};

export const setupAnalyticsApiMocks = () => {
  (api.analyticsApi.getDashboard as jest.Mock).mockResolvedValue({
    data: {
      product_stats: {
        total_products: 1800,
        in_stock_rate: 85,
        avg_discount: 15,
        total_brands: 150,
        total_categories: 60
      },
      daily_stats: [],
      brand_distribution: [],
      category_distribution: [],
      price_distribution: {}
    }
  });
  
  (api.analyticsApi.getProductTrends as jest.Mock).mockResolvedValue({
    data: {
      trending_products: [],
      price_drops: [],
      new_products: [],
      out_of_stock: []
    }
  });
  
  (api.analyticsApi.getScrapingPerformance as jest.Mock).mockResolvedValue({
    data: {
      hourly_metrics: [],
      retailer_health: [],
      error_summary: {}
    }
  });
};

export const setupCategoryApiMocks = () => {
  (api.categoryApi.getHealth as jest.Mock).mockResolvedValue({
    data: {
      retailer_code: 'HP',
      total_categories: 50,
      active_categories: 45,
      inactive_categories: 5,
      auto_discovered: 30,
      categories: []
    }
  });
  
  (api.categoryApi.getChanges as jest.Mock).mockResolvedValue({
    data: []
  });
  
  (api.categoryApi.getStats as jest.Mock).mockResolvedValue({
    data: {
      retailer_stats: {
        HP: { total: 100, active: 90, inactive: 10, auto_discovered: 50 },
        TWD: { total: 80, active: 70, inactive: 10, auto_discovered: 30 },
      }
    }
  });
  
  (api.categoryApi.triggerMonitor as jest.Mock).mockResolvedValue({
    data: { success: true }
  });
};

export const setupConfigApiMocks = () => {
  (api.configApi.get as jest.Mock).mockResolvedValue({
    data: {
      scraping: {
        batch_size: 10,
        max_pages_per_category: 5,
        request_timeout: 30,
        retry_attempts: 3
      },
      monitoring: {
        schedule_interval_hours: 24,
        price_change_threshold: 5
      }
    }
  });
  
  (api.configApi.update as jest.Mock).mockResolvedValue({
    data: { success: true }
  });
  
  (api.configApi.reset as jest.Mock).mockResolvedValue({
    data: { success: true }
  });
};

export const setupPriceComparisonApiMocks = () => {
  (api.priceComparisonApi.getTopSavings as jest.Mock).mockResolvedValue({
    data: []
  });
  
  (api.priceComparisonApi.getByCategory as jest.Mock).mockResolvedValue({
    data: []
  });
  
  (api.priceComparisonApi.getRetailerCompetitiveness as jest.Mock).mockResolvedValue({
    data: []
  });
  
  (api.priceComparisonApi.getProductMatch as jest.Mock).mockResolvedValue({
    data: null
  });
  
  (api.priceComparisonApi.createMatch as jest.Mock).mockResolvedValue({
    data: { success: true }
  });
  
  (api.priceComparisonApi.refreshMatches as jest.Mock).mockResolvedValue({
    data: { success: true }
  });
};

// Setup all mocks
export const setupAllApiMocks = () => {
  setupRetailerApiMocks();
  setupScrapingApiMocks();
  setupProductApiMocks();
  setupAnalyticsApiMocks();
  setupCategoryApiMocks();
  setupConfigApiMocks();
  setupPriceComparisonApiMocks();
};