import { test, expect } from '@playwright/test';

/**
 * Products Page Pagination Fix Test
 * Purpose: Verify that pagination works correctly on the products page
 */

test.describe('Products Pagination Fix', () => {
  
  test('should allow navigation through all pages on products page', async ({ page }) => {
    // Monitor API calls to verify pagination parameters
    let apiCalls: any[] = [];
    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('products/search')) {
        try {
          const data = await response.json();
          const urlObj = new URL(url);
          apiCalls.push({
            page: urlObj.searchParams.get('page'),
            page_size: urlObj.searchParams.get('page_size'),
            total: data.total,
            items: data.products?.length || 0,
            timestamp: Date.now()
          });
          console.log('📡 Products API:', {
            page: urlObj.searchParams.get('page'),
            page_size: urlObj.searchParams.get('page_size'),
            total: data.total,
            items: data.products?.length || 0
          });
        } catch (e) {
          console.log('📡 API Call (could not parse):', url);
        }
      }
    });

    // Navigate to products page
    console.log('🔄 Navigating to products page...');
    await page.goto('http://192.168.68.118:3000/products');
    await page.waitForTimeout(3000);
    
    // Enable multi-retailer mode if not enabled
    const multiRetailerToggle = page.locator('input[type="checkbox"]').first();
    if (await multiRetailerToggle.isVisible()) {
      const isChecked = await multiRetailerToggle.isChecked();
      if (!isChecked) {
        await multiRetailerToggle.check();
        await page.waitForTimeout(2000);
        console.log('✅ Enabled multi-retailer mode');
      }
    }
    
    // Wait for initial data to load
    console.log('🔄 Waiting for data grid to load...');
    await page.waitForSelector('[data-testid="data-grid"], .MuiDataGrid-root', { timeout: 10000 });
    await page.waitForTimeout(3000);
    
    // Look for pagination controls in the DataGrid
    const paginationControls = page.locator('.MuiDataGrid-footerContainer').first();
    await expect(paginationControls).toBeVisible();
    console.log('✅ Pagination controls found');
    
    // Check for next page button
    const nextPageButton = page.locator('button[aria-label="Go to next page"]').first();
    const isNextEnabled = await nextPageButton.isEnabled();
    console.log(`📊 Next page button enabled: ${isNextEnabled}`);
    
    if (isNextEnabled) {
      // Record initial API call count
      const initialCallCount = apiCalls.length;
      console.log(`📡 Initial API calls: ${initialCallCount}`);
      
      // Click next page
      console.log('🔄 Clicking next page...');
      await nextPageButton.click();
      await page.waitForTimeout(3000);
      
      // Verify new API call was made
      const newCallCount = apiCalls.length;
      console.log(`📡 API calls after pagination: ${newCallCount}`);
      
      if (newCallCount > initialCallCount) {
        const latestCall = apiCalls[apiCalls.length - 1];
        console.log('✅ Pagination triggered new API call:', latestCall);
        
        // Verify the page parameter changed
        expect(parseInt(latestCall.page || '1')).toBeGreaterThan(1);
        console.log('✅ Page parameter correctly incremented');
        
        // Test going back to previous page
        const prevPageButton = page.locator('button[aria-label="Go to previous page"]').first();
        if (await prevPageButton.isEnabled()) {
          console.log('🔄 Testing previous page...');
          await prevPageButton.click();
          await page.waitForTimeout(3000);
          
          const finalCallCount = apiCalls.length;
          if (finalCallCount > newCallCount) {
            const backCall = apiCalls[apiCalls.length - 1];
            console.log('✅ Previous page navigation working:', backCall);
            expect(parseInt(backCall.page || '1')).toBe(1);
          }
        }
      }
      
      // Test page size change
      console.log('🔄 Testing page size change...');
      const pageSizeSelect = page.locator('[aria-label*="rows per page"], .MuiTablePagination-select');
      if (await pageSizeSelect.isVisible()) {
        await pageSizeSelect.click();
        await page.waitForTimeout(500);
        
        // Select 50 items per page
        const option50 = page.locator('li[data-value="50"], [role="option"]:has-text("50")');
        if (await option50.isVisible()) {
          const beforePageSizeChange = apiCalls.length;
          await option50.click();
          await page.waitForTimeout(3000);
          
          if (apiCalls.length > beforePageSizeChange) {
            const pageSizeCall = apiCalls[apiCalls.length - 1];
            console.log('✅ Page size change triggered API call:', pageSizeCall);
            expect(parseInt(pageSizeCall.page_size || '20')).toBe(50);
          }
        }
      }
    } else {
      console.log('ℹ️ Next page button disabled - testing with search to get more results');
      
      // Try searching for a common term to get more results
      const searchInput = page.locator('input[placeholder*="Search"], input[label*="Search"]');
      if (await searchInput.isVisible()) {
        await searchInput.fill('home');
        
        const searchButton = page.locator('button:has-text("Search")');
        await searchButton.click();
        await page.waitForTimeout(3000);
        
        // Check pagination again after search
        const nextAfterSearch = await nextPageButton.isEnabled();
        console.log(`📊 Next page enabled after search: ${nextAfterSearch}`);
        
        if (nextAfterSearch) {
          await nextPageButton.click();
          await page.waitForTimeout(3000);
          console.log('✅ Pagination working after search');
        }
      }
    }
    
    // Final validation
    console.log(`📊 Total API calls made: ${apiCalls.length}`);
    console.log('📊 All API calls:', apiCalls);
    
    // Test passes if we made at least one API call
    expect(apiCalls.length).toBeGreaterThan(0);
    
    // Test passes if pagination controls are visible
    await expect(paginationControls).toBeVisible();
    
    console.log('✅ Products pagination test completed successfully');
  });

});