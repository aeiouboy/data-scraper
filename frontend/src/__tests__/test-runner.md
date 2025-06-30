# Frontend Test Runner Guide

## Running Tests

### Install Dependencies
```bash
cd frontend
npm install
```

### Run All Tests
```bash
npm test
```

### Run Tests in Watch Mode
```bash
npm run test:watch
```

### Run Tests with Coverage Report
```bash
npm run test:coverage
```

## Test Structure

### Unit Tests
- **API Services** (`__tests__/services/api.test.ts`)
  - Tests all API endpoints
  - Mocks axios responses
  - Validates request parameters

### Page Component Tests
- **Dashboard** (`__tests__/pages/Dashboard.test.tsx`)
  - Loading states
  - Data display
  - Chart rendering
  - Error handling

- **Products** (`__tests__/pages/Products.test.tsx`)
  - Product listing
  - Search functionality
  - Filtering
  - Pagination
  - Grid/List view toggle

- **Monitoring** (`__tests__/pages/Monitoring.test.tsx`)
  - Health metrics display
  - Auto-refresh functionality
  - Retailer health status
  - Category monitoring
  - Charts

- **Settings** (`__tests__/pages/Settings.test.tsx`)
  - Configuration updates
  - Schedule management
  - Tab navigation
  - Form validation

- **Scraping** (`__tests__/pages/Scraping.test.tsx`)
  - Job creation
  - Retailer selection
  - Category selection
  - Job status display
  - Validation

### Component Tests
- **Layout** (`__tests__/components/Layout.test.tsx`)
  - Navigation rendering
  - Active route highlighting
  - Responsive behavior
  - Drawer functionality

## Test Coverage Targets

- Statements: 80%+
- Branches: 75%+
- Functions: 80%+
- Lines: 80%+

## Common Test Patterns

### Mocking API Calls
```typescript
jest.mock('../../services/api');
(api.productApi.search as jest.Mock).mockResolvedValue({
  data: mockProducts
});
```

### Testing with React Query
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});
```

### Testing User Interactions
```typescript
const { user } = renderWithProviders(<Component />);
await user.click(button);
await user.type(input, 'text');
```

## Troubleshooting

### Issue: Tests failing due to Chart.js
Solution: Chart.js components are mocked in `setupTests.ts`

### Issue: API connection errors
Solution: All API calls should be mocked in tests

### Issue: React Query retries
Solution: Disable retries in test QueryClient configuration

## Next Steps

1. Run initial test suite to identify any environment issues
2. Fix any failing tests
3. Add integration tests for critical user flows
4. Set up CI/CD pipeline for automated testing
5. Add E2E tests with Cypress or Playwright