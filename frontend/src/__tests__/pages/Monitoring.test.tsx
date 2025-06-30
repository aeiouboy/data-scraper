import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import Monitoring from '../../pages/Monitoring';
import * as api from '../../services/api';

jest.mock('../../services/api');
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart">Line Chart</div>,
  Bar: () => <div data-testid="bar-chart">Bar Chart</div>,
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

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Monitoring Page', () => {
  beforeEach(() => {
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
    renderWithProviders(<Monitoring />);
    expect(screen.getByText('Scraping Health Monitor')).toBeInTheDocument();
  });

  it('should display health metrics cards', async () => {
    renderWithProviders(<Monitoring />);

    await waitFor(() => {
      expect(screen.getByText('System Health')).toBeInTheDocument();
      expect(screen.getByText('healthy')).toBeInTheDocument();
      expect(screen.getByText('24h Success Rate')).toBeInTheDocument();
      expect(screen.getByText('95.5%')).toBeInTheDocument();
      expect(screen.getByText('Active Jobs')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  it('should display retailer health table', async () => {
    renderWithProviders(<Monitoring />);

    await waitFor(() => {
      expect(screen.getByText('HomePro')).toBeInTheDocument();
      expect(screen.getByText('Thai Watsadu')).toBeInTheDocument();
      expect(screen.getByText('96.5%')).toBeInTheDocument();
      expect(screen.getByText('87.3%')).toBeInTheDocument();
    });
  });

  it('should render charts', async () => {
    renderWithProviders(<Monitoring />);

    await waitFor(() => {
      expect(screen.getAllByTestId('line-chart')).toHaveLength(1);
      expect(screen.getAllByTestId('bar-chart')).toHaveLength(1);
    });
  });

  it('should toggle auto-refresh', async () => {
    renderWithProviders(<Monitoring />);

    const autoRefreshChip = screen.getByText('Auto-refresh ON');
    fireEvent.click(autoRefreshChip);

    expect(screen.getByText('Auto-refresh OFF')).toBeInTheDocument();
  });

  it('should refresh data when refresh button clicked', async () => {
    renderWithProviders(<Monitoring />);

    await waitFor(() => {
      expect(screen.getByText('healthy')).toBeInTheDocument();
    });

    const refreshButton = screen.getByLabelText('Refresh data');
    fireEvent.click(refreshButton);

    expect(api.scrapingApi.getHealthMetrics).toHaveBeenCalledTimes(2);
  });

  it('should display category monitoring section', async () => {
    renderWithProviders(<Monitoring />);

    await waitFor(() => {
      expect(screen.getByText('Category Monitoring')).toBeInTheDocument();
      expect(screen.getByText('Total Categories')).toBeInTheDocument();
      expect(screen.getByText('Category Changes')).toBeInTheDocument();
    });
  });

  it('should display recent category changes', async () => {
    renderWithProviders(<Monitoring />);

    await waitFor(() => {
      expect(screen.getByText('Recent Category Changes')).toBeInTheDocument();
      expect(screen.getByText('Lighting')).toBeInTheDocument();
      expect(screen.getByText('Furniture')).toBeInTheDocument();
      expect(screen.getByText('+5.5%')).toBeInTheDocument();
    });
  });

  it('should handle category monitor button click', async () => {
    (api.categoryApi.triggerMonitor as jest.Mock).mockResolvedValue({});
    
    renderWithProviders(<Monitoring />);

    await waitFor(() => {
      expect(screen.getByText('Run Category Monitor')).toBeInTheDocument();
    });

    const monitorButton = screen.getByText('Start Monitor');
    fireEvent.click(monitorButton);

    expect(api.categoryApi.triggerMonitor).toHaveBeenCalled();
  });

  it('should display loading state', () => {
    renderWithProviders(<Monitoring />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should handle API errors gracefully', async () => {
    (api.scrapingApi.getHealthMetrics as jest.Mock).mockRejectedValue(
      new Error('API Error')
    );

    renderWithProviders(<Monitoring />);

    await waitFor(() => {
      expect(screen.queryByText('healthy')).not.toBeInTheDocument();
    });
  });

  it('should display category health by retailer', async () => {
    renderWithProviders(<Monitoring />);

    await waitFor(() => {
      expect(screen.getByText('Category Health by Retailer')).toBeInTheDocument();
      // The table should show retailer category stats
      const tables = screen.getAllByRole('table');
      expect(tables.length).toBeGreaterThan(1);
    });
  });
});