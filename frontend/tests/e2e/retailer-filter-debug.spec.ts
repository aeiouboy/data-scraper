import { test, expect } from '@playwright/test';

/**
 * Retailer Filter Debug Test
 * Purpose: Check what retailer filters are being sent to the API
 */

test.describe('Retailer Filter Debug', () => {
  
  test('should send correct retailer filters in multi-retailer mode', async ({ page }) => {
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
          retailer_code: body.retailer_code,
          retailer_codes: body.retailer_codes,
          query: body.query || '',
          timestamp: Date.now()
        });
        console.log('📡 Full Request Body:', JSON.stringify(body, null, 2));
      }
      
      // Continue with the request
      await route.continue();
    });

    // Navigate to products page
    console.log('🔄 Navigating to products page...');
    await page.goto('http://192.168.68.118:3000/products');
    await page.waitForTimeout(3000);
    
    // Check current multi-retailer mode status
    const multiRetailerToggle = page.locator('input[type="checkbox"]').first();
    if (await multiRetailerToggle.isVisible()) {
      const isChecked = await multiRetailerToggle.isChecked();
      console.log(`📊 Multi-retailer mode initially: ${isChecked}`);
      
      if (!isChecked) {
        console.log('🔄 Enabling multi-retailer mode...');
        await multiRetailerToggle.check();
        await page.waitForTimeout(3000);
      }
    }
    
    // Check which retailers are selected
    const retailerCards = await page.locator('[class*="retailer"], [data-testid*="retailer"]').count();
    console.log(`📊 Found ${retailerCards} retailer elements`);
    
    // Look for selected retailers in UI
    const selectedRetailers = await page.locator('text=/HomePro.*\d+/, text=/Thai Watsadu.*\d+/').allTextContents();
    console.log('📊 Selected retailers from UI:', selectedRetailers);
    
    // Wait for any pending requests to complete
    await page.waitForTimeout(3000);
    
    // Analyze the requests
    console.log('\n📊 API Request Analysis:');
    console.log(`📡 Total requests captured: ${requestBodies.length}`);
    
    requestBodies.forEach((req, index) => {
      console.log(`\n📡 Request ${index + 1}:`);
      console.log(`  Page: ${req.page}`);
      console.log(`  Page Size: ${req.page_size}`);
      console.log(`  Single Retailer: ${req.retailer_code || 'none'}`);
      console.log(`  Multi Retailer: ${req.retailer_codes ? JSON.stringify(req.retailer_codes) : 'none'}`);
      console.log(`  Query: "${req.query}"`);
    });
    
    // Check pagination info to see actual totals
    const paginationText = page.locator('.MuiTablePagination-displayedRows');
    if (await paginationText.isVisible()) {
      const paginationInfo = await paginationText.textContent();
      console.log(`\n📊 UI Pagination Info: ${paginationInfo}`);
    }
    
    // Test searching for a specific retailer's products
    console.log('\n🔄 Testing search with retailer filter...');
    const searchInput = page.locator('input[placeholder*="Search"], input[label*="Search"]');
    if (await searchInput.isVisible()) {
      const beforeSearch = requestBodies.length;
      await searchInput.fill('samsung');
      
      const searchButton = page.locator('button:has-text("Search")');
      await searchButton.click();
      await page.waitForTimeout(3000);
      
      const afterSearch = requestBodies.length;
      if (afterSearch > beforeSearch) {
        const searchRequest = requestBodies[afterSearch - 1];
        console.log('\n📡 Search request:', searchRequest);
      }
    }
    
    // Summary
    console.log('\n📊 Summary:');
    const hasMultiRetailerRequests = requestBodies.some(req => req.retailer_codes && req.retailer_codes.length > 0);
    const hasSingleRetailerRequests = requestBodies.some(req => req.retailer_code);
    const hasUnfilteredRequests = requestBodies.some(req => !req.retailer_code && (!req.retailer_codes || req.retailer_codes.length === 0));
    
    console.log(`✅ Multi-retailer requests: ${hasMultiRetailerRequests}`);
    console.log(`✅ Single-retailer requests: ${hasSingleRetailerRequests}`);
    console.log(`⚠️ Unfiltered requests: ${hasUnfilteredRequests}`);
    
    // Test passes if we captured requests
    expect(requestBodies.length).toBeGreaterThan(0);
  });

});