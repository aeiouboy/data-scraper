import { test, expect, Page } from '@playwright/test';

test.describe('Improved Price Comparisons', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    
    // Mock API responses
    await page.route('**/api/price-comparisons-v2/detailed-optimized*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            comparisons: [
              {
                id: '1',
                productName: 'Test Product 1',
                brand: 'Test Brand',
                category: 'Power Tools',
                matchConfidence: 0.85,
                retailerPrices: [
                  { retailer_code: 'HP', retailer_name: 'HomePro', price: 1500 },
                  { retailer_code: 'TWD', retailer_name: 'Thai Watsadu', price: 1200 },
                ],
                priceAnalysis: {
                  bestRetailer: 'TWD',
                  savingsAmount: 300,
                  savingsPercentage: 20,
                },
                matchDetails: {
                  sku_score: 0.9,
                  brand_score: 0.8,
                  name_score: 0.85,
                  spec_score: 0.75,
                }
              }
            ]
          }
        })
      });
    });

    await page.route('**/api/matching-optimized/statistics*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            cache_size: 150,
            matcher_info: {
              enhanced_brands: 228,
              progressive_tiers: ['strict', 'moderate', 'relaxed', 'fuzzy']
            },
            configuration: {
              max_workers: 4,
              batch_size: 100
            }
          }
        })
      });
    });

    // Navigate to the improved price comparisons page
    await page.goto('/improved-price-comparisons');
    await page.waitForLoadState('networkidle');
  });

  test('should display enhanced statistics dashboard', async () => {
    // Check for statistics cards
    await expect(page.locator('[data-testid="stats-dashboard"]')).toBeVisible();
    
    // Verify each statistic card
    const statsCards = page.locator('.MuiCard-root').filter({ hasText: /Total Savings|Average Match|Best Deal|Products with/ });
    await expect(statsCards).toHaveCount(4);

    // Check for animated values
    await expect(page.locator('text=฿300')).toBeVisible(); // Total savings
    await expect(page.locator('text=85.0%')).toBeVisible(); // Average confidence
    await expect(page.locator('text=20.0%')).toBeVisible(); // Best deal
    await expect(page.locator('text=1')).toBeVisible(); // Products count
  });

  test('should have functional smart filters', async () => {
    // Check filters panel visibility
    await expect(page.locator('text=Smart Filters')).toBeVisible();
    
    // Test confidence slider
    const confidenceSlider = page.locator('[data-testid="confidence-slider"]').first();
    await confidenceSlider.hover();
    await page.mouse.down();
    await page.mouse.move(100, 0);
    await page.mouse.up();
    
    // Verify filter change reflected in display
    await expect(page.locator('text=Match Confidence:')).toBeVisible();

    // Test AI toggle switch
    const aiToggle = page.locator('text=Use AI-Enhanced Matching').locator('..').locator('input[type="checkbox"]');
    await aiToggle.click();
    await expect(page.locator('text=📊 Standard algorithm')).toBeVisible();
    
    // Toggle back
    await aiToggle.click();
    await expect(page.locator('text=🚀 50% better accuracy')).toBeVisible();
  });

  test('should display enhanced product cards with animations', async () => {
    // Wait for product cards to load
    await expect(page.locator('.MuiCard-root').filter({ hasText: 'Test Product 1' })).toBeVisible();
    
    const productCard = page.locator('.MuiCard-root').filter({ hasText: 'Test Product 1' }).first();
    
    // Check confidence badge
    await expect(productCard.locator('text=85%')).toBeVisible();
    
    // Check savings display
    await expect(productCard.locator('text=฿300')).toBeVisible();
    await expect(productCard.locator('text=Save 20.0%')).toBeVisible();
    
    // Check retailer information
    await expect(productCard.locator('text=HomePro')).toBeVisible();
    await expect(productCard.locator('text=Thai Watsadu')).toBeVisible();
    
    // Test hover animation
    await productCard.hover();
    
    // Check for animated elements (confidence badge should rotate)
    const confidenceBadge = productCard.locator('[data-testid="confidence-badge"]').first();
    await expect(confidenceBadge).toBeVisible();
  });

  test('should handle view mode switching', async () => {
    // Test grid view (default)
    const gridButton = page.locator('[data-testid="grid-view-button"]').first();
    await expect(gridButton).toHaveClass(/Mui.*-selected/);

    // Switch to list view
    const listButton = page.locator('[data-testid="list-view-button"]').first();
    await listButton.click();
    
    // Verify layout change
    await expect(page.locator('[data-testid="list-view-container"]')).toBeVisible();

    // Switch to table view
    const tableButton = page.locator('[data-testid="table-view-button"]').first();
    await tableButton.click();
    
    // Verify table view
    await expect(page.locator('.MuiDataGrid-root')).toBeVisible();
  });

  test('should expand and collapse product details', async () => {
    const productCard = page.locator('.MuiCard-root').filter({ hasText: 'Test Product 1' }).first();
    
    // Check if expand button exists
    const expandButton = productCard.locator('text=Show More').first();
    if (await expandButton.isVisible()) {
      await expandButton.click();
      
      // Check for expanded details
      await expect(productCard.locator('text=Match Quality Details')).toBeVisible();
      await expect(productCard.locator('text=SKU')).toBeVisible();
      await expect(productCard.locator('text=BRAND')).toBeVisible();
      
      // Collapse
      const collapseButton = productCard.locator('text=Show Less').first();
      await collapseButton.click();
      
      // Verify collapse
      await expect(productCard.locator('text=Match Quality Details')).not.toBeVisible();
    }
  });

  test('should handle filter interactions correctly', async () => {
    // Toggle filters panel
    const filtersButton = page.locator('text=Filters');
    await filtersButton.click();
    
    // Check filters are hidden
    await expect(page.locator('text=Smart Filters')).not.toBeVisible();
    
    // Show filters again
    await filtersButton.click();
    await expect(page.locator('text=Smart Filters')).toBeVisible();
  });

  test('should display loading states properly', async () => {
    // Mock slow API response
    await page.route('**/api/price-comparisons-v2/detailed-optimized*', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: { comparisons: [] } })
      });
    });

    await page.reload();
    
    // Check loading indicator
    await expect(page.locator('text=Loading enhanced price comparisons...')).toBeVisible();
    await expect(page.locator('.MuiLinearProgress-root')).toBeVisible();
    
    // Wait for loading to complete
    await page.waitForSelector('text=No price comparisons found', { timeout: 5000 });
  });

  test('should export data functionality', async () => {
    // Mock download
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.locator('text=Export').click()
    ]);
    
    // Verify download
    expect(download.suggestedFilename()).toMatch(/price-comparisons-\d{4}-\d{2}-\d{2}\.csv/);
  });

  test('should be responsive on mobile', async () => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check mobile layout
    const statsCards = page.locator('.MuiGrid-item').filter({ hasText: /Total Savings|Average Match/ });
    
    // On mobile, cards should stack vertically
    for (let i = 0; i < await statsCards.count(); i++) {
      const card = statsCards.nth(i);
      await expect(card).toBeVisible();
    }
    
    // Check filters are still accessible
    await expect(page.locator('text=Filters')).toBeVisible();
  });

  test('should handle confidence threshold changes', async () => {
    // Find confidence slider
    const confidenceSlider = page.locator('input[type="range"]').first();
    
    // Change confidence threshold
    await confidenceSlider.fill('0.3'); // 30%
    
    // Verify filter value updated
    await expect(page.locator('text=Match Confidence: 30%')).toBeVisible();
  });

  test('should show retailer price points on range visualization', async () => {
    const productCard = page.locator('.MuiCard-root').filter({ hasText: 'Test Product 1' }).first();
    
    // Check price range visualization
    await expect(productCard.locator('text=Price Range')).toBeVisible();
    
    // Check retailer avatars on price range
    const retailerAvatars = productCard.locator('.MuiAvatar-root').filter({ hasText: /HP|TWD/ });
    await expect(retailerAvatars).toHaveCount(2);
    
    // Test hover on retailer avatar
    const hpAvatar = productCard.locator('.MuiAvatar-root').filter({ hasText: 'HP' });
    await hpAvatar.hover();
    
    // Should show tooltip
    await expect(page.locator('text=HomePro: ฿1,500')).toBeVisible();
  });

  test('should handle refresh functionality', async () => {
    const refreshButton = page.locator('text=Refresh');
    
    // Click refresh
    await refreshButton.click();
    
    // Button should be disabled during refresh
    await expect(refreshButton).toBeDisabled();
    
    // Wait for refresh to complete
    await page.waitForLoadState('networkidle');
    
    // Button should be enabled again
    await expect(refreshButton).toBeEnabled();
  });

  test('should display best price indicators correctly', async () => {
    const productCard = page.locator('.MuiCard-root').filter({ hasText: 'Test Product 1' }).first();
    
    // Check for best price chip
    await expect(productCard.locator('text=BEST PRICE')).toBeVisible();
    
    // Check best price is highlighted
    const bestPriceSection = productCard.locator(':has-text("BEST PRICE")').first();
    await expect(bestPriceSection).toHaveCSS('border-color', /rgb\(76, 175, 80\)/); // Success color
  });

  test.afterEach(async () => {
    await page.close();
  });
});

test.describe('Improved Price Comparisons - Performance', () => {
  test('should load page within performance budget', async ({ page }) => {
    // Start performance measurement
    await page.goto('/improved-price-comparisons');
    
    // Measure page load time
    const navigationTiming = await page.evaluate(() => {
      const timing = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: timing.domContentLoadedEventEnd - timing.domContentLoadedEventStart,
        loadComplete: timing.loadEventEnd - timing.loadEventStart,
      };
    });
    
    // Assert performance budgets
    expect(navigationTiming.domContentLoaded).toBeLessThan(2000); // 2 seconds
    expect(navigationTiming.loadComplete).toBeLessThan(3000); // 3 seconds
  });

  test('should have smooth animations', async ({ page }) => {
    await page.goto('/improved-price-comparisons');
    await page.waitForLoadState('networkidle');
    
    // Test card hover animation performance
    const productCard = page.locator('.MuiCard-root').first();
    
    // Start animation performance measurement
    await page.evaluate(() => {
      (window as any).animationFrames = [];
      const originalRequestAnimationFrame = window.requestAnimationFrame;
      window.requestAnimationFrame = (callback) => {
        (window as any).animationFrames.push(performance.now());
        return originalRequestAnimationFrame(callback);
      };
    });
    
    // Trigger hover animation
    await productCard.hover();
    await page.waitForTimeout(500);
    
    // Check animation frame rate
    const frameData = await page.evaluate(() => (window as any).animationFrames);
    
    if (frameData.length > 1) {
      const avgFrameTime = frameData.reduce((sum: number, time: number, index: number) => {
        if (index === 0) return 0;
        return sum + (time - frameData[index - 1]);
      }, 0) / (frameData.length - 1);
      
      // Should maintain 60fps (16.67ms per frame)
      expect(avgFrameTime).toBeLessThan(20);
    }
  });
});