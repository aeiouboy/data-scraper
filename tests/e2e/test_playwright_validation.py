"""
Playwright E2E validation tests
"""
import pytest
from playwright.async_api import async_playwright, Page, Browser


@pytest.mark.e2e
@pytest.mark.native 
class TestPlaywrightValidation:
    """Playwright E2E validation tests"""
    
    @pytest.fixture(scope="class")
    async def browser(self):
        """Create browser instance for testing"""
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            yield browser
            await browser.close()
            await playwright.stop()
        except Exception as e:
            pytest.skip(f"Playwright not available: {e}")
    
    @pytest.fixture
    async def page(self, browser):
        """Create page instance for testing"""
        page = await browser.new_page()
        yield page
        await page.close()
    
    @pytest.mark.asyncio
    async def test_playwright_basic_functionality(self, page: Page):
        """Test basic Playwright functionality"""
        # Create a simple HTML page
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1 id="title">Native Scraping Test</h1>
            <div class="product">
                <span class="name">Test Product</span>
                <span class="price">฿1,299.99</span>
            </div>
        </body>
        </html>
        """
        
        # Set page content
        await page.set_content(html_content)
        
        # Test element extraction
        title = await page.locator("#title").inner_text()
        assert title == "Native Scraping Test"
        
        product_name = await page.locator(".product .name").inner_text()
        assert product_name == "Test Product"
        
        price = await page.locator(".product .price").inner_text()
        assert price == "฿1,299.99"
    
    @pytest.mark.asyncio
    async def test_playwright_data_extraction(self, page: Page):
        """Test data extraction with Playwright"""
        # Create a product page
        product_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Product Page</title>
        </head>
        <body>
            <div class="product-container">
                <h1 class="product-title">Premium Test Product</h1>
                <div class="price-section">
                    <span class="current-price">฿2,499.99</span>
                    <span class="original-price">฿2,999.99</span>
                </div>
                <div class="brand">PremiumBrand</div>
                <div class="sku">SKU-TEST-123</div>
                <div class="availability">In Stock</div>
                <div class="rating">4.5 stars</div>
                <div class="reviews">123 reviews</div>
            </div>
        </body>
        </html>
        """
        
        await page.set_content(product_html)
        
        # Extract product data
        product_data = {}
        
        product_data['name'] = await page.locator(".product-title").inner_text()
        product_data['price'] = await page.locator(".current-price").inner_text()
        product_data['brand'] = await page.locator(".brand").inner_text()
        product_data['sku'] = await page.locator(".sku").inner_text()
        product_data['availability'] = await page.locator(".availability").inner_text()
        product_data['rating'] = await page.locator(".rating").inner_text()
        product_data['reviews'] = await page.locator(".reviews").inner_text()
        
        # Validate extracted data
        assert product_data['name'] == "Premium Test Product"
        assert product_data['price'] == "฿2,499.99"
        assert product_data['brand'] == "PremiumBrand"
        assert product_data['sku'] == "SKU-TEST-123"
        assert product_data['availability'] == "In Stock"
        assert product_data['rating'] == "4.5 stars"
        assert product_data['reviews'] == "123 reviews"
    
    @pytest.mark.asyncio
    async def test_playwright_navigation_simulation(self, page: Page):
        """Test navigation simulation with Playwright"""
        # Create a category page
        category_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Category Page</title>
        </head>
        <body>
            <h1 class="category-title">Electronics</h1>
            <div class="products">
                <div class="product-item">
                    <a href="/product/1">Product 1</a>
                    <span class="price">฿999.99</span>
                </div>
                <div class="product-item">
                    <a href="/product/2">Product 2</a>
                    <span class="price">฿1,299.99</span>
                </div>
                <div class="product-item">
                    <a href="/product/3">Product 3</a>
                    <span class="price">฿1,599.99</span>
                </div>
            </div>
            <div class="pagination">
                <a href="/category?page=1">1</a>
                <a href="/category?page=2">2</a>
                <a href="/category?page=3">3</a>
            </div>
        </body>
        </html>
        """
        
        await page.set_content(category_html)
        
        # Extract category information
        category_name = await page.locator(".category-title").inner_text()
        assert category_name == "Electronics"
        
        # Extract product links
        product_links = await page.locator(".product-item a").all()
        assert len(product_links) == 3
        
        # Extract product link texts
        product_texts = []
        for link in product_links:
            text = await link.inner_text()
            product_texts.append(text)
        
        assert "Product 1" in product_texts
        assert "Product 2" in product_texts
        assert "Product 3" in product_texts
        
        # Extract pagination links
        pagination_links = await page.locator(".pagination a").all()
        assert len(pagination_links) == 3
    
    @pytest.mark.asyncio
    async def test_playwright_error_handling(self, page: Page):
        """Test error handling with Playwright"""
        # Create a page with missing elements
        incomplete_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Incomplete Page</title>
        </head>
        <body>
            <h1>Product Not Found</h1>
            <div class="error">404 - Product not found</div>
        </body>
        </html>
        """
        
        await page.set_content(incomplete_html)
        
        # Test handling of missing elements
        try:
            # This should not exist
            missing_element = page.locator(".product-title")
            await missing_element.wait_for(timeout=1000)
            assert False, "Should not find missing element"
        except:
            # Expected to fail
            pass
        
        # Test that error element exists
        error_element = await page.locator(".error").inner_text()
        assert "404" in error_element
    
    @pytest.mark.asyncio
    async def test_playwright_performance_measurement(self, page: Page):
        """Test performance measurement with Playwright"""
        # Create a page with dynamic content
        dynamic_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dynamic Page</title>
        </head>
        <body>
            <div id="content">Loading...</div>
            <script>
                setTimeout(() => {
                    document.getElementById('content').innerHTML = 
                        '<h1>Loaded Content</h1><p>Dynamic content loaded successfully</p>';
                }, 100);
            </script>
        </body>
        </html>
        """
        
        await page.set_content(dynamic_html)
        
        # Measure load time
        import time
        start_time = time.time()
        
        # Wait for dynamic content
        await page.wait_for_selector("h1", timeout=5000)
        
        end_time = time.time()
        load_time = end_time - start_time
        
        # Validate content loaded
        content = await page.locator("h1").inner_text()
        assert content == "Loaded Content"
        
        # Load time should be reasonable
        assert load_time < 1.0  # Should load within 1 second
    
    @pytest.mark.asyncio
    async def test_playwright_concurrent_operations(self, page: Page):
        """Test concurrent operations with Playwright"""
        # Create multiple pages to simulate concurrent scraping
        pages = []
        
        try:
            # Create additional pages
            for i in range(3):
                new_page = await page.context.new_page()
                pages.append(new_page)
            
            # Set different content on each page
            for i, test_page in enumerate(pages):
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Page {i+1}</title>
                </head>
                <body>
                    <h1>Product {i+1}</h1>
                    <div class="price">฿{1000 + i*100}.99</div>
                </body>
                </html>
                """
                await test_page.set_content(html)
            
            # Extract data from all pages concurrently
            import asyncio
            
            async def extract_data(test_page, page_id):
                title = await test_page.locator("h1").inner_text()
                price = await test_page.locator(".price").inner_text()
                return {'page': page_id, 'title': title, 'price': price}
            
            # Create concurrent tasks
            tasks = []
            for i, test_page in enumerate(pages):
                task = asyncio.create_task(extract_data(test_page, i+1))
                tasks.append(task)
            
            # Wait for all tasks
            results = await asyncio.gather(*tasks)
            
            # Validate results
            assert len(results) == 3
            assert all('title' in result and 'price' in result for result in results)
            
            # Check specific values
            for i, result in enumerate(results):
                assert result['title'] == f"Product {i+1}"
                assert f"฿{1000 + i*100}.99" in result['price']
        
        finally:
            # Clean up pages
            for test_page in pages:
                await test_page.close()
    
    @pytest.mark.asyncio
    async def test_playwright_form_interaction(self, page: Page):
        """Test form interaction with Playwright"""
        # Create a page with search form
        form_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Search Page</title>
        </head>
        <body>
            <form id="search-form">
                <input type="text" id="search-input" placeholder="Search products...">
                <button type="submit" id="search-button">Search</button>
            </form>
            <div id="results" style="display: none;">
                <h2>Search Results</h2>
                <div class="result">Mock search result</div>
            </div>
            <script>
                document.getElementById('search-form').addEventListener('submit', function(e) {
                    e.preventDefault();
                    document.getElementById('results').style.display = 'block';
                });
            </script>
        </body>
        </html>
        """
        
        await page.set_content(form_html)
        
        # Test form interaction
        await page.fill("#search-input", "power tools")
        await page.click("#search-button")
        
        # Wait for results
        await page.wait_for_selector("#results", state="visible")
        
        # Validate results
        results_visible = await page.locator("#results").is_visible()
        assert results_visible
        
        search_value = await page.locator("#search-input").input_value()
        assert search_value == "power tools"
    
    @pytest.mark.asyncio
    async def test_playwright_screenshot_capability(self, page: Page):
        """Test screenshot capability with Playwright"""
        # Create a visually distinct page
        visual_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Visual Test Page</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .header { background: #3498db; color: white; padding: 20px; }
                .content { background: #ecf0f1; padding: 20px; margin: 20px 0; }
                .price { font-size: 24px; color: #e74c3c; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Native Scraping Test Page</h1>
            </div>
            <div class="content">
                <h2>Product Information</h2>
                <p>Product Name: Test Product</p>
                <p class="price">Price: ฿1,299.99</p>
            </div>
        </body>
        </html>
        """
        
        await page.set_content(visual_html)
        
        # Take screenshot
        screenshot = await page.screenshot()
        
        # Validate screenshot
        assert screenshot is not None
        assert len(screenshot) > 0
        
        # Screenshot should be binary data
        assert isinstance(screenshot, bytes)
    
    @pytest.mark.asyncio
    async def test_playwright_mobile_simulation(self, page: Page):
        """Test mobile device simulation with Playwright"""
        # Set mobile viewport
        await page.set_viewport_size({"width": 375, "height": 667})  # iPhone dimensions
        
        # Create responsive page
        responsive_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mobile Test Page</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { margin: 0; padding: 10px; font-family: Arial, sans-serif; }
                .container { max-width: 100%; }
                .product { border: 1px solid #ddd; padding: 10px; margin: 10px 0; }
                .price { font-size: 18px; color: #e74c3c; }
                @media (max-width: 480px) {
                    .price { font-size: 16px; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Mobile Product View</h1>
                <div class="product">
                    <h2>Mobile Product</h2>
                    <p class="price">฿999.99</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        await page.set_content(responsive_html)
        
        # Test mobile-specific content
        title = await page.locator("h1").inner_text()
        assert title == "Mobile Product View"
        
        product_name = await page.locator(".product h2").inner_text()
        assert product_name == "Mobile Product"
        
        price = await page.locator(".price").inner_text()
        assert price == "฿999.99"
        
        # Validate viewport
        viewport = page.viewport_size
        assert viewport["width"] == 375
        assert viewport["height"] == 667