import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import Scraping from '../../pages/Scraping';
import { RetailerProvider } from '../../contexts/RetailerContext';
import * as api from '../../services/api';

jest.mock('../../services/api');

const mockJobs = [
  {
    id: '1',
    job_type: 'product',
    status: 'completed',
    target_url: 'http://example.com/products',
    total_items: 100,
    processed_items: 100,
    success_items: 95,
    failed_items: 5,
    created_at: '2023-12-01T10:00:00Z',
    started_at: '2023-12-01T10:01:00Z',
    completed_at: '2023-12-01T10:30:00Z',
  },
  {
    id: '2',
    job_type: 'category',
    status: 'running',
    target_url: 'http://example.com/categories',
    total_items: 50,
    processed_items: 25,
    success_items: 23,
    failed_items: 2,
    created_at: '2023-12-01T11:00:00Z',
    started_at: '2023-12-01T11:01:00Z',
    completed_at: null,
  },
];

const mockRetailers = [
  { code: 'HP', name: 'HomePro' },
  { code: 'TWD', name: 'Thai Watsadu' },
  { code: 'GH', name: 'Global House' },
];

const mockCategories = {
  HP: [
    { code: 'LIG', name: 'Lighting', url: 'http://example.com/lighting' },
    { code: 'PAI', name: 'Paint', url: 'http://example.com/paint' },
  ],
  TWD: [
    { code: 'construction-materials', name: 'Construction Materials', url: 'http://example.com/construction' },
  ],
};

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return {
    user: userEvent.setup(),
    ...render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <RetailerProvider>
            {component}
          </RetailerProvider>
        </BrowserRouter>
      </QueryClientProvider>
    ),
  };
};

describe('Scraping Page', () => {
  beforeEach(() => {
    (api.scrapingApi.getJobs as jest.Mock).mockResolvedValue({
      data: mockJobs,
    });
    (api.retailerApi.getAll as jest.Mock).mockResolvedValue({
      data: mockRetailers,
    });
    (api.retailerApi.getSummary as jest.Mock).mockResolvedValue({
      data: [],
    });
    (api.retailerApi.getCategories as jest.Mock).mockImplementation((code) => {
      return Promise.resolve({ data: mockCategories[code] || [] });
    });
    (api.scrapingApi.createJob as jest.Mock).mockResolvedValue({
      data: { id: '3', status: 'pending' },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render scraping page title', () => {
    renderWithProviders(<Scraping />);
    expect(screen.getByText('Scraping Management')).toBeInTheDocument();
  });

  it('should display recent jobs', async () => {
    renderWithProviders(<Scraping />);

    await waitFor(() => {
      expect(screen.getByText('Recent Jobs')).toBeInTheDocument();
      expect(screen.getByText('http://example.com/products')).toBeInTheDocument();
      expect(screen.getByText('http://example.com/categories')).toBeInTheDocument();
    });
  });

  it('should show job status badges', async () => {
    renderWithProviders(<Scraping />);

    await waitFor(() => {
      expect(screen.getByText('completed')).toBeInTheDocument();
      expect(screen.getByText('running')).toBeInTheDocument();
    });
  });

  it('should display retailer selection', async () => {
    renderWithProviders(<Scraping />);

    await waitFor(() => {
      expect(screen.getByText('Select Retailers')).toBeInTheDocument();
      expect(screen.getByText('HomePro')).toBeInTheDocument();
      expect(screen.getByText('Thai Watsadu')).toBeInTheDocument();
    });
  });

  it('should select/deselect retailers', async () => {
    const { user } = renderWithProviders(<Scraping />);

    await waitFor(() => {
      expect(screen.getByText('HomePro')).toBeInTheDocument();
    });

    const homeproCheckbox = screen.getByRole('checkbox', { name: /HomePro/i });
    await user.click(homeproCheckbox);

    expect(homeproCheckbox).toBeChecked();
  });

  it('should show categories when retailer selected', async () => {
    const { user } = renderWithProviders(<Scraping />);

    await waitFor(() => {
      expect(screen.getByText('HomePro')).toBeInTheDocument();
    });

    const homeproCheckbox = screen.getByRole('checkbox', { name: /HomePro/i });
    await user.click(homeproCheckbox);

    await waitFor(() => {
      expect(screen.getByText('Lighting')).toBeInTheDocument();
      expect(screen.getByText('Paint')).toBeInTheDocument();
    });
  });

  it('should configure scraping options', async () => {
    const { user } = renderWithProviders(<Scraping />);

    const maxPagesInput = screen.getByLabelText('Max Pages per Category');
    await user.clear(maxPagesInput);
    await user.type(maxPagesInput, '20');

    expect(maxPagesInput).toHaveValue(20);
  });

  it('should start scraping job', async () => {
    const { user } = renderWithProviders(<Scraping />);

    // Select retailer
    const homeproCheckbox = screen.getByRole('checkbox', { name: /HomePro/i });
    await user.click(homeproCheckbox);

    // Wait for categories to load
    await waitFor(() => {
      expect(screen.getByText('Lighting')).toBeInTheDocument();
    });

    // Select category
    const lightingCheckbox = screen.getByRole('checkbox', { name: /Lighting/i });
    await user.click(lightingCheckbox);

    // Start scraping
    const startButton = screen.getByText('Start Scraping');
    await user.click(startButton);

    expect(api.scrapingApi.createJob).toHaveBeenCalledWith(
      expect.objectContaining({
        job_type: 'category',
      })
    );
  });

  it('should show validation error when no retailers selected', async () => {
    const { user } = renderWithProviders(<Scraping />);

    const startButton = screen.getByText('Start Scraping');
    await user.click(startButton);

    await waitFor(() => {
      expect(screen.getByText(/Please select at least one retailer/i)).toBeInTheDocument();
    });
  });

  it('should refresh job list', async () => {
    const { user } = renderWithProviders(<Scraping />);

    await waitFor(() => {
      expect(screen.getByText('Recent Jobs')).toBeInTheDocument();
    });

    const refreshButton = screen.getByLabelText('Refresh jobs');
    await user.click(refreshButton);

    expect(api.scrapingApi.getJobs).toHaveBeenCalledTimes(2);
  });

  it('should display job progress', async () => {
    renderWithProviders(<Scraping />);

    await waitFor(() => {
      expect(screen.getByText('25 / 50')).toBeInTheDocument(); // Progress for running job
      expect(screen.getByText('100 / 100')).toBeInTheDocument(); // Progress for completed job
    });
  });

  it('should show job duration', async () => {
    renderWithProviders(<Scraping />);

    await waitFor(() => {
      expect(screen.getByText(/29 minutes/i)).toBeInTheDocument(); // Duration for completed job
    });
  });

  it('should toggle advanced options', async () => {
    const { user } = renderWithProviders(<Scraping />);

    const advancedToggle = screen.getByText('Advanced Options');
    await user.click(advancedToggle);

    await waitFor(() => {
      expect(screen.getByLabelText('Max Concurrent Requests')).toBeInTheDocument();
      expect(screen.getByLabelText('Request Timeout (seconds)')).toBeInTheDocument();
    });
  });

  it('should handle multi-retailer selection', async () => {
    const { user } = renderWithProviders(<Scraping />);

    await waitFor(() => {
      expect(screen.getByText('HomePro')).toBeInTheDocument();
    });

    // Select multiple retailers
    const homeproCheckbox = screen.getByRole('checkbox', { name: /HomePro/i });
    const twdCheckbox = screen.getByRole('checkbox', { name: /Thai Watsadu/i });
    
    await user.click(homeproCheckbox);
    await user.click(twdCheckbox);

    expect(homeproCheckbox).toBeChecked();
    expect(twdCheckbox).toBeChecked();
  });

  it('should disable start button when scraping in progress', async () => {
    (api.scrapingApi.createJob as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000))
    );

    const { user } = renderWithProviders(<Scraping />);

    const homeproCheckbox = screen.getByRole('checkbox', { name: /HomePro/i });
    await user.click(homeproCheckbox);

    await waitFor(() => {
      expect(screen.getByText('Lighting')).toBeInTheDocument();
    });

    const lightingCheckbox = screen.getByRole('checkbox', { name: /Lighting/i });
    await user.click(lightingCheckbox);

    const startButton = screen.getByText('Start Scraping');
    await user.click(startButton);

    expect(startButton).toBeDisabled();
  });
});