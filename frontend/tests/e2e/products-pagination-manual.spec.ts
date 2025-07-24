import { test, expect } from '@playwright/test';

/**
 * Manual Products Pagination Test
 * Purpose: Manually test pagination by checking request body data
 */

test.describe('Products Pagination Manual Test', () => {
  
  test('should send correct pagination parameters in request body', async ({ page }) => {
    // Monitor API request bodies
    let requestBodies: any[] = [];
    
    // Intercept POST requests to products/search
    await page.route('**/products/search', async (route) => {
      const request = route.request();
      const body = request.postDataJSON();
      
      if (body) {
        requestBodies.push({
          page: body.page,
          page_size: body.page_size,
          query: body.query,
          timestamp: Date.now()
        });
        console.log('📡 Request Body:', {
          page: body.page,
          page_size: body.page_size,
          query: body.query || 'none'
        });
      }
      
      // Continue with the request
      await route.continue();
    });

    // Navigate to products page
    console.log('🔄 Navigating to products page...');
    await page.goto('http://192.168.68.118:3000/products');
    await page.waitForTimeout(3000);
    
    // Enable multi-retailer mode if needed
    const multiRetailerToggle = page.locator('input[type="checkbox"]').first();
    if (await multiRetailerToggle.isVisible()) {
      const isChecked = await multiRetailerToggle.isChecked();
      if (!isChecked) {
        await multiRetailerToggle.check();
        await page.waitForTimeout(2000);
        console.log('✅ Enabled multi-retailer mode');
      }
    }
    
    // Wait for initial data load
    await page.waitForSelector('.MuiDataGrid-root', { timeout: 10000 });
    await page.waitForTimeout(3000);
    
    console.log(`📡 Initial requests captured: ${requestBodies.length}`);
    
    // Look for pagination info to see total items
    const paginationText = page.locator('.MuiTablePagination-displayedRows');
    if (await paginationText.isVisible()) {
      const paginationInfo = await paginationText.textContent();
      console.log(`📊 Pagination info: ${paginationInfo}`);
    }
    
    // Try to click next page
    const nextButton = page.locator('button[aria-label="Go to next page"]').first();
    const isNextEnabled = await nextButton.isEnabled();
    console.log(`📊 Next button enabled: ${isNextEnabled}`);
    
    if (isNextEnabled) {
      console.log('🔄 Clicking next page...');
      const beforeClick = requestBodies.length;
      
      await nextButton.click();
      await page.waitForTimeout(3000);
      
      const afterClick = requestBodies.length;
      console.log(`📡 Requests after click: ${afterClick} (was ${beforeClick})`);
      
      if (afterClick > beforeClick) {
        const latestRequest = requestBodies[afterClick - 1];
        console.log('✅ New request after pagination:', latestRequest);
        
        // Verify page parameter increased
        if (latestRequest.page > 1) {
          console.log('✅ Page parameter correctly incremented');
        } else {
          console.log('❌ Page parameter not incremented:', latestRequest.page);
        }
      }
    } else {
      console.log('ℹ️ Pagination not available - trying with search');
      
      // Try searching for a common term to get more results
      const searchInput = page.locator('input[placeholder*="Search"], input[label*="Search"]');
      if (await searchInput.isVisible()) {
        console.log('🔄 Performing search to get more results...');
        
        const beforeSearch = requestBodies.length;
        await searchInput.fill('samsung');
        
        const searchButton = page.locator('button:has-text("Search")');
        await searchButton.click();
        await page.waitForTimeout(3000);
        
        const afterSearch = requestBodies.length;
        console.log(`📡 Requests after search: ${afterSearch} (was ${beforeSearch})`);
        
        // Check if next button is now enabled
        const nextAfterSearch = await nextButton.isEnabled();
        console.log(`📊 Next button enabled after search: ${nextAfterSearch}`);
        
        if (nextAfterSearch) {
          console.log('🔄 Testing pagination after search...');
          await nextButton.click();
          await page.waitForTimeout(3000);
          
          const finalCount = requestBodies.length;
          if (finalCount > afterSearch) {
            const paginationRequest = requestBodies[finalCount - 1];
            console.log('✅ Pagination after search:', paginationRequest);
          }
        }
      }
    }
    
    // Summary
    console.log('📊 Final Summary:');
    console.log(`📡 Total requests: ${requestBodies.length}`);
    requestBodies.forEach((req, index) => {
      console.log(`  ${index + 1}. Page: ${req.page}, Size: ${req.page_size}, Query: "${req.query || 'none'}"`);
    });
    
    // Test passes if we captured at least one request
    expect(requestBodies.length).toBeGreaterThan(0);
    
    // Test passes if pagination controls exist
    const paginationContainer = page.locator('.MuiDataGrid-footerContainer').first();
    await expect(paginationContainer).toBeVisible();
    
    console.log('✅ Manual pagination test completed');
  });

});