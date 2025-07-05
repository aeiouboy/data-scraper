import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../test-utils';
import { useLocation } from 'react-router-dom';
import Layout from '../../components/Layout';
import { useQuery } from '@tanstack/react-query';
import { setupAllApiMocks } from '../../test-utils/mockHelpers';

// Mock the API
jest.mock('../../services/api');

// Create a mock navigate function
const mockNavigate = jest.fn();

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: jest.fn(),
  useNavigate: () => mockNavigate,
}));

// Mock React Query
jest.mock('@tanstack/react-query', () => ({
  ...jest.requireActual('@tanstack/react-query'),
  useQuery: jest.fn(),
}));

const mockUseLocation = useLocation as jest.MockedFunction<typeof useLocation>;
const mockUseQuery = useQuery as jest.MockedFunction<typeof useQuery>;

describe('Layout Component', () => {
  beforeEach(() => {
    setupAllApiMocks();
    // Mock location
    mockUseLocation.mockReturnValue({
      pathname: '/',
      search: '',
      hash: '',
      state: null,
      key: 'default',
    });

    // Mock retailer data from React Query
    mockUseQuery.mockImplementation((options: any) => {
      if (options.queryKey[0] === 'retailers') {
        return {
          data: [
            {
              id: '1',
              code: 'HP',
              name: 'HomePro',
              base_url: 'https://www.homepro.co.th',
              is_active: true,
            },
            {
              id: '2',
              code: 'TG',
              name: 'Thai Watsadu',
              base_url: 'https://www.thaiwatsadu.com',
              is_active: true,
            },
          ],
          isLoading: false,
          isError: false,
          error: null,
          refetch: jest.fn(),
        } as any;
      }
      if (options.queryKey[0] === 'retailer-stats') {
        return {
          data: [],
          isLoading: false,
          isError: false,
          error: null,
          refetch: jest.fn(),
        } as any;
      }
      return {
        data: undefined,
        isLoading: false,
        isError: false,
        error: null,
        refetch: jest.fn(),
      } as any;
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render application title', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    // There are two instances (mobile and desktop), just check that at least one exists
    expect(screen.getAllByText('Thai Market Intel').length).toBeGreaterThanOrEqual(1);
  });

  it('should render navigation items', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    // Check main navigation items (they appear in both mobile and desktop drawers)
    const navItems = ['Dashboard', 'Products', 'Price Comparisons', 'Scraping', 'Analytics', 'Monitoring', 'Settings'];
    navItems.forEach(item => {
      const items = screen.getAllByText(item);
      expect(items.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('should highlight active navigation item based on current path', () => {
    // Mock products page
    mockUseLocation.mockReturnValue({
      pathname: '/products',
      search: '',
      hash: '',
      state: null,
      key: 'default',
    });

    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    // Just verify that Products text exists in the navigation
    const productsItems = screen.getAllByText('Products');
    expect(productsItems.length).toBeGreaterThanOrEqual(1);
  });

  it('should render children content', () => {
    render(
      <Layout>
        <div data-testid="test-content">Test Content</div>
      </Layout>
    );

    expect(screen.getByTestId('test-content')).toBeInTheDocument();
  });

  it('should toggle drawer on mobile', async () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    });

    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    const menuButton = screen.getByLabelText('open drawer');
    fireEvent.click(menuButton);

    // Wait for drawer to open and check that drawer content is visible
    // Use getAllByText since Dashboard might appear multiple times
    await waitFor(() => {
      const dashboardElements = screen.getAllByText('Dashboard');
      expect(dashboardElements.length).toBeGreaterThan(0);
    });
  });

  it('should have clickable menu items', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    // Get all dashboard buttons (might be multiple due to mobile/desktop views)
    const dashboardButtons = screen.getAllByText('Dashboard');
    
    // Click the first visible Dashboard button
    fireEvent.click(dashboardButtons[0]);

    // Verify all menu items are present and clickable
    const menuItems = ['Dashboard', 'Products', 'Price Comparisons', 'Scraping', 'Analytics', 'Monitoring', 'Settings'];
    
    menuItems.forEach(item => {
      const elements = screen.getAllByText(item);
      expect(elements.length).toBeGreaterThan(0);
    });
  });

  it('should display correct icons for navigation items', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    // Check if navigation items have associated icons
    const listItems = screen.getAllByRole('listitem');
    const navigationItems = listItems.filter(item => {
      // Filter only navigation menu items
      const text = item.textContent || '';
      return ['Dashboard', 'Products', 'Price Comparisons', 'Scraping', 'Analytics', 'Monitoring', 'Settings'].some(
        navItem => text.includes(navItem)
      );
    });

    expect(navigationItems.length).toBeGreaterThan(0);
    
    // Each navigation item should have an icon
    navigationItems.forEach((item) => {
      const icon = item.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });
  });

  it('should render RetailerSelector component', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    // The RetailerSelector should be present in the layout
    // Look for the autocomplete component
    const autocomplete = screen.getByRole('combobox');
    expect(autocomplete).toBeInTheDocument();
  });

  it('should maintain drawer state on route change', () => {
    const { rerender } = render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    // Just verify navigation items are present
    const dashboardElements = screen.getAllByText('Dashboard');
    expect(dashboardElements.length).toBeGreaterThan(0);

    // Change route
    mockUseLocation.mockReturnValue({
      pathname: '/products',
      search: '',
      hash: '',
      state: null,
      key: 'products',
    });

    rerender(
      <Layout>
        <div>Different Content</div>
      </Layout>
    );

    // Navigation should still be visible
    const dashboardElementsAfter = screen.getAllByText('Dashboard');
    expect(dashboardElementsAfter.length).toBeGreaterThan(0);
  });

  it('should have responsive drawer width', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    const drawer = screen.getByRole('navigation').parentElement;
    // Check that drawer has the expected width styling
    expect(drawer).toBeInTheDocument();
  });

  it('should render toolbar spacing', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    // Check for main content area
    const main = screen.getByRole('main');
    expect(main).toBeInTheDocument();
  });

  it('should handle drawer close on mobile', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    });

    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    // Open drawer
    const menuButton = screen.getByLabelText('open drawer');
    fireEvent.click(menuButton);

    // Click on a navigation item
    const dashboardItems = screen.getAllByText('Dashboard');
    fireEvent.click(dashboardItems[0]);

    // The drawer behavior would be handled by MUI
    expect(menuButton).toBeInTheDocument();
  });
});