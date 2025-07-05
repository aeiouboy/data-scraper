import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../test-utils';
import Products from '../../pages/Products';
import * as api from '../../services/api';
import { setupAllApiMocks } from '../../test-utils/mockHelpers';

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
const mockCategories = [
  { id: 'cat1', name: 'Category 1' },
  { id: 'cat2', name: 'Category 2' },
  { id: 'cat3', name: 'Category 3' },
];

describe('Products Page', () => {
  beforeEach(() => {
    setupAllApiMocks();
    
    // Test-specific mock overrides
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
      data: { brands: mockBrands },
    });
    (api.productApi.getCategories as jest.Mock).mockResolvedValue({
      data: { categories: mockCategories },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render products page with title', () => {
    render(<Products />);
    expect(screen.getByText('Products')).toBeInTheDocument();
  });

  it('should display search bar', () => {
    render(<Products />);
    expect(screen.getByPlaceholderText('Search by name, SKU, or description')).toBeInTheDocument();
  });

  it('should display filter options', async () => {
    render(<Products />);
    
    await waitFor(() => {
      expect(screen.getByText('Filters')).toBeInTheDocument();
    });
  });

  it('should display products after loading', async () => {
    render(<Products />);

    await waitFor(() => {
      expect(screen.getByText('Test Product 1')).toBeInTheDocument();
      expect(screen.getByText('Test Product 2')).toBeInTheDocument();
    });
  });

  it('should display product details correctly', async () => {
    render(<Products />);

    // Wait for the API call to complete and products to render
    await waitFor(() => {
      expect(screen.getByText('Test Product 1')).toBeInTheDocument();
    });
    
    // Check for basic product data
    expect(screen.getByText('Brand A')).toBeInTheDocument();
    expect(screen.getByText('HP-001')).toBeInTheDocument();
    expect(screen.getByText('Test Product 2')).toBeInTheDocument();
    expect(screen.getByText('HP-002')).toBeInTheDocument();
  });

  it('should handle search input', async () => {
    const { user } = render(<Products />);

    const searchInput = screen.getByPlaceholderText('Search by name, SKU, or description');
    await user.type(searchInput, 'Test search');

    // Click search button to trigger search
    const searchButton = screen.getByRole('button', { name: /search/i });
    await user.click(searchButton);

    await waitFor(() => {
      expect(api.productApi.search).toHaveBeenCalledWith(
        expect.objectContaining({
          query: 'Test search',
        })
      );
    });
  });

  it('should display products in grid', async () => {
    render(<Products />);

    await waitFor(() => {
      expect(screen.getByText('Test Product 1')).toBeInTheDocument();
    });

    // Products should be displayed
    expect(screen.getByText('Test Product 1')).toBeInTheDocument();
    expect(screen.getByText('Test Product 2')).toBeInTheDocument();
  });

  it('should handle price filter changes', async () => {
    const { user } = render(<Products />);

    // Wait for initial load
    await waitFor(() => {
      expect(api.productApi.search).toHaveBeenCalled();
    });

    // First click the Filters button to show the filter section
    const filterButton = screen.getByRole('button', { name: /filters/i });
    await user.click(filterButton);

    // Wait for filters to be visible
    await waitFor(() => {
      expect(screen.getByText('Price Range')).toBeInTheDocument();
    });

    // Find the price range sliders (there should be 2, one for each thumb)
    const priceSliders = screen.getAllByRole('slider');
    expect(priceSliders.length).toBe(2);
    
    // Simulate slider change
    fireEvent.change(priceSliders[0], { target: { value: 500 } });
    fireEvent.change(priceSliders[1], { target: { value: 1500 } });

    // Click search to apply filters
    const searchButton = screen.getByRole('button', { name: /search/i });
    await user.click(searchButton);

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

    render(<Products />);

    await waitFor(() => {
      expect(screen.getByText('Test Product 1')).toBeInTheDocument();
    });

    // Note: Actual pagination component testing would depend on the implementation
  });

  it('should show loading state', () => {
    render(<Products />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should handle API errors', async () => {
    (api.productApi.search as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(<Products />);

    await waitFor(() => {
      expect(screen.queryByText('Test Product 1')).not.toBeInTheDocument();
    });
  });

  it('should filter by availability', async () => {
    const { user } = render(<Products />);

    // Wait for initial load
    await waitFor(() => {
      expect(api.productApi.search).toHaveBeenCalled();
    });

    // First click the Filters button to show the filter section
    const filterButton = screen.getByRole('button', { name: /filters/i });
    await user.click(filterButton);

    // Wait for filters to be visible
    await waitFor(() => {
      expect(screen.getByLabelText('In Stock Only')).toBeInTheDocument();
    });

    const inStockCheckbox = screen.getByLabelText('In Stock Only');
    await user.click(inStockCheckbox);

    // Click search to apply filters
    const searchButton = screen.getByRole('button', { name: /search/i });
    await user.click(searchButton);

    await waitFor(() => {
      expect(api.productApi.search).toHaveBeenCalledWith(
        expect.objectContaining({
          in_stock_only: true,
        })
      );
    });
  });

  it('should filter by sale items', async () => {
    const { user } = render(<Products />);

    // Wait for initial load
    await waitFor(() => {
      expect(api.productApi.search).toHaveBeenCalled();
    });

    // First click the Filters button to show the filter section
    const filterButton = screen.getByRole('button', { name: /filters/i });
    await user.click(filterButton);

    // Wait for filters to be visible
    await waitFor(() => {
      expect(screen.getByLabelText('On Sale Only')).toBeInTheDocument();
    });

    const onSaleCheckbox = screen.getByLabelText('On Sale Only');
    await user.click(onSaleCheckbox);

    // Click search to apply filters
    const searchButton = screen.getByRole('button', { name: /search/i });
    await user.click(searchButton);

    await waitFor(() => {
      expect(api.productApi.search).toHaveBeenCalledWith(
        expect.objectContaining({
          on_sale_only: true,
        })
      );
    });
  });
});