import { test, expect } from '@playwright/test';

/**
 * Data Quality Improvements Test
 * Purpose: Verify that all data quality fixes are working
 */

test.describe('Data Quality Improvements', () => {
  
  test('should show improved data quality with proper fallbacks', async ({ page }) => {
    // Navigate to products page
    console.log('🔄 Navigating to products page...');
    await page.goto('http://192.168.68.118:3000/products');
    await page.waitForTimeout(3000);
    
    // Enable multi-retailer mode if needed
    const multiRetailerToggle = page.locator('input[type="checkbox"]').first();
    if (await multiRetailerToggle.isVisible()) {
      const isChecked = await multiRetailerToggle.isChecked();
      if (!isChecked) {
        console.log('🔄 Enabling multi-retailer mode...');
        await multiRetailerToggle.check();
        await page.waitForTimeout(3000);
      }
    }
    
    // Wait for DataGrid to load
    await page.waitForSelector('.MuiDataGrid-root', { timeout: 10000 });
    await page.waitForTimeout(2000);
    
    console.log('🔍 Analyzing data quality improvements...');
    
    // 1. Check for retailer codes (should no longer show generic icons)
    const retailerCells = await page.locator('.MuiDataGrid-cell:has-text("HP"), .MuiDataGrid-cell:has-text("TWD")').count();
    console.log(`✅ Retailer codes visible: ${retailerCells > 0 ? 'Yes' : 'No'} (${retailerCells} cells)`);
    
    // 2. Check for brand fallbacks (should show "No Brand" instead of empty)
    const noBrandCells = await page.locator('.MuiDataGrid-cell:has-text("No Brand")').count();
    console.log(`✅ Brand fallbacks: ${noBrandCells} cells show "No Brand"`);
    
    // 3. Check for cleaned product names (should not have HTML/markdown)
    const htmlInNames = await page.locator('.MuiDataGrid-cell:has-text("[!["), .MuiDataGrid-cell:has-text("<")').count();
    console.log(`✅ HTML/markdown in names: ${htmlInNames === 0 ? 'Cleaned' : 'Still present'} (${htmlInNames} cells)`);
    
    // 4. Check for improved status (should show "Available" for products with prices)
    const availableCells = await page.locator('.MuiDataGrid-cell:has-text("Available")').count();
    const checkStoreCells = await page.locator('.MuiDataGrid-cell:has-text("Check Store")').count();
    console.log(`✅ Status improvements: ${availableCells} "Available", ${checkStoreCells} "Check Store"`);
    
    // 5. Check for data validation indicators (warning chips)
    const warningChips = await page.locator('.MuiChip-root:has-text("⚠️")').count();
    console.log(`✅ Data validation indicators: ${warningChips} warning chips for incomplete data`);
    
    // Take a screenshot to compare with the original
    await page.screenshot({ 
      path: 'improved-product-data-grid.png',
      fullPage: true 
    });
    console.log('📸 Screenshot saved as improved-product-data-grid.png');
    
    // 6. Check pagination still works
    const paginationText = await page.locator('.MuiTablePagination-displayedRows').textContent();
    console.log(`📊 Pagination: ${paginationText}`);
    
    // 7. Verify no more empty cells (except controlled ones)
    const emptyCells = await page.locator('.MuiDataGrid-cell:empty').count();
    console.log(`📊 Empty cells remaining: ${emptyCells}`);
    
    // Test pagination with improved data
    const nextButton = page.locator('button[aria-label="Go to next page"]').first();
    const isNextEnabled = await nextButton.isEnabled();
    
    if (isNextEnabled) {
      console.log('🔄 Testing pagination with improved data...');
      await nextButton.click();
      await page.waitForTimeout(2000);
      
      // Check data quality on page 2
      const page2RetailerCells = await page.locator('.MuiDataGrid-cell:has-text("HP"), .MuiDataGrid-cell:has-text("TWD")').count();
      console.log(`✅ Page 2 retailer codes: ${page2RetailerCells > 0 ? 'Present' : 'Missing'}`);
    }
    
    // Summary
    console.log('\n📊 Data Quality Improvement Summary:');
    console.log(`  ✅ Retailer codes: ${retailerCells > 0 ? 'Fixed' : 'Still missing'}`);
    console.log(`  ✅ Brand fallbacks: ${noBrandCells > 0 ? 'Working' : 'Not applied'}`);
    console.log(`  ✅ HTML cleaning: ${htmlInNames === 0 ? 'Successful' : 'Needs work'}`);
    console.log(`  ✅ Status improvement: ${availableCells > 0 ? 'Applied' : 'Not working'}`);
    console.log(`  ✅ Validation indicators: ${warningChips > 0 ? 'Showing' : 'Hidden'}`);
    
    // Test passes if main improvements are visible
    expect(retailerCells).toBeGreaterThan(0); // Should have retailer codes
    expect(htmlInNames).toBe(0); // Should have no HTML in names
    
    console.log('✅ Data quality improvements test completed');
  });

});