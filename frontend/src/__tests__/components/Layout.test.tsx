import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter, useLocation } from 'react-router-dom';
import Layout from '../../components/Layout';

// Mock useLocation
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: jest.fn(),
}));

const mockUseLocation = useLocation as jest.MockedFunction<typeof useLocation>;

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Layout Component', () => {
  beforeEach(() => {
    mockUseLocation.mockReturnValue({
      pathname: '/',
      search: '',
      hash: '',
      state: null,
      key: 'default',
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should render application title', () => {
    renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    expect(screen.getByText('HomePro Product Manager')).toBeInTheDocument();
  });

  it('should render navigation items', () => {
    renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Products')).toBeInTheDocument();
    expect(screen.getByText('Scraping')).toBeInTheDocument();
    expect(screen.getByText('Monitoring')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('should highlight active navigation item', () => {
    mockUseLocation.mockReturnValue({
      pathname: '/products',
      search: '',
      hash: '',
      state: null,
      key: 'default',
    });

    renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    const productsLink = screen.getByRole('link', { name: /Products/i });
    expect(productsLink.closest('li')).toHaveClass('Mui-selected');
  });

  it('should render children content', () => {
    renderWithRouter(
      <Layout>
        <div data-testid="test-content">Test Content</div>
      </Layout>
    );

    expect(screen.getByTestId('test-content')).toBeInTheDocument();
  });

  it('should toggle drawer on mobile', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    });

    renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    const menuButton = screen.getByLabelText('open drawer');
    fireEvent.click(menuButton);

    // Drawer should be open
    expect(screen.getByRole('presentation')).toBeInTheDocument();
  });

  it('should navigate to correct routes', () => {
    renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    const dashboardLink = screen.getByRole('link', { name: /Dashboard/i });
    expect(dashboardLink).toHaveAttribute('href', '/');

    const productsLink = screen.getByRole('link', { name: /Products/i });
    expect(productsLink).toHaveAttribute('href', '/products');

    const scrapingLink = screen.getByRole('link', { name: /Scraping/i });
    expect(scrapingLink).toHaveAttribute('href', '/scraping');

    const monitoringLink = screen.getByRole('link', { name: /Monitoring/i });
    expect(monitoringLink).toHaveAttribute('href', '/monitoring');

    const settingsLink = screen.getByRole('link', { name: /Settings/i });
    expect(settingsLink).toHaveAttribute('href', '/settings');
  });

  it('should display correct icons for navigation items', () => {
    renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    // Check if navigation items have associated icons
    const listItems = screen.getAllByRole('listitem');
    expect(listItems.length).toBeGreaterThan(0);
    
    // Each navigation item should have an icon
    listItems.forEach((item) => {
      const icon = item.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });
  });

  it('should maintain drawer state on route change', () => {
    const { rerender } = renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    // Initial route
    expect(screen.getByText('Dashboard')).toBeInTheDocument();

    // Change route
    mockUseLocation.mockReturnValue({
      pathname: '/products',
      search: '',
      hash: '',
      state: null,
      key: 'products',
    });

    rerender(
      <BrowserRouter>
        <Layout>
          <div>Different Content</div>
        </Layout>
      </BrowserRouter>
    );

    // Navigation should still be visible
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Products')).toBeInTheDocument();
  });

  it('should have responsive drawer width', () => {
    renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    const drawer = screen.getByRole('navigation').parentElement;
    expect(drawer).toHaveStyle({ width: '240px' });
  });

  it('should render toolbar spacing', () => {
    renderWithRouter(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    // Check for toolbar offset div
    const main = screen.getByRole('main');
    const toolbar = main.querySelector('.MuiToolbar-root');
    expect(toolbar).toBeInTheDocument();
  });
});