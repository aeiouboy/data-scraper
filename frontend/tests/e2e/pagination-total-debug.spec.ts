import { test, expect } from '@playwright/test';

/**
 * Pagination Total Debug Test
 * Purpose: Track exactly which API response affects the pagination display
 */

test.describe('Pagination Total Debug', () => {
  
  test('should track API responses and UI pagination updates', async ({ page }) => {
    // Monitor all API responses
    let apiResponses: any[] = [];
    
    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('products/search')) {
        try {
          const data = await response.json();
          const timestamp = Date.now();
          apiResponses.push({
            timestamp,
            total: data.total,
            items: data.products?.length || 0,
            url: url
          });
          console.log(`📡 API Response ${apiResponses.length}: Total=${data.total}, Items=${data.products?.length || 0}`);
        } catch (e) {
          console.log('📡 API Response (could not parse):', url);
        }
      }
    });

    // Navigate and wait for initial load
    console.log('🔄 Navigating to products page...');
    await page.goto('http://192.168.68.118:3000/products');
    await page.waitForTimeout(3000);
    
    // Check initial pagination
    let paginationText = page.locator('.MuiTablePagination-displayedRows');
    if (await paginationText.isVisible()) {
      const initialPagination = await paginationText.textContent();
      console.log(`📊 Initial pagination: ${initialPagination}`);
    }
    
    // Check multi-retailer toggle state
    const multiRetailerToggle = page.locator('input[type="checkbox"]').first();
    const isInitiallyChecked = await multiRetailerToggle.isChecked();
    console.log(`📊 Multi-retailer initially: ${isInitiallyChecked}`);
    
    if (!isInitiallyChecked) {
      console.log('🔄 Enabling multi-retailer mode...');
      await multiRetailerToggle.check();
      await page.waitForTimeout(4000); // Wait longer for multi-retailer data
      
      // Check pagination after enabling multi-retailer
      if (await paginationText.isVisible()) {
        const afterTogglePagination = await paginationText.textContent();
        console.log(`📊 After multi-retailer toggle: ${afterTogglePagination}`);
      }
    }
    
    // Wait for any additional requests
    await page.waitForTimeout(2000);
    
    // Final pagination check
    if (await paginationText.isVisible()) {
      const finalPagination = await paginationText.textContent();
      console.log(`📊 Final pagination: ${finalPagination}`);
    }
    
    // Summary of all API responses
    console.log('\n📊 API Response Timeline:');
    apiResponses.forEach((response, index) => {
      const timeFromStart = index === 0 ? 0 : response.timestamp - apiResponses[0].timestamp;
      console.log(`  ${index + 1}. [+${timeFromStart}ms] Total: ${response.total}, Items: ${response.items}`);
    });
    
    // Extract totals from pagination text
    const currentPagination = await paginationText.textContent();
    const paginationMatch = currentPagination?.match(/(\d+)–(\d+) of (\d+)/);
    
    if (paginationMatch) {
      const [, start, end, total] = paginationMatch;
      console.log(`\n📊 UI Pagination Analysis:`);
      console.log(`  Showing: ${start}–${end} of ${total}`);
      console.log(`  Expected total (HP + TWD): 2973 + 206 = 3179`);
      console.log(`  Actual UI total: ${total}`);
      console.log(`  Match: ${total === '3179' ? '✅' : '❌'}`);
      
      // Find which API response matches the UI total
      const matchingResponse = apiResponses.find(r => r.total.toString() === total);
      if (matchingResponse) {
        const responseIndex = apiResponses.indexOf(matchingResponse);
        console.log(`  UI is using API response #${responseIndex + 1}`);
      } else {
        console.log(`  ⚠️ No API response matches UI total of ${total}`);
      }
    }
    
    // Test passes if we have pagination and API responses
    expect(apiResponses.length).toBeGreaterThan(0);
    await expect(paginationText).toBeVisible();
  });

});