import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import Products from '../../pages/Products';
import { RetailerProvider } from '../../contexts/RetailerContext';
import * as api from '../../services/api';

jest.mock('../../services/api');

const mockProducts = [
  {
    id: '1',
    sku: 'HP-001',
    name: 'Test Product 1',
    brand: 'Brand A',
    category: 'Category 1',
    current_price: 1000,
    original_price: 1200,
    discount_percentage: 16.67,
    availability: 'in_stock',
    retailer_code: 'HP',
    url: 'http://test.com/product1',
    images: ['http://test.com/image1.jpg'],
    features: [],
    specifications: {},
    last_scraped: '2023-12-01T00:00:00Z',
    created_at: '2023-12-01T00:00:00Z',
  },
  {
    id: '2',
    sku: 'HP-002',
    name: 'Test Product 2',
    brand: 'Brand B',
    category: 'Category 2',
    current_price: 2000,
    original_price: 2000,
    discount_percentage: 0,
    availability: 'out_of_stock',
    retailer_code: 'HP',
    url: 'http://test.com/product2',
    images: [],
    features: [],
    specifications: {},
    last_scraped: '2023-12-01T00:00:00Z',
    created_at: '2023-12-01T00:00:00Z',
  },
];

const mockBrands = ['Brand A', 'Brand B', 'Brand C'];
const mockCategories = ['Category 1', 'Category 2', 'Category 3'];

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

describe('Products Page', () => {
  beforeEach(() => {
    (api.productApi.search as jest.Mock).mockResolvedValue({
      data: {
        products: mockProducts,
        total: 2,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    });
    (api.productApi.getBrands as jest.Mock).mockResolvedValue({
      data: mockBrands,
    });
    (api.productApi.getCategories as jest.Mock).mockResolvedValue({
      data: mockCategories,
    });
    (api.retailerApi.getAll as jest.Mock).mockResolvedValue({
      data: [],
    });
    (api.retailerApi.getSummary as jest.Mock).mockResolvedValue({
      data: [],
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render products page with title', () => {
    renderWithProviders(<Products />);
    expect(screen.getByText('Products')).toBeInTheDocument();
  });

  it('should display search bar', () => {
    renderWithProviders(<Products />);
    expect(screen.getByPlaceholderText('Search products...')).toBeInTheDocument();
  });

  it('should display filter options', async () => {
    renderWithProviders(<Products />);
    
    await waitFor(() => {
      expect(screen.getByText('Filters')).toBeInTheDocument();
    });
  });

  it('should display products after loading', async () => {
    renderWithProviders(<Products />);

    await waitFor(() => {
      expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      expect(screen.getByText('Test Product 2')).toBeInTheDocument();
    });
  });

  it('should display product details correctly', async () => {
    renderWithProviders(<Products />);

    await waitFor(() => {
      expect(screen.getByText('HP-001')).toBeInTheDocument();
      expect(screen.getByText('Brand A')).toBeInTheDocument();
      expect(screen.getByText('฿1,000.00')).toBeInTheDocument();
      expect(screen.getByText('16.7% off')).toBeInTheDocument();
    });
  });

  it('should handle search input', async () => {
    const { user } = renderWithProviders(<Products />);

    const searchInput = screen.getByPlaceholderText('Search products...');
    await user.type(searchInput, 'Test search');

    // Wait for debounce
    await waitFor(() => {
      expect(api.productApi.search).toHaveBeenCalledWith(
        expect.objectContaining({
          query: 'Test search',
        })
      );
    }, { timeout: 1000 });
  });

  it('should toggle grid and list view', async () => {
    renderWithProviders(<Products />);

    await waitFor(() => {
      expect(screen.getByText('Test Product 1')).toBeInTheDocument();
    });

    const listViewButton = screen.getByLabelText('List view');
    fireEvent.click(listViewButton);

    // View should change but products should still be visible
    expect(screen.getByText('Test Product 1')).toBeInTheDocument();
  });

  it('should handle price filter changes', async () => {
    const { user } = renderWithProviders(<Products />);

    const minPriceInput = screen.getByLabelText('Min Price');
    await user.clear(minPriceInput);
    await user.type(minPriceInput, '500');

    const maxPriceInput = screen.getByLabelText('Max Price');
    await user.clear(maxPriceInput);
    await user.type(maxPriceInput, '1500');

    await waitFor(() => {
      expect(api.productApi.search).toHaveBeenCalledWith(
        expect.objectContaining({
          min_price: 500,
          max_price: 1500,
        })
      );
    });
  });

  it('should handle pagination', async () => {
    (api.productApi.search as jest.Mock).mockResolvedValue({
      data: {
        products: mockProducts,
        total: 50,
        page: 1,
        page_size: 20,
        total_pages: 3,
      },
    });

    renderWithProviders(<Products />);

    await waitFor(() => {
      expect(screen.getByText('Test Product 1')).toBeInTheDocument();
    });

    // Note: Actual pagination component testing would depend on the implementation
  });

  it('should show loading state', () => {
    renderWithProviders(<Products />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should handle API errors', async () => {
    (api.productApi.search as jest.Mock).mockRejectedValue(new Error('API Error'));

    renderWithProviders(<Products />);

    await waitFor(() => {
      expect(screen.queryByText('Test Product 1')).not.toBeInTheDocument();
    });
  });

  it('should filter by availability', async () => {
    renderWithProviders(<Products />);

    const inStockCheckbox = screen.getByLabelText('In Stock Only');
    fireEvent.click(inStockCheckbox);

    await waitFor(() => {
      expect(api.productApi.search).toHaveBeenCalledWith(
        expect.objectContaining({
          in_stock_only: true,
        })
      );
    });
  });

  it('should filter by sale items', async () => {
    renderWithProviders(<Products />);

    const onSaleCheckbox = screen.getByLabelText('On Sale Only');
    fireEvent.click(onSaleCheckbox);

    await waitFor(() => {
      expect(api.productApi.search).toHaveBeenCalledWith(
        expect.objectContaining({
          on_sale_only: true,
        })
      );
    });
  });
});