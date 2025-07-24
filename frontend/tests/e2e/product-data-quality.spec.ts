import { test, expect } from '@playwright/test';

/**
 * Product Data Quality Test
 * Purpose: Check for missing/null values in product fields
 */

test.describe('Product Data Quality Check', () => {
  
  test('should examine product data fields for null values', async ({ page }) => {
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
    
    // Take a screenshot of the data grid
    await page.screenshot({ 
      path: 'product-data-grid.png',
      fullPage: true 
    });
    console.log('📸 Screenshot saved as product-data-grid.png');
    
    // Count cells with specific content
    const cells = await page.locator('.MuiDataGrid-cell').all();
    console.log(`📊 Total cells found: ${cells.length}`);
    
    // Check for null/empty values in different columns
    const nullValues = {
      sku: 0,
      brand: 0,
      category: 0,
      price: 0,
      status: 0,
      total: 0
    };
    
    // Check for "-" or "N/A" values (common null indicators)
    const dashCells = await page.locator('.MuiDataGrid-cell:has-text("-")').count();
    const naCells = await page.locator('.MuiDataGrid-cell:has-text("N/A")').count();
    const unknownCells = await page.locator('.MuiDataGrid-cell:has-text("Unknown")').count();
    
    console.log(`\n📊 Data Quality Analysis:`);
    console.log(`  Cells with "-": ${dashCells}`);
    console.log(`  Cells with "N/A": ${naCells}`);
    console.log(`  Cells with "Unknown": ${unknownCells}`);
    
    // Get sample rows to examine data quality
    const rows = await page.locator('.MuiDataGrid-row').all();
    const maxRowsToCheck = Math.min(10, rows.length);
    
    console.log(`\n🔍 Examining first ${maxRowsToCheck} rows for data quality:`);
    
    for (let i = 0; i < maxRowsToCheck; i++) {
      const row = rows[i];
      const cells = await row.locator('.MuiDataGrid-cell').all();
      
      console.log(`\n📋 Row ${i + 1}:`);
      
      // Get text from each cell
      const cellTexts = [];
      for (const cell of cells) {
        const text = await cell.textContent();
        cellTexts.push(text || 'EMPTY');
      }
      
      // Analyze the row data
      const hasNullValues = cellTexts.some(text => 
        text === '-' || 
        text === 'N/A' || 
        text === 'Unknown' || 
        text === 'EMPTY' ||
        text === ''
      );
      
      if (hasNullValues) {
        console.log('  ⚠️ Contains null/empty values');
        cellTexts.forEach((text, idx) => {
          if (text === '-' || text === 'N/A' || text === 'Unknown' || text === 'EMPTY' || text === '') {
            console.log(`    Cell ${idx}: "${text}"`);
          }
        });
      } else {
        console.log('  ✅ All fields have values');
      }
      
      // Log sample data
      if (i === 0) {
        console.log('\n📊 Sample row data:');
        cellTexts.forEach((text, idx) => {
          console.log(`  Column ${idx}: ${text}`);
        });
      }
    }
    
    // Check specific columns
    const skuColumn = await page.locator('[data-field="sku"]').count();
    const brandColumn = await page.locator('[data-field="brand"]').count();
    const categoryColumn = await page.locator('[data-field="category"]').count();
    const priceColumns = await page.locator('[data-field*="price"]').count();
    
    console.log(`\n📊 Column Analysis:`);
    console.log(`  SKU cells: ${skuColumn}`);
    console.log(`  Brand cells: ${brandColumn}`);
    console.log(`  Category cells: ${categoryColumn}`);
    console.log(`  Price-related cells: ${priceColumns}`);
    
    // Check pagination info
    const paginationText = await page.locator('.MuiTablePagination-displayedRows').textContent();
    console.log(`\n📊 Pagination: ${paginationText}`);
    
    // Final summary
    const totalNullIndicators = dashCells + naCells + unknownCells;
    console.log(`\n📊 Data Quality Summary:`);
    console.log(`  Total null/empty indicators: ${totalNullIndicators}`);
    console.log(`  Percentage of cells with missing data: ${((totalNullIndicators / cells.length) * 100).toFixed(1)}%`);
    
    // Test passes if grid is visible
    await expect(page.locator('.MuiDataGrid-root')).toBeVisible();
  });

});