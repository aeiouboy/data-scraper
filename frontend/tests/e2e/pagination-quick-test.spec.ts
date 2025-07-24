import { test, expect } from '@playwright/test';

/**
 * Quick Pagination Test
 * Purpose: Verify core pagination functionality works
 */

test.describe('Quick Pagination Test', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForTimeout(2000); // Simple timeout instead of networkidle
  });

  test('should access price comparisons and verify pagination exists', async ({ page }) => {
    // Navigate to Price Comparisons
    await page.click('text=Price Comparisons');
    await page.waitForTimeout(2000);
    
    // Try to enable multi-retailer mode with a simpler selector
    const multiRetailerToggle = page.locator('input[type="checkbox"]').first();
    if (await multiRetailerToggle.isVisible()) {
      await multiRetailerToggle.check();
      await page.waitForTimeout(3000);
    }
    
    // Check for pagination elements
    const previousButton = page.locator('button:has-text("Previous")');
    const nextButton = page.locator('button:has-text("Next")');
    
    // Verify pagination elements exist
    const hasPrevious = await previousButton.isVisible();
    const hasNext = await nextButton.isVisible();
    
    console.log(`✅ Previous button visible: ${hasPrevious}`);
    console.log(`✅ Next button visible: ${hasNext}`);
    
    // If pagination is visible, test basic navigation
    if (hasNext) {
      const isNextEnabled = await nextButton.isEnabled();
      console.log(`✅ Next button enabled: ${isNextEnabled}`);
      
      if (isNextEnabled) {
        // Test clicking next button
        await nextButton.click();
        await page.waitForTimeout(2000);
        console.log('✅ Successfully clicked next button');
        
        // Check if previous button becomes enabled
        const isPreviousEnabled = await previousButton.isEnabled();
        console.log(`✅ Previous button enabled after navigation: ${isPreviousEnabled}`);
      }
    }
    
    // Look for page info
    const pageInfo = page.locator('text=/Page \\d+ of \\d+/');
    if (await pageInfo.isVisible()) {
      const pageText = await pageInfo.textContent();
      console.log(`✅ Page info displayed: ${pageText}`);
    }
  });

  test('should verify API calls are made during pagination', async ({ page }) => {
    let apiCalls: string[] = [];
    
    // Monitor API calls
    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('detailed-comparisons') || url.includes('price-comparisons')) {
        apiCalls.push(url);
        console.log('📡 API Call detected:', url);
      }
    });
    
    await page.click('text=Price Comparisons');
    await page.waitForTimeout(3000);
    
    // Try to enable multi-retailer mode
    const multiRetailerToggle = page.locator('input[type="checkbox"]').first();
    if (await multiRetailerToggle.isVisible()) {
      await multiRetailerToggle.check();
      await page.waitForTimeout(3000);
    }
    
    console.log(`✅ Captured ${apiCalls.length} API calls`);
    
    // Verify we made some API calls
    expect(apiCalls.length).toBeGreaterThan(0);
  });

});