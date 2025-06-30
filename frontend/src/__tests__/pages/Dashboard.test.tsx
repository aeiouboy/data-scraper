import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../../pages/Dashboard';
import { RetailerProvider } from '../../contexts/RetailerContext';
import * as api from '../../services/api';

// Mock the API
jest.mock('../../services/api');

// Mock react-chartjs-2
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
  { code: 'HP', name: 'HomePro', isActive: true },
  { code: 'TWD', name: 'Thai Watsadu', isActive: false },
];

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <RetailerProvider>
          {component}
        </RetailerProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Dashboard Page', () => {
  beforeEach(() => {
    (api.analyticsApi.getDashboard as jest.Mock).mockResolvedValue({
      data: mockAnalyticsData,
    });
    (api.retailerApi.getAll as jest.Mock).mockResolvedValue({
      data: mockRetailers,
    });
    (api.retailerApi.getSummary as jest.Mock).mockResolvedValue({
      data: [],
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render dashboard title', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
  });

  it('should display loading state initially', () => {
    renderWithProviders(<Dashboard />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should display product statistics after loading', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Total Products')).toBeInTheDocument();
      expect(screen.getByText('1,000')).toBeInTheDocument();
      expect(screen.getByText('In Stock')).toBeInTheDocument();
      expect(screen.getByText('800')).toBeInTheDocument();
    });
  });

  it('should display average price and discount', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('Average Price')).toBeInTheDocument();
      expect(screen.getByText('฿500.00')).toBeInTheDocument();
      expect(screen.getByText('Average Discount')).toBeInTheDocument();
      expect(screen.getByText('15.0%')).toBeInTheDocument();
    });
  });

  it('should render charts after loading', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
      expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    (api.analyticsApi.getDashboard as jest.Mock).mockRejectedValue(
      new Error('API Error')
    );

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.queryByText('Total Products')).not.toBeInTheDocument();
    });
  });

  it('should filter by retailer when selected', async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(api.analyticsApi.getDashboard).toHaveBeenCalledWith(undefined);
    });

    // Note: Testing retailer selection would require mocking the RetailerContext
    // and simulating the selection change
  });
});