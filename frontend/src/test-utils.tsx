import React, { ReactElement } from 'react';
import { render, RenderOptions, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { RetailerProvider } from './contexts/RetailerContext';
import userEvent from '@testing-library/user-event';

// Create a custom render function that includes all providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <RetailerProvider>
          {children}
        </RetailerProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

// Custom render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  const user = userEvent.setup();
  
  return {
    user,
    ...render(ui, { wrapper: AllTheProviders, ...options }),
  };
};

// Re-export everything
export * from '@testing-library/react';

// Override render method
export { customRender as render };

// Mock data helpers
export const mockRetailers = [
  { 
    code: 'HP', 
    name: 'HomePro', 
    domain: 'homepro.co.th',
    isActive: true,
    config: {},
    lastScraped: '2023-12-01T00:00:00Z'
  },
  { 
    code: 'TWD', 
    name: 'Thai Watsadu', 
    domain: 'thaiwatsadu.com',
    isActive: true,
    config: {},
    lastScraped: '2023-12-01T00:00:00Z'
  },
];

export const mockRetailerStats = [
  {
    retailer_code: 'HP',
    retailer_name: 'HomePro',
    product_count: 1000,
    last_updated: '2023-12-01T00:00:00Z',
    avg_price: 500,
    price_range: { min: 10, max: 10000 },
  },
  {
    retailer_code: 'TWD',
    retailer_name: 'Thai Watsadu',
    product_count: 800,
    last_updated: '2023-12-01T00:00:00Z',
    avg_price: 450,
    price_range: { min: 15, max: 8000 },
  },
];

// Helper to create mock API responses
export const createMockResponse = <T,>(data: T) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  config: {} as any,
});

// Helper to wait for async operations
export const waitForLoadingToFinish = async () => {
  await waitFor(() => {
    const progressBars = screen.queryAllByRole('progressbar');
    if (progressBars.length > 0) {
      throw new Error('Still loading');
    }
  }, { timeout: 3000 });
};