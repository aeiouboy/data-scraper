import { test, expect } from '@playwright/test';

/**
 * Request Body Debug Test  
 * Purpose: Check exact request bodies sent during multi-retailer toggle
 */

test.describe('Request Body Debug', () => {
  
  test('should capture exact request bodies during multi-retailer toggle', async ({ page }) => {
    // Monitor request bodies and responses
    let requestData: any[] = [];
    
    await page.route('**/products/search', async (route) => {
      const request = route.request();
      const requestBody = request.postDataJSON();
      
      // Continue request and capture response
      const response = await route.fulfill({
        status: 200,
        body: await (await fetch(request.url(), {
          method: request.method(),
          headers: await request.allHeaders(),
          body: request.postData()
        })).text()
      });
      
      try {
        const responseBody = JSON.parse(await response.text());
        requestData.push({
          timestamp: Date.now(),
          request: requestBody,
          response: {
            total: responseBody.total,
            items: responseBody.products?.length || 0
          }
        });
        
        console.log('\n📡 REQUEST/RESPONSE PAIR:');
        console.log('📤 Request:', JSON.stringify(requestBody, null, 2));
        console.log(`📥 Response: Total=${responseBody.total}, Items=${responseBody.products?.length || 0}`);
        
      } catch (e) {
        console.log('❌ Could not parse response');
      }
    });

    // Navigate and monitor the toggle process
    console.log('🔄 Navigating to products page...');
    await page.goto('http://192.168.68.118:3000/products');
    await page.waitForTimeout(3000);
    
    console.log(`📊 Requests after initial load: ${requestData.length}`);
    
    // Enable multi-retailer mode
    const multiRetailerToggle = page.locator('input[type="checkbox"]').first();
    const isChecked = await multiRetailerToggle.isChecked();
    console.log(`📊 Multi-retailer initially: ${isChecked}`);
    
    if (!isChecked) {
      console.log('🔄 Toggling multi-retailer mode...');
      await multiRetailerToggle.check();
      await page.waitForTimeout(4000);
      
      console.log(`📊 Requests after toggle: ${requestData.length}`);
    }
    
    // Summary
    console.log('\n📊 SUMMARY:');
    requestData.forEach((data, index) => {
      const req = data.request;
      const resp = data.response;
      
      console.log(`\n🔍 API Call #${index + 1}:`);
      console.log(`   Retailer Code: ${req.retailer_code || 'none'}`);
      console.log(`   Retailer Codes: ${req.retailer_codes ? JSON.stringify(req.retailer_codes) : 'none'}`);
      console.log(`   Query: "${req.query || ''}"`);
      console.log(`   Page: ${req.page}, Size: ${req.page_size}`);
      console.log(`   Response Total: ${resp.total}`);
      console.log(`   Expected for these retailers:`);
      
      if (req.retailer_code === 'HP') {
        console.log(`     HP only: 2973 products`);
      } else if (req.retailer_codes) {
        let expectedTotal = 0;
        req.retailer_codes.forEach((code: string) => {
          const counts: Record<string, number> = { HP: 2973, TWD: 206, GH: 0, DH: 0, BT: 0, MH: 0 };
          expectedTotal += counts[code] || 0;
        });
        console.log(`     Total expected: ${expectedTotal} products`);
        console.log(`     Actual: ${resp.total} products`);
        console.log(`     Match: ${expectedTotal === resp.total ? '✅' : '❌'}`);
      }
    });
    
    expect(requestData.length).toBeGreaterThan(0);
  });

});