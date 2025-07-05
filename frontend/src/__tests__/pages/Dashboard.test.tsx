import React from 'react';
import { render, screen, waitFor } from '../../test-utils';
import Dashboard from '../../pages/Dashboard';
import { analyticsApi, retailerApi } from '../../services/api';
import { useQuery } from '@tanstack/react-query';
import { setupAllApiMocks } from '../../test-utils/mockHelpers';

// Mock the API
jest.mock('../../services/api');

// Mock React Query
jest.mock('@tanstack/react-query', () => ({
  ...jest.requireActual('@tanstack/react-query'),
  useQuery: jest.fn(),
}));

// Mock react-chartjs-2 (already mocked in setupTests.ts, but we'll override for specific tests)
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart">Line Chart</div>,
  Bar: () => <div data-testid="bar-chart">Bar Chart</div>,
  Doughnut: () => <div data-testid="doughnut-chart">Doughnut Chart</div>,
}));

const mockAnalyticsData = {
  product_stats: {
    total_products: 1000,
    in_stock_products: 800,
    out_of_stock_products: 200,
    average_price: 500,
    products_on_sale: 150,
    average_discount: 15,
  },
  scraping_stats: {
    total_jobs: 50,
    successful_jobs: 45,
    failed_jobs: 5,
    average_duration_minutes: 12,
    products_per_hour: 250,
  },
  daily_stats: [
    { date: '2023-12-01', products_scraped: 100, new_products: 10, price_changes: 5 },
    { date: '2023-12-02', products_scraped: 120, new_products: 15, price_changes: 8 },
  ],
  brand_distribution: [
    { brand: 'Brand A', count: 300 },
    { brand: 'Brand B', count: 200 },
  ],
  category_distribution: [
    { category: 'Category 1', count: 400 },
    { category: 'Category 2', count: 300 },
  ],
  price_distribution: {
    '0-100': 100,
    '100-500': 400,
    '500-1000': 300,
    '1000+': 200,
  },
};

const mockRetailers = [
  { 
    id: '1',
    code: 'HP', 
    name: 'HomePro', 
    base_url: 'https://www.homepro.co.th',
    market_position: 'Leading Retailer',
    estimated_products: 150000,
    rate_limit_delay: 1,
    max_concurrent: 5,
    focus_categories: ['Tools', 'Building Materials'],
    price_volatility: 'medium',
    is_active: true 
  },
  { 
    id: '2',
    code: 'TG', 
    name: 'Thai Watsadu', 
    base_url: 'https://www.thaiwatsadu.com',
    market_position: 'Market Leader',
    estimated_products: 100000,
    rate_limit_delay: 1,
    max_concurrent: 3,
    focus_categories: ['Construction', 'Hardware'],
    price_volatility: 'low',
    is_active: true 
  },
];

const mockRetailerStats = [
  {
    code: 'HP',
    name: 'HomePro',
    actual_products: 1000,
    in_stock_products: 800,
    priced_products: 900,
    avg_price: 500,
    min_price: 10,
    max_price: 5000,
    ultra_critical_count: 10,
    high_value_count: 50,
    standard_count: 200,
    low_priority_count: 740,
    category_coverage_percentage: 85.5,
    brand_coverage_percentage: 90.0,
    last_scraped_at: new Date().toISOString(),
  },
];

const mockUseQuery = useQuery as jest.MockedFunction<typeof useQuery>;

describe('Dashboard Page', () => {
  beforeEach(() => {
    setupAllApiMocks();
    // Mock React Query responses
    mockUseQuery.mockImplementation((options: any) => {
      // Handle dashboard query
      if (options.queryKey[0] === 'dashboard') {
        return {
          data: mockAnalyticsData,
          isLoading: false,
          isError: false,
          error: null,
          refetch: jest.fn(),
          isSuccess: true,
        } as any;
      }
      if (options.queryKey[0] === 'retailers') {
        return {
          data: mockRetailers,
          isLoading: false,
          isError: false,
          error: null,
          refetch: jest.fn(),
          isSuccess: true,
        } as any;
      }
      if (options.queryKey[0] === 'retailer-stats') {
        return {
          data: mockRetailerStats,
          isLoading: false,
          isError: false,
          error: null,
          refetch: jest.fn(),
          isSuccess: true,
        } as any;
      }
      if (options.queryKey[0] === 'retailer-summary') {
        return {
          data: undefined,
          isLoading: false,
          isError: false,
          error: null,
          refetch: jest.fn(),
          isSuccess: true,
        } as any;
      }
      if (options.queryKey[0] === 'price-comparison-summary') {
        return {
          data: { savings_opportunities: [] },
          isLoading: false,
          isError: false,
          error: null,
          refetch: jest.fn(),
          isSuccess: true,
        } as any;
      }
      return {
        data: undefined,
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
        isSuccess: true,
      } as any;
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render dashboard title', () => {
    render(<Dashboard />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('should display loading state initially', () => {
    // Mock loading state
    mockUseQuery.mockImplementation((options: any) => {
      if (options.queryKey[0] === 'analytics-dashboard') {
        return {
          data: undefined,
          isLoading: true,
          isError: false,
          error: null,
          refetch: jest.fn(),
          isSuccess: false,
        } as any;
      }
      return {
        data: mockRetailers,
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
        isSuccess: true,
      } as any;
    });

    render(<Dashboard />);
    // There might be multiple progress bars, so use getAllByRole
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars.length).toBeGreaterThan(0);
  });

  it('should display product statistics after loading', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Total Products')).toBeInTheDocument();
      expect(screen.getByText('1,000')).toBeInTheDocument();
      expect(screen.getByText('In Stock')).toBeInTheDocument();
      expect(screen.getByText('800')).toBeInTheDocument();
    });
  });

  it('should display average price and category coverage', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Average Price')).toBeInTheDocument();
      expect(screen.getByText('฿500')).toBeInTheDocument();
      expect(screen.getByText('Category Coverage')).toBeInTheDocument();
      expect(screen.getByText('85.5%')).toBeInTheDocument();
    });
  });

  it('should display price range', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Range: ฿10 - ฿5000/)).toBeInTheDocument();
    });
  });

  it('should handle empty retailer stats gracefully', async () => {
    // Mock empty retailer stats
    mockUseQuery.mockImplementation((options: any) => {
      if (options.queryKey[0] === 'retailer-stats') {
        return {
          data: [],
          isLoading: false,
          isError: false,
          error: null,
          refetch: jest.fn(),
          isSuccess: true,
        } as any;
      }
      return {
        data: options.queryKey[0] === 'retailers' ? mockRetailers : undefined,
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
        isSuccess: true,
      } as any;
    });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/No data available for the selected retailer/i)).toBeInTheDocument();
    });
  });

  it('should display retailer selector', () => {
    render(<Dashboard />);
    
    // The retailer selector should show the selected retailer
    expect(screen.getByText('HomePro')).toBeInTheDocument();
  });

  it('should display retailer name and market position', async () => {
    render(<Dashboard />);

    await waitFor(() => {
      // Check that retailer info is displayed in the selector
      expect(screen.getByText('HomePro')).toBeInTheDocument();
      // Check for "Leading Retailer" text which is the market position shown in the component
      expect(screen.getByText('Leading Retailer')).toBeInTheDocument();
    });
  });


});