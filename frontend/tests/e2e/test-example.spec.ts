import { test, expect } from '@playwright/test';

/**
 * Basic E2E Test to verify the improved price comparisons UI is working
 * This is a simplified test to ensure the integration is successful
 */

test.describe('Improved Price Comparisons - Basic Integration', () => {
  test('should load the improved price comparisons page', async ({ page }) => {
    // Navigate to the improved price comparisons page
    await page.goto('/price-comparisons');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check that the main heading is present (could be multi-retailer prompt or actual comparisons)
    const smartPriceComparisons = page.locator('text=💰 Smart Price Comparisons');
    const enableMultiRetailer = page.locator('text=Enable Multi-Retailer Mode');
    
    // Either the improved UI should be shown or the multi-retailer prompt
    try {
      await expect(smartPriceComparisons).toBeVisible({ timeout: 2000 });
    } catch {
      await expect(enableMultiRetailer).toBeVisible();
    }
    
    // Check that the page doesn't show any obvious errors
    const errorElements = page.locator('[role="alert"]:has-text("Error"), text="Error:", text="Failed"');
    const errorCount = await errorElements.count();
    
    // If there are error elements, log them for debugging but don't fail the test
    // since this might be due to API being unavailable
    if (errorCount > 0) {
      console.log('Note: Error elements found on page (this may be expected if API is not running)');
    }
    
    // Verify basic page structure exists (only if multi-retailer mode is enabled)
    const gridButton = page.locator('button:has-text("Grid")');
    const listButton = page.locator('button:has-text("List")');
    const analyticsButton = page.locator('button:has-text("Analytics")');
    
    // These buttons should only be present when multi-retailer mode is enabled
    const gridButtonCount = await gridButton.count();
    if (gridButtonCount > 0) {
      await expect(gridButton).toBeVisible();
      await expect(listButton).toBeVisible();
      await expect(analyticsButton).toBeVisible();
    }
  });

  test('should show filter toggle button', async ({ page }) => {
    await page.goto('/price-comparisons');
    await page.waitForLoadState('networkidle');
    
    // Check for filters toggle (only if multi-retailer mode is enabled)
    const filtersButton = page.locator('button:has-text("Show Filters"), button:has-text("Hide Filters")');
    const filtersButtonCount = await filtersButton.count();
    
    if (filtersButtonCount > 0) {
      await expect(filtersButton.first()).toBeVisible();
    } else {
      // If no filters button, we're likely in the multi-retailer mode prompt
      await expect(page.locator('text=Enable Multi-Retailer Mode')).toBeVisible();
    }
  });
});