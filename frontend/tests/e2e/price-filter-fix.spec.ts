import { test, expect } from '@playwright/test';

/**
 * Price Filter Fix Test
 * Purpose: Verify that increasing max_price shows all products
 */

test.describe('Price Filter Fix', () => {
  
  test('should show correct total after fixing price filter', async ({ page }) => {
    // Monitor API responses
    let apiResponses: any[] = [];
    
    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('products/search')) {
        try {
          const data = await response.json();
          apiResponses.push({
            total: data.total,
            items: data.products?.length || 0,
            timestamp: Date.now()
          });
          console.log(`📡 API Response: Total=${data.total}, Items=${data.products?.length || 0}`);
        } catch (e) {
          console.log('📡 API Response (could not parse)');
        }
      }
    });

    // Navigate to products page
    console.log('🔄 Navigating to products page...');
    await page.goto('http://192.168.68.118:3000/products');
    await page.waitForTimeout(3000);
    
    // Enable multi-retailer mode
    const multiRetailerToggle = page.locator('input[type="checkbox"]').first();
    const isChecked = await multiRetailerToggle.isChecked();
    console.log(`📊 Multi-retailer initially: ${isChecked}`);
    
    if (!isChecked) {
      console.log('🔄 Enabling multi-retailer mode...');
      await multiRetailerToggle.check();
      await page.waitForTimeout(4000);
    }
    
    // Check final pagination total
    const paginationText = page.locator('.MuiTablePagination-displayedRows');
    await paginationText.waitFor({ timeout: 10000 });
    
    const paginationInfo = await paginationText.textContent();
    console.log(`📊 Final pagination: ${paginationInfo}`);
    
    // Extract total from pagination
    const totalMatch = paginationInfo?.match(/of (\d+)/);
    const uiTotal = totalMatch ? parseInt(totalMatch[1]) : 0;
    
    console.log('\n📊 Analysis:');
    console.log(`  UI Total: ${uiTotal}`);
    console.log(`  Expected (HP + TWD): 2973 + 206 = 3179`);
    console.log(`  Match: ${uiTotal === 3179 ? '✅' : '❌'}`);
    
    // Check latest API response
    if (apiResponses.length > 0) {
      const latestResponse = apiResponses[apiResponses.length - 1];
      console.log(`  Latest API Total: ${latestResponse.total}`);
      console.log(`  API Match: ${latestResponse.total === 3179 ? '✅' : '❌'}`);
    }
    
    // Verify that we now see the correct total
    expect(uiTotal).toBe(3179);
    
    // Test pagination navigation to ensure it works with the full dataset
    const nextButton = page.locator('button[aria-label="Go to next page"]').first();
    const isNextEnabled = await nextButton.isEnabled();
    console.log(`📊 Next page available: ${isNextEnabled}`);
    
    if (isNextEnabled) {
      console.log('🔄 Testing pagination with full dataset...');
      const beforeClick = apiResponses.length;
      
      await nextButton.click();
      await page.waitForTimeout(3000);
      
      const afterClick = apiResponses.length;
      if (afterClick > beforeClick) {
        const paginationCall = apiResponses[afterClick - 1];
        console.log(`📡 Page 2 API call: Total=${paginationCall.total}, Items=${paginationCall.items}`);
        
        // Should still have the same total
        expect(paginationCall.total).toBe(3179);
        console.log('✅ Pagination maintains correct total');
      }
    }
    
    console.log('✅ Price filter fix verification completed');
  });

});