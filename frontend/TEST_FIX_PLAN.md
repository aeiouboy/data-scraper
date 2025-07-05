# Comprehensive Test Fix Plan

## Overview
The test suite is failing due to three main issues:
1. **Axios Mock Issues**: The axios mock is not being properly applied to the imported API services
2. **Missing Context Providers**: Components requiring RetailerProvider and QueryClient are not wrapped properly in tests
3. **React Query Dependencies**: Tests need proper mocking of React Query hooks

## Root Causes

### 1. Axios Mock Problem
- The current axios mock in `src/__mocks__/axios.ts` is not being used correctly
- The API service (`src/services/api.ts`) creates an axios instance at module load time, before the mock is applied
- Tests are calling the real axios instance methods, not the mocked ones

### 2. Context Provider Issues
- Layout component uses `RetailerSelector` which requires `RetailerProvider`
- Many components use React Query hooks which require `QueryClientProvider`
- Tests don't wrap components with these required providers

### 3. Test Setup Configuration
- Jest configuration needs proper module name mapping
- Missing test utilities for wrapping components with providers

## Fix Implementation Plan

### Priority 1: Fix Axios Mocking (Critical)

#### Option A: Module Factory Mock (Recommended)
1. Update jest.config.js to use module factory pattern
2. Create a proper axios mock that returns the mocked instance

#### Option B: Manual Mock in Each Test
1. Mock axios.create in beforeEach of each test
2. Less maintainable but works

### Priority 2: Create Test Utilities (Critical)

Create `src/test-utils.tsx`:
```typescript
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { RetailerProvider } from './contexts/RetailerContext';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      cacheTime: 0,
    },
  },
});

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const testQueryClient = createTestQueryClient();
  
  return (
    <QueryClientProvider client={testQueryClient}>
      <RetailerProvider>
        <BrowserRouter>
          {children}
        </BrowserRouter>
      </RetailerProvider>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

### Priority 3: Update All Test Files (High)

1. Replace `@testing-library/react` imports with custom test-utils
2. Remove manual BrowserRouter wrapping
3. Update axios mocking approach

### Priority 4: Mock React Query Properly (Medium)

Add to setupTests.ts:
```typescript
// Mock React Query for tests
jest.mock('@tanstack/react-query', () => ({
  ...jest.requireActual('@tanstack/react-query'),
  useQuery: jest.fn(),
  useMutation: jest.fn(),
}));
```

### Priority 5: Fix Individual Test Issues (Medium)

1. Update api.test.ts to properly mock axios instance
2. Update component tests to use new render utility
3. Add missing mock implementations

## Implementation Steps

### Step 1: Fix Axios Mock (30 minutes)
1. Delete current `src/__mocks__/axios.ts`
2. Update jest.config.js
3. Create new mock implementation

### Step 2: Create Test Utilities (20 minutes)
1. Create `src/test-utils.tsx`
2. Add provider wrapper components
3. Export custom render function

### Step 3: Update Test Files (1-2 hours)
1. Start with api.test.ts
2. Update Layout.test.tsx
3. Update remaining component tests

### Step 4: Verify and Debug (30 minutes)
1. Run all tests
2. Fix any remaining issues
3. Check coverage reports

## Expected Outcomes

After implementing these fixes:
- All axios-related tests will pass
- Component tests will have proper context providers
- No more "useRetailer must be used within RetailerProvider" errors
- Tests will be more maintainable and easier to write

## Alternative Approaches

If the above doesn't work:
1. Use MSW (Mock Service Worker) for API mocking
2. Use React Testing Library's wrapper option per test
3. Consider upgrading testing dependencies

## Code Examples

### Fixed api.test.ts structure:
```typescript
import axios from 'axios';
import { productApi } from '../../services/api';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('API Services', () => {
  let mockApiInstance: any;

  beforeEach(() => {
    mockApiInstance = {
      get: jest.fn(),
      post: jest.fn(),
      // ... other methods
    };
    
    mockedAxios.create = jest.fn(() => mockApiInstance);
    
    // Re-import to get fresh instance with mock
    jest.resetModules();
  });
  
  // ... tests
});
```

### Fixed Layout.test.tsx structure:
```typescript
import { render, screen } from '../../test-utils';
import Layout from '../../components/Layout';

describe('Layout Component', () => {
  it('should render application title', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );

    expect(screen.getByText('HomePro Product Manager')).toBeInTheDocument();
  });
  
  // ... other tests
});
```

## Timeline

- **Immediate (Day 1)**: Fix axios mocking and create test utilities
- **Short-term (Day 2)**: Update all failing tests
- **Medium-term (Week 1)**: Add missing test coverage
- **Long-term (Month 1)**: Implement E2E tests with Cypress/Playwright

## Success Metrics

- All tests passing (100% success rate)
- Test coverage > 80%
- Test execution time < 30 seconds
- No flaky tests
- Easy to add new tests