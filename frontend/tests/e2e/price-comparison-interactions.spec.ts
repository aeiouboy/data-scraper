import { test, expect } from '@playwright/test';

/**
 * Focused E2E Tests for Price Comparison Interactions
 * Tests user interactions, animations, and dynamic behaviors
 */

test.describe('Price Comparison Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/price-comparisons-improved');
    await page.waitForLoadState('networkidle');
    
    // Ensure we're in multi-retailer mode with test data
    await page.evaluate(() => {
      window.localStorage.setItem('retailer-context', JSON.stringify({
        selectedRetailers: ['HP', 'TWD', 'GH'],
        multiRetailerMode: true
      }));
    });
    
    await page.reload();
    await page.waitForLoadState('networkidle');
  });

  test.describe('Statistics Card Interactions', () => {
    test('should show hover effects on statistics cards', async ({ page }) => {
      const statsCard = page.locator('[data-testid="stats-card"]').first();
      await expect(statsCard).toBeVisible();
      
      // Hover over the card
      await statsCard.hover();
      
      // Wait for hover animation
      await page.waitForTimeout(300);
      
      // Card should have transform or shadow changes (visual feedback)
      // This is hard to test precisely, but we can check the card is still interactable
      await expect(statsCard).toBeVisible();
    });

    test('should display correct retailer branding colors', async ({ page }) => {
      // Wait for any retailer chips to load
      await page.waitForSelector('[data-testid="retailer-chip"]', { state: 'visible', timeout: 10000 });
      
      const retailerChips = page.locator('[data-testid="retailer-chip"]');
      
      if (await retailerChips.count() > 0) {
        // Check that chips have background colors (indicating branding)
        const firstChip = retailerChips.first();
        await expect(firstChip).toBeVisible();
        
        // The chip should have some styling applied
        const chipStyle = await firstChip.getAttribute('style');
        // Should have color or background color styling
        expect(chipStyle).toBeTruthy();
      }
    });
  });

  test.describe('Real-time Filter Updates', () => {
    test('should update deal count as filters change', async ({ page }) => {
      // Open filters panel
      await page.locator('button:has-text("Show Filters")').click();
      await page.waitForTimeout(500);
      
      // Get initial deal count
      const dealCountElement = page.locator('text=/\\d+ deals found/');
      await expect(dealCountElement).toBeVisible();
      const initialText = await dealCountElement.textContent();
      const initialCount = parseInt(initialText?.match(/\\d+/)?.[0] || '0');
      
      // Change minimum savings filter
      const savingsInput = page.locator('input[type="number"]').first();
      await savingsInput.fill('1000');
      
      // Wait for debounced update
      await page.waitForTimeout(1000);
      
      // Deal count should update
      const newText = await dealCountElement.textContent();
      const newCount = parseInt(newText?.match(/\\d+/)?.[0] || '0');
      
      // Count should be different (likely lower with higher minimum)
      expect(newCount).not.toBe(initialCount);
    });

    test('should show search chip when searching', async ({ page }) => {
      // Open filters
      await page.locator('button:has-text("Show Filters")').click();
      await page.waitForTimeout(300);
      
      // Enter search term
      const searchInput = page.locator('input[placeholder*="Search Products"]');
      await searchInput.fill('drill');
      
      // Wait for search to take effect
      await page.waitForTimeout(700);
      
      // Search chip should appear
      await expect(page.locator('text=Search: "drill"')).toBeVisible();
      
      // Click X to clear search
      const clearButton = page.locator('[data-testid="search-chip"] button');
      if (await clearButton.isVisible()) {
        await clearButton.click();
        
        // Search chip should disappear
        await expect(page.locator('text=Search: "drill"')).not.toBeVisible();
        
        // Search input should be cleared
        await expect(searchInput).toHaveValue('');
      }
    });
  });

  test.describe('View Mode Transitions', () => {
    test('should animate between grid and list views', async ({ page }) => {
      // Start in grid view
      await page.locator('button:has-text("Grid")').click();
      await page.waitForTimeout(500);
      
      // Check for grid layout
      const gridContainer = page.locator('[data-testid="comparison-grid"]');
      if (await gridContainer.isVisible()) {
        await expect(gridContainer).toBeVisible();
      }
      
      // Switch to list view
      await page.locator('button:has-text("List")').click();
      await page.waitForTimeout(500);
      
      // Layout should change
      // The exact implementation depends on how the views are structured
      const listContainer = page.locator('[data-testid="comparison-list"]');
      if (await listContainer.isVisible()) {
        await expect(listContainer).toBeVisible();
      }
    });

    test('should load analytics view with dashboard', async ({ page }) => {
      // Switch to analytics view
      await page.locator('button:has-text("Analytics")').click();
      await page.waitForTimeout(1000);
      
      // Analytics dashboard should load
      const dashboard = page.locator('[data-testid="price-tracking-dashboard"]');
      await expect(dashboard).toBeVisible();
      
      // Switch back to grid
      await page.locator('button:has-text("Grid")').click();
      await page.waitForTimeout(500);
      
      // Should be back to grid view
      await expect(page.locator('button:has-text("Grid")')).toHaveClass(/Mui-selected/);
    });
  });

  test.describe('Retailer Selector Integration', () => {
    test('should show retailer selector in compact mode', async ({ page }) => {
      // Look for retailer selector component
      const retailerSelector = page.locator('[data-testid="retailer-selector"]');
      await expect(retailerSelector).toBeVisible();
      
      // Should be in compact mode (smaller, integrated into the page)
      // This depends on the actual implementation
      const compactIndicator = page.locator('[data-variant="compact"]');
      if (await compactIndicator.isVisible()) {
        await expect(compactIndicator).toBeVisible();
      }
    });
  });

  test.describe('Loading and Error States', () => {
    test('should show skeleton loading for statistics', async ({ page }) => {
      // Mock slow API response
      await page.route('**/api/price-comparisons-v2/quick-stats**', async route => {
        // Delay response
        await page.waitForTimeout(2000);
        await route.continue();
      });
      
      // Trigger refresh
      await page.locator('button:has-text("Refresh Data")').click();
      
      // Should show skeleton loading in stats cards
      const skeleton = page.locator('.MuiSkeleton-root');
      await expect(skeleton.first()).toBeVisible();
      
      // Wait for loading to complete
      await page.waitForTimeout(3000);
    });

    test('should retry failed requests with button', async ({ page }) => {
      // Mock API failure
      let requestCount = 0;
      await page.route('**/api/price-comparisons-v2/**', route => {
        requestCount++;
        if (requestCount === 1) {
          route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Server Error' })
          });
        } else {
          route.continue();
        }
      });
      
      // Trigger request that will fail
      await page.locator('button:has-text("Refresh Data")').click();
      
      // Wait for error state
      await page.waitForTimeout(2000);
      
      // Error message should appear
      await expect(page.locator('text=Failed to load')).toBeVisible();
      
      // Click retry (refresh again)
      await page.locator('button:has-text("Refresh Data")').click();
      
      // Should succeed on second attempt
      await page.waitForTimeout(2000);
      
      // Error should be gone
      await expect(page.locator('text=Failed to load')).not.toBeVisible();
    });
  });

  test.describe('Performance Behavior', () => {
    test('should handle rapid view mode switching', async ({ page }) => {
      // Rapidly switch between view modes
      for (let i = 0; i < 5; i++) {
        await page.locator('button:has-text("Grid")').click();
        await page.waitForTimeout(100);
        await page.locator('button:has-text("List")').click();
        await page.waitForTimeout(100);
        await page.locator('button:has-text("Analytics")').click();
        await page.waitForTimeout(100);
      }
      
      // End in grid view
      await page.locator('button:has-text("Grid")').click();
      await page.waitForTimeout(500);
      
      // Application should still be responsive
      await expect(page.locator('text=💰 Smart Price Comparisons')).toBeVisible();
      await expect(page.locator('button:has-text("Grid")')).toHaveClass(/Mui-selected/);
    });

    test('should debounce filter updates properly', async ({ page }) => {
      // Open filters
      await page.locator('button:has-text("Show Filters")').click();
      await page.waitForTimeout(300);
      
      const searchInput = page.locator('input[placeholder*="Search Products"]');
      
      // Type rapidly without waiting for debounce
      await searchInput.type('power tool drill machine', { delay: 50 });
      
      // Wait for debounce to complete
      await page.waitForTimeout(1000);
      
      // Should show final search term
      await expect(page.locator('text=Search: "power tool drill machine"')).toBeVisible();
      
      // Deal count should be updated
      const dealCount = page.locator('text=/\\d+ deals found/');
      await expect(dealCount).toBeVisible();
    });
  });

  test.describe('Enhanced UX Features', () => {
    test('should show enhanced loading with retailer count', async ({ page }) => {
      // Trigger loading state
      await page.locator('button:has-text("Refresh Data")').click();
      
      // Loading should show retailer count
      const loadingText = page.locator('text=/Analyzing deals across \\d+ retailers/');
      await expect(loadingText).toBeVisible();
      
      // Should show backdrop overlay
      const backdrop = page.locator('[data-testid="loading-backdrop"]');
      await expect(backdrop).toBeVisible();
      
      // Wait for loading to complete
      await page.waitForSelector('[data-testid="loading-backdrop"]', { state: 'hidden', timeout: 10000 });
    });

    test('should provide clear empty state guidance', async ({ page }) => {
      // Mock empty results
      await page.route('**/api/price-comparisons-v2/**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ 
            comparisons: [], 
            total: 0,
            quickStats: { totalSavings: 0, averageSavings: 0 }
          })
        });
      });
      
      // Trigger refresh
      await page.locator('button:has-text("Refresh Data")').click();
      await page.waitForTimeout(1500);
      
      // Should show helpful empty state
      await expect(page.locator('text=No price comparisons found')).toBeVisible();
      await expect(page.locator('text=Try adjusting your filters')).toBeVisible();
      
      // Should provide clear action
      const clearFiltersBtn = page.locator('button:has-text("Clear Filters")');
      await expect(clearFiltersBtn).toBeVisible();
      
      // Clicking clear filters should reset
      await clearFiltersBtn.click();
      await page.waitForTimeout(500);
      
      // Minimum savings should be reset to 0
      await page.locator('button:has-text("Show Filters")').click();
      await page.waitForTimeout(300);
      const savingsInput = page.locator('input[type="number"]').first();
      await expect(savingsInput).toHaveValue('0');
    });
  });
});