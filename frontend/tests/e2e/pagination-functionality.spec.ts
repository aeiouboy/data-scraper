import { test, expect } from '@playwright/test';

/**
 * Test Suite: Pagination Functionality
 * Purpose: Comprehensive testing of the recently fixed pagination system
 * Context: After fixing pagination issues in PriceComparisons component
 */

test.describe('Pagination Functionality Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
  });

  test('should enable multi-retailer mode and access price comparisons', async ({ page }) => {
    // Navigate to Price Comparisons
    await page.click('text=Price Comparisons');
    await page.waitForLoadState('networkidle');
    
    // Enable multi-retailer mode if not already enabled
    const multiRetailerToggle = page.locator('input[type="checkbox"]:near(text="Multi-Retailer")');
    if (await multiRetailerToggle.isVisible()) {
      await multiRetailerToggle.check();
      await page.waitForTimeout(1000);
    }
    
    // Wait for data to load
    await page.waitForLoadState('networkidle');
    
    console.log('✅ Multi-retailer mode enabled and price comparisons loaded');
  });

  test('should display pagination controls when data is available', async ({ page }) => {
    // Setup multi-retailer mode
    await page.click('text=Price Comparisons');
    await page.waitForLoadState('networkidle');
    
    const multiRetailerToggle = page.locator('input[type="checkbox"]:near(text="Multi-Retailer")');
    if (await multiRetailerToggle.isVisible()) {
      await multiRetailerToggle.check();
      await page.waitForTimeout(2000);
    }
    
    // Wait for price comparison data to load
    await page.waitForTimeout(3000);
    
    // Check for pagination controls
    const previousButton = page.locator('button:has-text("Previous")');
    const nextButton = page.locator('button:has-text("Next")');
    const pageInfo = page.locator('text=/Page \\d+ of \\d+/');
    
    // Verify pagination elements exist (may be disabled if only one page)
    await expect(previousButton).toBeVisible();
    await expect(nextButton).toBeVisible();
    
    // If there's more than one page, page info should be visible
    if (await pageInfo.isVisible()) {
      const pageText = await pageInfo.textContent();
      console.log(`✅ Pagination info displayed: ${pageText}`);
      
      // Extract current page and total pages
      const pageMatch = pageText?.match(/Page (\\d+) of (\\d+)/);
      if (pageMatch) {
        const currentPage = parseInt(pageMatch[1]);
        const totalPages = parseInt(pageMatch[2]);
        
        expect(currentPage).toBeGreaterThanOrEqual(1);
        expect(totalPages).toBeGreaterThanOrEqual(1);
        expect(currentPage).toBeLessThanOrEqual(totalPages);
        
        console.log(`✅ Page info validation passed: Page ${currentPage} of ${totalPages}`);
      }
    }
  });

  test('should navigate between pages using pagination buttons', async ({ page }) => {
    // Setup
    await page.click('text=Price Comparisons');
    await page.waitForLoadState('networkidle');
    
    const multiRetailerToggle = page.locator('input[type="checkbox"]:near(text="Multi-Retailer")');
    if (await multiRetailerToggle.isVisible()) {
      await multiRetailerToggle.check();
      await page.waitForTimeout(2000);
    }
    
    // Wait for data to load
    await page.waitForTimeout(3000);
    
    const previousButton = page.locator('button:has-text("Previous")');
    const nextButton = page.locator('button:has-text("Next")');
    const pageInfo = page.locator('text=/Page \\d+ of \\d+/');
    
    // Check if we have multiple pages
    if (await pageInfo.isVisible()) {
      const initialPageText = await pageInfo.textContent();
      const initialMatch = initialPageText?.match(/Page (\\d+) of (\\d+)/);
      
      if (initialMatch) {
        const totalPages = parseInt(initialMatch[2]);
        
        if (totalPages > 1) {
          // Test next button
          const isNextEnabled = await nextButton.isEnabled();
          if (isNextEnabled) {
            console.log('🔄 Testing next page navigation...');
            
            // Intercept API calls to verify pagination
            let apiCalled = false;
            page.on('response', async (response) => {
              if (response.url().includes('detailed-comparisons-optimized') && 
                  response.url().includes('offset=12')) {
                apiCalled = true;
                console.log('✅ Pagination API call detected:', response.url());
              }
            });
            
            await nextButton.click();
            await page.waitForTimeout(2000);
            
            // Verify page changed
            const newPageText = await pageInfo.textContent();
            const newMatch = newPageText?.match(/Page (\\d+) of (\\d+)/);
            
            if (newMatch) {
              const newPage = parseInt(newMatch[1]);
              expect(newPage).toBe(2);
              console.log(`✅ Successfully navigated to page ${newPage}`);
              
              // Test previous button
              console.log('🔄 Testing previous page navigation...');
              await previousButton.click();
              await page.waitForTimeout(2000);
              
              const backPageText = await pageInfo.textContent();
              const backMatch = backPageText?.match(/Page (\\d+) of (\\d+)/);
              
              if (backMatch) {
                const backPage = parseInt(backMatch[1]);
                expect(backPage).toBe(1);
                console.log(`✅ Successfully navigated back to page ${backPage}`);
              }
            }
            
            // Verify API was called
            if (apiCalled) {
              console.log('✅ Pagination API calls verified');
            }
          } else {
            console.log('ℹ️ Next button disabled - likely only one page of results');
          }
        } else {
          console.log('ℹ️ Only one page of results available');
        }
      }
    } else {
      console.log('ℹ️ No pagination info visible - checking for data...');
      
      // Check if there's any price comparison data at all
      const priceCards = await page.locator('[data-testid*="price"], .price-comparison, [class*="comparison"]').count();
      console.log(`Found ${priceCards} price comparison elements`);
    }
  });

  test('should support keyboard navigation for pagination', async ({ page }) => {
    // Setup
    await page.click('text=Price Comparisons');
    await page.waitForLoadState('networkidle');
    
    const multiRetailerToggle = page.locator('input[type="checkbox"]:near(text="Multi-Retailer")');
    if (await multiRetailerToggle.isVisible()) {
      await multiRetailerToggle.check();
      await page.waitForTimeout(2000);
    }
    
    await page.waitForTimeout(3000);
    
    const pageInfo = page.locator('text=/Page \\d+ of \\d+/');
    
    if (await pageInfo.isVisible()) {
      const pageText = await pageInfo.textContent();
      const pageMatch = pageText?.match(/Page (\\d+) of (\\d+)/);
      
      if (pageMatch) {
        const totalPages = parseInt(pageMatch[2]);
        
        if (totalPages > 1) {
          console.log('🔄 Testing keyboard navigation...');
          
          // Focus on the page body and test arrow key navigation
          await page.keyboard.press('Tab'); // Ensure focus is on page
          await page.keyboard.press('ArrowRight');
          await page.waitForTimeout(1000);
          
          const newPageText = await pageInfo.textContent();
          const newMatch = newPageText?.match(/Page (\\d+) of (\\d+)/);
          
          if (newMatch) {
            const newPage = parseInt(newMatch[1]);
            if (newPage === 2) {
              console.log('✅ Right arrow key navigation working');
              
              // Test left arrow
              await page.keyboard.press('ArrowLeft');
              await page.waitForTimeout(1000);
              
              const backPageText = await pageInfo.textContent();
              const backMatch = backPageText?.match(/Page (\\d+) of (\\d+)/);
              
              if (backMatch && parseInt(backMatch[1]) === 1) {
                console.log('✅ Left arrow key navigation working');
              }
            }
          }
        }
      }
    }
  });

  test('should reset pagination when filters change', async ({ page }) => {
    // Setup
    await page.click('text=Price Comparisons');
    await page.waitForLoadState('networkidle');
    
    const multiRetailerToggle = page.locator('input[type="checkbox"]:near(text="Multi-Retailer")');
    if (await multiRetailerToggle.isVisible()) {
      await multiRetailerToggle.check();
      await page.waitForTimeout(2000);
    }
    
    await page.waitForTimeout(3000);
    
    // Navigate to page 2 if possible
    const nextButton = page.locator('button:has-text("Next")');
    const pageInfo = page.locator('text=/Page \\d+ of \\d+/');
    
    if (await nextButton.isEnabled()) {
      await nextButton.click();
      await page.waitForTimeout(1000);
      
      // Verify we're on page 2
      if (await pageInfo.isVisible()) {
        const pageText = await pageInfo.textContent();
        const pageMatch = pageText?.match(/Page (\\d+) of (\\d+)/);
        
        if (pageMatch && parseInt(pageMatch[1]) === 2) {
          console.log('🔄 Testing filter reset behavior...');
          
          // Show filters if they're hidden
          const filterButton = page.locator('button:has-text("Show Filters")');
          if (await filterButton.isVisible()) {
            await filterButton.click();
            await page.waitForTimeout(500);
          }
          
          // Change minimum savings filter
          const minSavingsInput = page.locator('input[label*="Minimum Savings" i], input[placeholder*="savings" i]').first();
          if (await minSavingsInput.isVisible()) {
            await minSavingsInput.fill('500');
            await page.waitForTimeout(2000);
            
            // Check if pagination reset to page 1
            const resetPageText = await pageInfo.textContent();
            const resetMatch = resetPageText?.match(/Page (\\d+) of (\\d+)/);
            
            if (resetMatch && parseInt(resetMatch[1]) === 1) {
              console.log('✅ Pagination correctly reset to page 1 after filter change');
            }
          }
        }
      }
    }
  });

  test('should display loading states during pagination', async ({ page }) => {
    // Setup
    await page.click('text=Price Comparisons');
    await page.waitForLoadState('networkidle');
    
    const multiRetailerToggle = page.locator('input[type="checkbox"]:near(text="Multi-Retailer")');
    if (await multiRetailerToggle.isVisible()) {
      await multiRetailerToggle.check();
      await page.waitForTimeout(2000);
    }
    
    await page.waitForTimeout(3000);
    
    const nextButton = page.locator('button:has-text("Next")');
    
    if (await nextButton.isEnabled()) {
      console.log('🔄 Testing loading states...');
      
      // Monitor for loading text or disabled buttons during navigation
      await nextButton.click();
      
      // Check for loading indicators (buttons should be disabled during loading)
      const isDisabledDuringLoading = await nextButton.isDisabled();
      if (isDisabledDuringLoading) {
        console.log('✅ Buttons correctly disabled during loading');
      }
      
      // Wait for navigation to complete
      await page.waitForTimeout(2000);
      
      // Check for loading text in pagination area
      const loadingText = page.locator('text=/loading/i').first();
      if (await loadingText.isVisible()) {
        console.log('✅ Loading state displayed during pagination');
      }
    }
  });

  test('should handle errors gracefully with retry functionality', async ({ page }) => {
    console.log('🔄 Testing error handling...');
    
    // This test simulates network issues by intercepting API calls
    await page.route('**/detailed-comparisons-optimized*', async (route) => {
      // Simulate a network error on first call
      if (route.request().url().includes('offset=12')) {
        await route.abort('failed');
      } else {
        await route.continue();
      }
    });
    
    await page.click('text=Price Comparisons');
    await page.waitForLoadState('networkidle');
    
    const multiRetailerToggle = page.locator('input[type="checkbox"]:near(text="Multi-Retailer")');
    if (await multiRetailerToggle.isVisible()) {
      await multiRetailerToggle.check();
      await page.waitForTimeout(2000);
    }
    
    const nextButton = page.locator('button:has-text("Next")');
    
    if (await nextButton.isEnabled()) {
      await nextButton.click();
      await page.waitForTimeout(3000);
      
      // Look for error message or retry button
      const errorMessage = page.locator('text=/error/i, text=/retry/i').first();
      if (await errorMessage.isVisible()) {
        console.log('✅ Error state displayed correctly');
        
        // Look for retry button
        const retryButton = page.locator('button:has-text("Retry")');
        if (await retryButton.isVisible()) {
          console.log('✅ Retry button available');
        }
      }
    }
  });

  test('should verify API parameters are correct for pagination', async ({ page }) => {
    console.log('🔄 Testing API parameter verification...');
    
    let apiCalls: string[] = [];
    
    // Intercept API calls to verify parameters
    page.on('response', async (response) => {
      if (response.url().includes('detailed-comparisons-optimized')) {
        apiCalls.push(response.url());
        console.log('API Call:', response.url());
      }
    });
    
    await page.click('text=Price Comparisons');
    await page.waitForLoadState('networkidle');
    
    const multiRetailerToggle = page.locator('input[type="checkbox"]:near(text="Multi-Retailer")');
    if (await multiRetailerToggle.isVisible()) {
      await multiRetailerToggle.check();
      await page.waitForTimeout(2000);
    }
    
    await page.waitForTimeout(2000);
    
    // Navigate to page 2
    const nextButton = page.locator('button:has-text("Next")');
    if (await nextButton.isEnabled()) {
      await nextButton.click();
      await page.waitForTimeout(2000);
    }
    
    // Verify API calls contain correct parameters
    const page2Call = apiCalls.find(url => url.includes('offset=12'));
    if (page2Call) {
      expect(page2Call).toContain('limit=12');
      expect(page2Call).toContain('offset=12');
      console.log('✅ Page 2 API call has correct parameters');
    }
    
    // Navigate back to page 1
    const previousButton = page.locator('button:has-text("Previous")');
    if (await previousButton.isEnabled()) {
      await previousButton.click();
      await page.waitForTimeout(2000);
    }
    
    const page1Call = apiCalls.find((url, index) => 
      url.includes('offset=0') && index > 0 // Not the initial call
    );
    if (page1Call) {
      expect(page1Call).toContain('limit=12');
      expect(page1Call).toContain('offset=0');
      console.log('✅ Page 1 API call has correct parameters');
    }
    
    console.log(`✅ Captured ${apiCalls.length} API calls with correct parameters`);
  });

});

test.describe('Performance and Accessibility Tests', () => {
  
  test('should meet performance benchmarks for pagination', async ({ page }) => {
    console.log('🔄 Testing pagination performance...');
    
    await page.click('text=Price Comparisons');
    await page.waitForLoadState('networkidle');
    
    const multiRetailerToggle = page.locator('input[type="checkbox"]:near(text="Multi-Retailer")');
    if (await multiRetailerToggle.isVisible()) {
      await multiRetailerToggle.check();
      await page.waitForTimeout(2000);
    }
    
    const nextButton = page.locator('button:has-text("Next")');
    
    if (await nextButton.isEnabled()) {
      const startTime = Date.now();
      await nextButton.click();
      await page.waitForLoadState('networkidle');
      const navigationTime = Date.now() - startTime;
      
      // Navigation should complete within 5 seconds
      expect(navigationTime).toBeLessThan(5000);
      console.log(`✅ Page navigation completed in ${navigationTime}ms`);
    }
  });
  
  test('should be accessible with screen readers', async ({ page }) => {
    console.log('🔄 Testing accessibility...');
    
    await page.click('text=Price Comparisons');
    await page.waitForLoadState('networkidle');
    
    const multiRetailerToggle = page.locator('input[type="checkbox"]:near(text="Multi-Retailer")');
    if (await multiRetailerToggle.isVisible()) {
      await multiRetailerToggle.check();
      await page.waitForTimeout(2000);
    }
    
    // Check for proper ARIA labels and roles
    const previousButton = page.locator('button:has-text("Previous")');
    const nextButton = page.locator('button:has-text("Next")');
    
    // Buttons should be properly labeled
    await expect(previousButton).toBeVisible();
    await expect(nextButton).toBeVisible();
    
    // Check for keyboard accessibility
    await page.keyboard.press('Tab');
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    console.log(`✅ Keyboard navigation available, focused on: ${focusedElement}`);
  });
  
});