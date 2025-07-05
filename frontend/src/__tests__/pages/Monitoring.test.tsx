import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../test-utils';
import Monitoring from '../../pages/Monitoring';
import * as api from '../../services/api';
import { setupAllApiMocks } from '../../test-utils/mockHelpers';

jest.mock('../../services/api');
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart">Line Chart</div>,
  Bar: () => <div data-testid="bar-chart">Bar Chart</div>,
}));

// Mock the useCategoryMonitoring hook directly
jest.mock('../../hooks/useCategoryMonitoring', () => ({
  useCategoryMonitoring: () => ({
    categoryChanges: [
      {
        id: '1',
        category_name: 'Lighting',
        change_type: 'price_increase',
        change_date: '2023-12-01T10:00:00Z',
        details: {
          percentage_change: 5.5,
          product_count: 25,
        },
      },
      {
        id: '2',
        category_name: 'Furniture',
        change_type: 'new_products',
        change_date: '2023-12-01T09:00:00Z',
        details: {
          product_count: 15,
        },
      },
    ],
    aggregateStats: {
      HP: { total: 100, active: 90, inactive: 10, auto_discovered: 50 },
      TWD: { total: 80, active: 70, inactive: 10, auto_discovered: 30 },
    },
    isLoadingHealth: false,
    refreshAll: jest.fn(),
  }),
}));

const mockHealthMetrics = {
  overall_health: 'healthy',
  success_rate_24h: 95.5,
  success_rate_7d: 94.2,
  avg_response_time: 2.5,
  total_jobs_24h: 100,
  failed_jobs_24h: 5,
  active_jobs: 3,
  queue_size: 10,
  last_updated: '2023-12-01T12:00:00Z',
};

const mockRetailerHealth = [
  {
    retailer_code: 'HP',
    retailer_name: 'HomePro',
    status: 'healthy',
    success_rate: 96.5,
    avg_response_time: 2.3,
    last_successful_scrape: '2023-12-01T11:00:00Z',
    error_count_24h: 2,
    products_scraped_24h: 500,
  },
  {
    retailer_code: 'TWD',
    retailer_name: 'Thai Watsadu',
    status: 'warning',
    success_rate: 87.3,
    avg_response_time: 3.5,
    last_successful_scrape: '2023-12-01T10:00:00Z',
    error_count_24h: 8,
    products_scraped_24h: 350,
  },
];

const mockJobMetrics = [
  { hour: '00:00', successful: 10, failed: 1, avg_duration: 2.1 },
  { hour: '01:00', successful: 12, failed: 0, avg_duration: 2.3 },
  { hour: '02:00', successful: 8, failed: 2, avg_duration: 2.5 },
];

const mockCategoryChanges = [
  {
    id: '1',
    category_name: 'Lighting',
    change_type: 'price_increase',
    change_date: '2023-12-01T10:00:00Z',
    details: {
      percentage_change: 5.5,
      product_count: 25,
    },
  },
  {
    id: '2',
    category_name: 'Furniture',
    change_type: 'new_products',
    change_date: '2023-12-01T09:00:00Z',
    details: {
      product_count: 15,
    },
  },
];

describe('Monitoring Page', () => {
  beforeEach(() => {
    setupAllApiMocks();
    
    // Test-specific mock overrides
    (api.scrapingApi.getHealthMetrics as jest.Mock).mockResolvedValue({
      data: mockHealthMetrics,
    });
    (api.scrapingApi.getRetailerHealth as jest.Mock).mockResolvedValue({
      data: mockRetailerHealth,
    });
    (api.scrapingApi.getJobMetrics as jest.Mock).mockResolvedValue({
      data: mockJobMetrics,
    });
    (api.categoryApi.getChanges as jest.Mock).mockResolvedValue({
      data: mockCategoryChanges,
    });
    (api.categoryApi.getStats as jest.Mock).mockResolvedValue({
      data: {
        retailer_stats: {
          HP: { total: 100, active: 90, inactive: 10, auto_discovered: 50 },
          TWD: { total: 80, active: 70, inactive: 10, auto_discovered: 30 },
        },
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render monitoring page title', () => {
    render(<Monitoring />);
    expect(screen.getByText('Scraping Health Monitor')).toBeInTheDocument();
  });

  it('should display health metrics cards', async () => {
    render(<Monitoring />);

    await waitFor(() => {
      expect(screen.getByText('System Health')).toBeInTheDocument();
      // Use getAllByText since there might be multiple healthy statuses
      const healthyElements = screen.getAllByText('healthy');
      expect(healthyElements.length).toBeGreaterThan(0);
      expect(screen.getByText('24h Success Rate')).toBeInTheDocument();
      expect(screen.getByText('95.5%')).toBeInTheDocument();
      expect(screen.getByText('Active Jobs')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  it('should display retailer health table', async () => {
    render(<Monitoring />);

    await waitFor(() => {
      // Use getAllByText for retailer names that might appear multiple times
      const homeproElements = screen.getAllByText('HomePro');
      expect(homeproElements.length).toBeGreaterThan(0);
      const twdElements = screen.getAllByText('Thai Watsadu');
      expect(twdElements.length).toBeGreaterThan(0);
      expect(screen.getByText('96.5%')).toBeInTheDocument();
      expect(screen.getByText('87.3%')).toBeInTheDocument();
    });
  });

  it('should render charts', async () => {
    render(<Monitoring />);

    await waitFor(() => {
      expect(screen.getAllByTestId('line-chart')).toHaveLength(1);
      expect(screen.getAllByTestId('bar-chart')).toHaveLength(1);
    });
  });

  it('should toggle auto-refresh', async () => {
    render(<Monitoring />);

    const autoRefreshChip = screen.getByText('Auto-refresh ON');
    fireEvent.click(autoRefreshChip);

    expect(screen.getByText('Auto-refresh OFF')).toBeInTheDocument();
  });

  it('should refresh data when refresh button clicked', async () => {
    render(<Monitoring />);

    await waitFor(() => {
      const healthyElements = screen.getAllByText('healthy');
      expect(healthyElements.length).toBeGreaterThan(0);
    });

    const refreshButton = screen.getByLabelText('Refresh data');
    fireEvent.click(refreshButton);

    expect(api.scrapingApi.getHealthMetrics).toHaveBeenCalledTimes(2);
  });

  it('should display category monitoring section', async () => {
    render(<Monitoring />);

    await waitFor(() => {
      expect(screen.getByText('Category Monitoring')).toBeInTheDocument();
      // Use getAllByText for texts that might appear multiple times
      const totalCategoriesElements = screen.getAllByText('Total Categories');
      expect(totalCategoriesElements.length).toBeGreaterThan(0);
      expect(screen.getByText('Category Changes')).toBeInTheDocument();
    });
  });

  it('should display recent category changes', async () => {
    render(<Monitoring />);

    await waitFor(() => {
      expect(screen.getByText('Recent Category Changes')).toBeInTheDocument();
    });
    
    // Check for category names from our mock data
    expect(screen.getByText('Lighting')).toBeInTheDocument();
    
    // Check for change type (it gets formatted in the component)
    expect(screen.getByText('Price increase')).toBeInTheDocument();
  });

  it('should handle category monitor button click', async () => {
    (api.categoryApi.triggerMonitor as jest.Mock).mockResolvedValue({});
    
    render(<Monitoring />);

    await waitFor(() => {
      // Look for the actual button text in the component
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    // Find the button that triggers monitoring
    const playButtons = screen.getAllByTestId('PlayArrowIcon');
    if (playButtons.length > 0) {
      fireEvent.click(playButtons[0].parentElement as HTMLElement);
      await waitFor(() => {
        expect(api.categoryApi.triggerMonitor).toHaveBeenCalled();
      });
    }
  });

  it('should display loading state', () => {
    render(<Monitoring />);
    // Use getAllByRole since there might be multiple progress bars
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars.length).toBeGreaterThan(0);
  });

  it('should handle API errors gracefully', async () => {
    (api.scrapingApi.getHealthMetrics as jest.Mock).mockRejectedValue(
      new Error('API Error')
    );

    render(<Monitoring />);

    await waitFor(() => {
      expect(screen.queryByText('healthy')).not.toBeInTheDocument();
    });
  });

  it('should display category health by retailer', async () => {
    render(<Monitoring />);

    await waitFor(() => {
      expect(screen.getByText('Category Health by Retailer')).toBeInTheDocument();
      // The table should show retailer category stats
      const tables = screen.getAllByRole('table');
      expect(tables.length).toBeGreaterThan(1);
    });
  });
});