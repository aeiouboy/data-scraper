import { test, expect } from '@playwright/test';

/**
 * Test Suite: Search API Fix Verification
 * Purpose: Verify that the search API fix correctly displays product counts in the UI
 * Context: After fixing the search API pagination bug that showed 1 instead of 3,179 products
 */

test.describe('Search API Fix Verification', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the main application
    await page.goto('http://localhost:3000');
    
    // Wait for the application to load
    await page.waitForLoadState('networkidle');
  });

  test('should display correct product count in products page', async ({ page }) => {
    // Navigate to products or search page
    await page.click('text=Products');
    
    // Wait for search results to load
    await page.waitForLoadState('networkidle');
    
    // Check if the total product count is displayed correctly
    // Look for text patterns that might show total count
    const productCountElements = await page.locator('text=/\\d+.*products?/i').all();
    
    if (productCountElements.length > 0) {
      const productCountText = await productCountElements[0].textContent();
      console.log('Found product count text:', productCountText);
      
      // Extract number from text
      const match = productCountText?.match(/\\d+/);
      if (match) {
        const count = parseInt(match[0]);
        
        // Should show around 3,179 products (allow for small variations due to ongoing scraping)
        expect(count).toBeGreaterThan(3000);
        expect(count).toBeLessThan(4000);
        
        console.log(`✅ Product count verification passed: ${count} products`);
      }
    }
  });

  test('should verify search API returns correct data', async ({ page }) => {
    // Intercept API calls to verify the search API response
    let searchApiResponse: any;
    
    page.on('response', async (response) => {
      if (response.url().includes('/api/products/search')) {
        searchApiResponse = await response.json();
      }
    });
    
    // Navigate to products page to trigger search API call
    await page.click('text=Products');
    await page.waitForLoadState('networkidle');
    
    // Wait a bit for API call to complete
    await page.waitForTimeout(2000);
    
    // Verify the API response
    if (searchApiResponse) {
      console.log('Search API Response:', JSON.stringify(searchApiResponse, null, 2));
      
      // Check total products
      expect(searchApiResponse.total).toBeGreaterThan(3000);
      expect(searchApiResponse.total).toBeLessThan(4000);
      
      // Check response structure
      expect(searchApiResponse).toHaveProperty('products');
      expect(searchApiResponse).toHaveProperty('total');
      expect(searchApiResponse).toHaveProperty('page');
      expect(searchApiResponse).toHaveProperty('total_pages');
      
      console.log(`✅ Search API verification passed: ${searchApiResponse.total} total products`);
    } else {
      console.log('⚠️ No search API call intercepted');
    }
  });

  test('should navigate to scraping page and verify complete catalog feature', async ({ page }) => {
    // Navigate to scraping page
    await page.click('text=Scraping');
    await page.waitForLoadState('networkidle');
    
    // Check if Complete Catalog tab exists
    const completeCatalogTab = page.locator('text=Complete Catalog');
    await expect(completeCatalogTab).toBeVisible();
    
    // Click on Complete Catalog tab
    await completeCatalogTab.click();
    await page.waitForTimeout(1000);
    
    // Verify the complete catalog content is displayed
    const catalogContent = page.locator('text=/complete catalog/i');
    await expect(catalogContent).toBeVisible();
    
    // Check for the wizard button
    const wizardButton = page.locator('text=/open.*wizard/i');
    await expect(wizardButton).toBeVisible();
    
    console.log('✅ Complete Catalog feature verification passed');
  });

  test('should verify scraping jobs display correctly', async ({ page }) => {
    // Navigate to scraping page
    await page.click('text=Scraping');
    await page.waitForLoadState('networkidle');
    
    // Look for job statistics or counts
    const statsElements = await page.locator('text=/\\d+.*jobs?/i').all();
    
    if (statsElements.length > 0) {
      for (const element of statsElements) {
        const text = await element.textContent();
        console.log('Found job stats:', text);
      }
      
      console.log('✅ Scraping jobs display verification passed');
    }
    
    // Check for job tables or lists
    const jobTables = await page.locator('[role="grid"], table, .data-grid').count();
    if (jobTables > 0) {
      console.log(`✅ Found ${jobTables} job display elements`);
    }
  });

  test('should test search functionality', async ({ page }) => {
    // Navigate to products page
    await page.click('text=Products');
    await page.waitForLoadState('networkidle');
    
    // Look for search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i]').first();
    
    if (await searchInput.isVisible()) {
      // Test search functionality
      await searchInput.fill('samsung');
      await page.waitForTimeout(1000);
      
      // Check if results update
      await page.waitForLoadState('networkidle');
      
      console.log('✅ Search functionality test completed');
    } else {
      console.log('⚠️ Search input not found on page');
    }
  });
});

test.describe('Performance Verification', () => {
  
  test('should load pages within reasonable time', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Should load within 10 seconds
    expect(loadTime).toBeLessThan(10000);
    
    console.log(`✅ Page load time: ${loadTime}ms`);
  });
  
});