import { test, expect } from '@playwright/test';

/**
 * Comprehensive E2E Tests for Improved Price Comparisons UI
 * Tests the enhanced user interface with animations, filters, and improved UX
 */

test.describe('Improved Price Comparisons UI', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the improved price comparisons page
    await page.goto('/price-comparisons-improved');
    
    // Wait for the page to fully load
    await page.waitForLoadState('networkidle');
    
    // Enable multi-retailer mode by clicking the toggle if it exists
    const multiRetailerToggle = page.locator('input[type="checkbox"]').first();
    if (await multiRetailerToggle.isVisible()) {
      const isChecked = await multiRetailerToggle.isChecked();
      if (!isChecked) {
        await multiRetailerToggle.click();
        await page.waitForTimeout(1000); // Wait for state update
      }
    }
  });

  test.describe('Page Load and Initial State', () => {
    test('should load with enhanced header and gradient styling', async ({ page }) => {
      // Check for the enhanced header with gradient text
      await expect(page.locator('text=💰 Smart Price Comparisons')).toBeVisible();
      
      // Verify the page has the expected gradient background
      const headerSection = page.locator('[data-testid="enhanced-header"]').first();
      await expect(headerSection).toBeVisible();
      
      // Check for retailer count in subtitle
      await expect(page.locator('text=/Find the best deals across \\d+ trusted retailers/')).toBeVisible();
    });

    test('should display animated statistics cards', async ({ page }) => {
      // Wait for statistics cards to load and animate
      await page.waitForSelector('[data-testid="stats-card"]', { state: 'visible' });
      
      // Check all 4 statistics cards are present
      const statsCards = page.locator('[data-testid="stats-card"]');
      await expect(statsCards).toHaveCount(4);
      
      // Verify each card has proper content
      await expect(page.locator('text=Total Savings')).toBeVisible();
      await expect(page.locator('text=Best Deals')).toBeVisible();
      await expect(page.locator('text=Average Savings')).toBeVisible();
      await expect(page.locator('text=Retailers')).toBeVisible();
      
      // Check for proper currency formatting (Thai Baht)
      await expect(page.locator('text=/฿[0-9,]+/')).toBeVisible();
    });

    test('should show view mode toggles with proper icons', async ({ page }) => {
      // Wait for the loading backdrop to disappear if it exists
      const loadingBackdrop = page.locator('[data-testid="loading-backdrop"]');
      if (await loadingBackdrop.isVisible()) {
        await loadingBackdrop.waitFor({ state: 'hidden', timeout: 30000 });
      }
      
      // Enable multi-retailer mode first if not already enabled
      const enableButton = page.locator('text=Enable Multi-Retailer Mode');
      if (await enableButton.isVisible()) {
        const multiRetailerToggle = page.locator('input[type="checkbox"]').first();
        if (await multiRetailerToggle.isVisible()) {
          await multiRetailerToggle.click();
          await page.waitForTimeout(2000); // Wait for state update and re-render
        }
      }
      
      // Wait for the enhanced header to appear (indicates multi-retailer mode is active)
      await page.waitForSelector('[data-testid="enhanced-header"]', { timeout: 10000 });
      
      // Check for view mode toggle buttons
      await expect(page.locator('button:has-text("Grid")')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('button:has-text("List")')).toBeVisible();
      await expect(page.locator('button:has-text("Analytics")')).toBeVisible();
      
      // Verify icons are present in toggle buttons
      const gridIcon = page.locator('button:has-text("Grid") svg');
      const listIcon = page.locator('button:has-text("List") svg');
      const analyticsIcon = page.locator('button:has-text("Analytics") svg');
      
      await expect(gridIcon).toBeVisible();
      await expect(listIcon).toBeVisible();
      await expect(analyticsIcon).toBeVisible();
    });
  });

  test.describe('Multi-Retailer Mode Requirement', () => {
    test('should show multi-retailer mode prompt when insufficient retailers', async ({ page }) => {
      // Simulate single retailer mode (this might need API mocking)
      await page.evaluate(() => {
        // Mock the retailer context to show single retailer mode
        window.localStorage.setItem('retailer-context', JSON.stringify({
          selectedRetailers: ['HP'],
          multiRetailerMode: false
        }));
      });
      
      await page.reload();
      await page.waitForLoadState('networkidle');
      
      // Check for multi-retailer mode prompt
      await expect(page.locator('text=Enable Multi-Retailer Mode')).toBeVisible();
      await expect(page.locator('text=Price comparisons require data from multiple retailers')).toBeVisible();
      
      // Verify the info alert is displayed
      await expect(page.locator('[role="alert"]')).toBeVisible();
      await expect(page.locator('text=Getting Started')).toBeVisible();
    });
  });

  test.describe('Enhanced Filtering System', () => {
    test('should toggle filters panel with animation', async ({ page }) => {
      // Find and click the show filters button
      const showFiltersBtn = page.locator('button:has-text("Show Filters")');
      await expect(showFiltersBtn).toBeVisible();
      await showFiltersBtn.click();
      
      // Wait for animation to complete
      await page.waitForTimeout(500);
      
      // Check that filters panel is now visible
      await expect(page.locator('text=Smart Filters')).toBeVisible();
      await expect(page.locator('[role="textbox"][placeholder*="Search"]')).toBeVisible();
      await expect(page.locator('input[type="number"]')).toBeVisible();
      
      // Verify the button text changed to "Hide Filters"
      await expect(page.locator('button:has-text("Hide Filters")')).toBeVisible();
      
      // Click to hide filters
      await page.locator('button:has-text("Hide Filters")').click();
      await page.waitForTimeout(500);
      
      // Filters should be hidden again
      await expect(page.locator('text=Smart Filters')).not.toBeVisible();
    });

    test('should filter products by search query', async ({ page }) => {
      // Open filters panel
      await page.locator('button:has-text("Show Filters")').click();
      await page.waitForTimeout(300);
      
      // Find and use search input
      const searchInput = page.locator('input[placeholder*="Search Products"]');
      await expect(searchInput).toBeVisible();
      
      // Type a search term
      await searchInput.fill('power drill');
      
      // Wait for debounced search to take effect
      await page.waitForTimeout(600);
      
      // Check that search chip appears
      await expect(page.locator('text=Search: "power drill"')).toBeVisible();
      
      // Verify results are filtered (this depends on actual data)
      const dealCount = page.locator('text=/\\d+ deals found/');
      await expect(dealCount).toBeVisible();
    });

    test('should update minimum savings filter', async ({ page }) => {
      // Open filters panel
      await page.locator('button:has-text("Show Filters")').click();
      await page.waitForTimeout(300);
      
      // Find minimum savings input
      const savingsInput = page.locator('input[type="number"]').first();
      await expect(savingsInput).toBeVisible();
      
      // Clear and set new value
      await savingsInput.fill('500');
      
      // Wait for debounced update
      await page.waitForTimeout(600);
      
      // Check that the filter takes effect
      const dealCount = page.locator('text=/\\d+ deals found/');
      await expect(dealCount).toBeVisible();
    });

    test('should change sort order with animated icon', async ({ page }) => {
      // Find the sort order toggle button
      const sortButton = page.locator('button[title="Sort order"]');
      await expect(sortButton).toBeVisible();
      
      // Check initial sort order indicator
      await expect(page.locator('text=High to Low')).toBeVisible();
      
      // Click to change sort order
      await sortButton.click();
      
      // Wait for animation
      await page.waitForTimeout(300);
      
      // Verify sort order changed
      await expect(page.locator('text=Low to High')).toBeVisible();
      
      // Icon should be rotated (this is visual, hard to test precisely)
      const sortIcon = sortButton.locator('svg');
      await expect(sortIcon).toBeVisible();
    });
  });

  test.describe('Product Comparison Cards', () => {
    test('should display comparison cards with retailer branding', async ({ page }) => {
      // Wait for comparison cards to load
      await page.waitForSelector('[data-testid="price-comparison-card"]', { state: 'visible', timeout: 10000 });
      
      // Check that comparison cards are present
      const comparisonCards = page.locator('[data-testid="price-comparison-card"]');
      await expect(comparisonCards.first()).toBeVisible();
      
      // Verify card contains expected elements
      await expect(page.locator('text=/฿[0-9,]+/')).toBeVisible(); // Price
      await expect(page.locator('[data-testid="retailer-chip"]')).toBeVisible(); // Retailer
      await expect(page.locator('text=/Save.*%/')).toBeVisible(); // Savings percentage
    });

    test('should show loading states with enhanced animations', async ({ page }) => {
      // Trigger a refresh to see loading state
      await page.locator('button:has-text("Refresh Data")').click();
      
      // Check for loading backdrop
      const loadingBackdrop = page.locator('[data-testid="loading-backdrop"]');
      await expect(loadingBackdrop).toBeVisible();
      
      // Check for loading text
      await expect(page.locator('text=Loading price comparisons')).toBeVisible();
      await expect(page.locator('text=/Analyzing deals across \\d+ retailers/')).toBeVisible();
      
      // Wait for loading to complete
      await page.waitForSelector('[data-testid="loading-backdrop"]', { state: 'hidden', timeout: 15000 });
    });
  });

  test.describe('View Mode Switching', () => {
    test('should switch between grid and list views', async ({ page }) => {
      // Ensure we start in grid view
      const gridButton = page.locator('button:has-text("Grid")');
      await gridButton.click();
      
      // Wait for view change
      await page.waitForTimeout(500);
      
      // Switch to list view
      const listButton = page.locator('button:has-text("List")');
      await listButton.click();
      
      // Wait for view change
      await page.waitForTimeout(500);
      
      // List view should be active (button should be highlighted)
      await expect(listButton).toHaveClass(/Mui-selected/);
      
      // Switch to analytics view
      const analyticsButton = page.locator('button:has-text("Analytics")');
      await analyticsButton.click();
      
      // Wait for view change
      await page.waitForTimeout(500);
      
      // Analytics view should show dashboard
      await expect(page.locator('[data-testid="price-tracking-dashboard"]')).toBeVisible();
    });
  });

  test.describe('Responsive Design', () => {
    test('should adapt to mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Check that header elements stack vertically on mobile
      const header = page.locator('[data-testid="enhanced-header"]').first();
      await expect(header).toBeVisible();
      
      // Statistics cards should stack in mobile
      const statsGrid = page.locator('[data-testid="stats-grid"]');
      await expect(statsGrid).toBeVisible();
      
      // Filters should be collapsible on mobile
      const filtersButton = page.locator('button:has-text("Show Filters")');
      await expect(filtersButton).toBeVisible();
    });

    test('should maintain functionality on tablet viewport', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });
      
      // All main elements should still be visible
      await expect(page.locator('text=💰 Smart Price Comparisons')).toBeVisible();
      await expect(page.locator('[data-testid="stats-card"]').first()).toBeVisible();
      
      // View toggle should remain horizontal
      await expect(page.locator('button:has-text("Grid")')).toBeVisible();
      await expect(page.locator('button:has-text("List")')).toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('should show graceful error states', async ({ page }) => {
      // Mock API error response
      await page.route('**/api/price-comparisons-v2/**', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal Server Error' })
        });
      });
      
      // Trigger a refresh to cause error
      await page.locator('button:has-text("Refresh Data")').click();
      
      // Wait for error state
      await page.waitForTimeout(2000);
      
      // Check for error alert
      await expect(page.locator('[role="alert"]')).toBeVisible();
      await expect(page.locator('text=Failed to load price comparisons')).toBeVisible();
    });

    test('should handle empty results gracefully', async ({ page }) => {
      // Mock empty results
      await page.route('**/api/price-comparisons-v2/**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ comparisons: [], total: 0 })
        });
      });
      
      // Trigger refresh
      await page.locator('button:has-text("Refresh Data")').click();
      
      // Wait for results
      await page.waitForTimeout(2000);
      
      // Check for empty state
      await expect(page.locator('text=No price comparisons found')).toBeVisible();
      await expect(page.locator('text=Try adjusting your filters')).toBeVisible();
      await expect(page.locator('button:has-text("Clear Filters")')).toBeVisible();
    });
  });

  test.describe('Performance and Animations', () => {
    test('should have smooth card entrance animations', async ({ page }) => {
      // Wait for cards to be present
      await page.waitForSelector('[data-testid="price-comparison-card"]', { state: 'visible' });
      
      // Cards should have animation classes or data attributes
      const firstCard = page.locator('[data-testid="price-comparison-card"]').first();
      await expect(firstCard).toBeVisible();
      
      // Check for framer-motion presence (indicates animations are working)
      const motionDiv = page.locator('[data-framer-motion]').first();
      await expect(motionDiv).toBeVisible();
    });

    test('should handle rapid filter changes without breaking', async ({ page }) => {
      // Open filters
      await page.locator('button:has-text("Show Filters")').click();
      await page.waitForTimeout(300);
      
      const searchInput = page.locator('input[placeholder*="Search Products"]');
      
      // Rapidly type and clear search terms
      await searchInput.fill('drill');
      await page.waitForTimeout(100);
      await searchInput.fill('saw');
      await page.waitForTimeout(100);
      await searchInput.fill('hammer');
      await page.waitForTimeout(100);
      await searchInput.fill('');
      
      // Wait for all debounced updates to complete
      await page.waitForTimeout(1000);
      
      // Page should still be functional
      await expect(page.locator('text=💰 Smart Price Comparisons')).toBeVisible();
      const dealCount = page.locator('text=/\\d+ deals found/');
      await expect(dealCount).toBeVisible();
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper ARIA labels and roles', async ({ page }) => {
      // Check for proper heading structure
      await expect(page.locator('h1, h2, h3').first()).toBeVisible();
      
      // Check for button accessibility
      const refreshButton = page.locator('button:has-text("Refresh Data")');
      await expect(refreshButton).toHaveAttribute('type', 'button');
      
      // Check for form labels
      await page.locator('button:has-text("Show Filters")').click();
      await page.waitForTimeout(300);
      
      const searchInput = page.locator('input[placeholder*="Search Products"]');
      await expect(searchInput).toBeVisible();
      
      // Alert roles should be present for error/info messages
      const alerts = page.locator('[role="alert"]');
      if (await alerts.count() > 0) {
        await expect(alerts.first()).toBeVisible();
      }
    });

    test('should be keyboard navigable', async ({ page }) => {
      // Tab through interactive elements
      await page.keyboard.press('Tab');
      
      // Should be able to navigate to refresh button
      const refreshButton = page.locator('button:has-text("Refresh Data")');
      await refreshButton.focus();
      await expect(refreshButton).toBeFocused();
      
      // Continue tabbing to other interactive elements
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      
      // Should be able to activate buttons with Enter/Space
      const filtersButton = page.locator('button:has-text("Show Filters")');
      await filtersButton.focus();
      await page.keyboard.press('Enter');
      
      // Filters should open
      await page.waitForTimeout(300);
      await expect(page.locator('text=Smart Filters')).toBeVisible();
    });
  });
});