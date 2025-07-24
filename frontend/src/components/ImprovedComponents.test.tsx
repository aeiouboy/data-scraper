import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ImprovedPriceComparisonCard from './ImprovedPriceComparisonCard';

const theme = createTheme();
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider theme={theme}>
      {children}
    </ThemeProvider>
  </QueryClientProvider>
);

const mockProps = {
  productName: 'Test Product',
  category: 'Power Tools',
  brand: 'Test Brand',
  retailers: [
    { retailer_code: 'HP', retailer_name: 'HomePro', price: 1500 },
    { retailer_code: 'TWD', retailer_name: 'Thai Watsadu', price: 1200 },
  ],
  bestRetailerCode: 'TWD',
  savingsAmount: 300,
  savingsPercentage: 20,
  matchConfidence: 0.85,
  matchDetails: {
    sku_score: 0.9,
    brand_score: 0.8,
    name_score: 0.85,
    spec_score: 0.75,
  },
};

describe('ImprovedPriceComparisonCard', () => {
  test('renders product information correctly', () => {
    render(
      <TestWrapper>
        <ImprovedPriceComparisonCard {...mockProps} />
      </TestWrapper>
    );

    // Check product name
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    
    // Check brand and category
    expect(screen.getByText('Test Brand')).toBeInTheDocument();
    expect(screen.getByText('Power Tools')).toBeInTheDocument();
    
    // Check confidence score
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('Excellent Match')).toBeInTheDocument();
    
    // Check savings
    expect(screen.getByText('฿300')).toBeInTheDocument();
    expect(screen.getByText('Save 20.0%')).toBeInTheDocument();
    
    // Check retailers
    expect(screen.getByText('HomePro')).toBeInTheDocument();
    expect(screen.getByText('Thai Watsadu')).toBeInTheDocument();
    
    // Check best price indicator
    expect(screen.getByText('BEST PRICE')).toBeInTheDocument();
  });

  test('renders action buttons', () => {
    render(
      <TestWrapper>
        <ImprovedPriceComparisonCard {...mockProps} />
      </TestWrapper>
    );

    // Check action buttons
    expect(screen.getByText('Compare All')).toBeInTheDocument();
    expect(screen.getByText('View Details')).toBeInTheDocument();
  });

  test('handles missing optional props gracefully', () => {
    const minimalProps = {
      productName: 'Minimal Product',
      category: 'Test Category',
      brand: 'Test Brand',
      retailers: [
        { retailer_code: 'HP', retailer_name: 'HomePro', price: 1000 },
      ],
      bestRetailerCode: 'HP',
      savingsAmount: 0,
      savingsPercentage: 0,
      matchConfidence: 0.5,
    };

    render(
      <TestWrapper>
        <ImprovedPriceComparisonCard {...minimalProps} />
      </TestWrapper>
    );

    expect(screen.getByText('Minimal Product')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument(); // Confidence score
    expect(screen.getByText('Fair Match')).toBeInTheDocument();
  });
});

// Integration test to verify component exports
describe('Component Exports', () => {
  test('ImprovedPriceComparisonCard exports correctly', () => {
    expect(ImprovedPriceComparisonCard).toBeDefined();
    expect(typeof ImprovedPriceComparisonCard).toBe('function');
  });
});

// Accessibility tests
describe('Accessibility', () => {
  test('has proper ARIA labels and structure', () => {
    render(
      <TestWrapper>
        <ImprovedPriceComparisonCard {...mockProps} />
      </TestWrapper>
    );

    // Check for proper heading structure
    const productHeading = screen.getByText('Test Product');
    expect(productHeading.tagName).toBe('H6');

    // Check for accessible buttons
    const compareButton = screen.getByRole('button', { name: /compare all/i });
    expect(compareButton).toBeInTheDocument();

    const detailsButton = screen.getByRole('button', { name: /view details/i });
    expect(detailsButton).toBeInTheDocument();
  });
});