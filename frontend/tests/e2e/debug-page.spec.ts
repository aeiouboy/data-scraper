import { test, expect } from '@playwright/test';

test.describe('Debug Page Content', () => {
  test('should capture page content for debugging', async ({ page }) => {
    await page.goto('/price-comparisons');
    await page.waitForLoadState('networkidle');
    
    // Get the page title
    const title = await page.title();
    console.log('Page title:', title);
    
    // Get the main content
    const bodyText = await page.locator('body').textContent();
    console.log('Body text (first 500 chars):', bodyText?.substring(0, 500));
    
    // Take a screenshot
    await page.screenshot({ path: 'debug-page-screenshot.png' });
    
    // Check if it's a React error page
    const reactError = await page.locator('text=Something went wrong').count();
    console.log('React error count:', reactError);
    
    // Check if it's a 404 page
    const notFound = await page.locator('text=404').count();
    console.log('404 error count:', notFound);
    
    // Check if it's loading
    const loading = await page.locator('text=Loading').count();
    console.log('Loading indicators count:', loading);
    
    // This test always passes - we just want to see what's on the page
    expect(true).toBe(true);
  });
});