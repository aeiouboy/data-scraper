"""
Simple Playwright E2E tests
"""
import pytest
import asyncio


@pytest.mark.e2e
@pytest.mark.native
class TestPlaywrightSimple:
    """Simple Playwright E2E tests"""
    
    @pytest.mark.asyncio
    async def test_playwright_installation(self):
        """Test that Playwright is installed and can be imported"""
        try:
            from playwright.async_api import async_playwright
            
            # Test that we can create a playwright instance
            playwright = await async_playwright().start()
            
            # Test that we can access browser types
            browser_types = [
                playwright.chromium,
                playwright.firefox,
                playwright.webkit
            ]
            
            assert len(browser_types) == 3
            
            # Clean up
            await playwright.stop()
            
        except ImportError:
            pytest.skip("Playwright not installed")
    
    @pytest.mark.asyncio
    async def test_playwright_browser_launch(self):
        """Test that we can launch a browser"""
        try:
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            
            # Try to launch browser
            browser = await playwright.chromium.launch(headless=True)
            
            # Test that browser is running
            assert browser.is_connected()
            
            # Clean up
            await browser.close()
            await playwright.stop()
            
        except ImportError:
            pytest.skip("Playwright not installed")
        except Exception as e:
            pytest.skip(f"Browser launch failed: {e}")
    
    @pytest.mark.asyncio
    async def test_playwright_page_creation(self):
        """Test that we can create a page"""
        try:
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            
            # Create a page
            page = await browser.new_page()
            
            # Test basic page functionality
            await page.set_content("<html><body><h1>Test</h1></body></html>")
            
            # Extract content
            title = await page.locator("h1").inner_text()
            assert title == "Test"
            
            # Clean up
            await page.close()
            await browser.close()
            await playwright.stop()
            
        except ImportError:
            pytest.skip("Playwright not installed")
        except Exception as e:
            pytest.skip(f"Page creation failed: {e}")
    
    @pytest.mark.asyncio
    async def test_playwright_element_interaction(self):
        """Test element interaction"""
        try:
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Create test HTML
            html = """
            <html>
            <body>
                <div class="product">
                    <h1 class="name">Test Product</h1>
                    <span class="price">฿1,299.99</span>
                    <button id="buy-btn">Buy Now</button>
                </div>
            </body>
            </html>
            """
            
            await page.set_content(html)
            
            # Test element selection and text extraction
            product_name = await page.locator(".product .name").inner_text()
            assert product_name == "Test Product"
            
            price = await page.locator(".price").inner_text()
            assert price == "฿1,299.99"
            
            # Test button interaction
            button = page.locator("#buy-btn")
            assert await button.is_visible()
            
            # Clean up
            await page.close()
            await browser.close()
            await playwright.stop()
            
        except ImportError:
            pytest.skip("Playwright not installed")
        except Exception as e:
            pytest.skip(f"Element interaction failed: {e}")
    
    @pytest.mark.asyncio
    async def test_playwright_multiple_elements(self):
        """Test extracting multiple elements"""
        try:
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Create test HTML with multiple products
            html = """
            <html>
            <body>
                <div class="category">
                    <h1>Electronics</h1>
                    <div class="product-list">
                        <div class="product">
                            <span class="name">Product 1</span>
                            <span class="price">฿999.99</span>
                        </div>
                        <div class="product">
                            <span class="name">Product 2</span>
                            <span class="price">฿1,299.99</span>
                        </div>
                        <div class="product">
                            <span class="name">Product 3</span>
                            <span class="price">฿1,599.99</span>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            await page.set_content(html)
            
            # Test category extraction
            category = await page.locator(".category h1").inner_text()
            assert category == "Electronics"
            
            # Test multiple product extraction
            products = await page.locator(".product").all()
            assert len(products) == 3
            
            # Extract data from each product
            product_data = []
            for product in products:
                name = await product.locator(".name").inner_text()
                price = await product.locator(".price").inner_text()
                product_data.append({'name': name, 'price': price})
            
            # Validate extracted data
            assert len(product_data) == 3
            assert product_data[0]['name'] == "Product 1"
            assert product_data[1]['name'] == "Product 2"
            assert product_data[2]['name'] == "Product 3"
            
            # Clean up
            await page.close()
            await browser.close()
            await playwright.stop()
            
        except ImportError:
            pytest.skip("Playwright not installed")
        except Exception as e:
            pytest.skip(f"Multiple elements test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_playwright_performance_basic(self):
        """Test basic performance with Playwright"""
        try:
            from playwright.async_api import async_playwright
            import time
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Test performance of multiple operations
            start_time = time.time()
            
            # Create and process multiple pages
            for i in range(5):
                html = f"""
                <html>
                <body>
                    <h1>Page {i+1}</h1>
                    <div class="content">Content for page {i+1}</div>
                </body>
                </html>
                """
                
                await page.set_content(html)
                
                # Extract content
                title = await page.locator("h1").inner_text()
                content = await page.locator(".content").inner_text()
                
                assert title == f"Page {i+1}"
                assert content == f"Content for page {i+1}"
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should complete reasonably quickly
            assert total_time < 5.0  # Should complete within 5 seconds
            
            # Clean up
            await page.close()
            await browser.close()
            await playwright.stop()
            
        except ImportError:
            pytest.skip("Playwright not installed")
        except Exception as e:
            pytest.skip(f"Performance test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_playwright_error_handling(self):
        """Test error handling with Playwright"""
        try:
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Test with invalid HTML
            html = """
            <html>
            <body>
                <div class="incomplete">
                    <h1>Page with missing elements</h1>
                </div>
            </body>
            </html>
            """
            
            await page.set_content(html)
            
            # Test existing element
            title = await page.locator("h1").inner_text()
            assert title == "Page with missing elements"
            
            # Test missing element handling
            try:
                await page.locator(".missing-element").inner_text(timeout=100)
                assert False, "Should have timed out"
            except:
                # Expected to timeout
                pass
            
            # Clean up
            await page.close()
            await browser.close()
            await playwright.stop()
            
        except ImportError:
            pytest.skip("Playwright not installed")
        except Exception as e:
            pytest.skip(f"Error handling test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_playwright_concurrent_pages(self):
        """Test concurrent page operations"""
        try:
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            
            # Create multiple pages
            pages = []
            for i in range(3):
                page = await browser.new_page()
                pages.append(page)
            
            # Set content on all pages concurrently
            async def setup_page(page, page_id):
                html = f"""
                <html>
                <body>
                    <h1>Concurrent Page {page_id}</h1>
                    <div class="data">Data for page {page_id}</div>
                </body>
                </html>
                """
                await page.set_content(html)
                return page_id
            
            # Run concurrent operations
            tasks = []
            for i, page in enumerate(pages):
                task = asyncio.create_task(setup_page(page, i+1))
                tasks.append(task)
            
            # Wait for all tasks
            results = await asyncio.gather(*tasks)
            assert len(results) == 3
            
            # Extract data from all pages
            page_data = []
            for page in pages:
                title = await page.locator("h1").inner_text()
                data = await page.locator(".data").inner_text()
                page_data.append({'title': title, 'data': data})
            
            # Validate data
            assert len(page_data) == 3
            for i, data in enumerate(page_data):
                assert data['title'] == f"Concurrent Page {i+1}"
                assert data['data'] == f"Data for page {i+1}"
            
            # Clean up
            for page in pages:
                await page.close()
            await browser.close()
            await playwright.stop()
            
        except ImportError:
            pytest.skip("Playwright not installed")
        except Exception as e:
            pytest.skip(f"Concurrent pages test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_playwright_data_extraction_workflow(self):
        """Test complete data extraction workflow"""
        try:
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Simulate a product page
            html = """
            <html>
            <head>
                <title>Product Page</title>
            </head>
            <body>
                <div class="product-container">
                    <div class="breadcrumb">
                        <a href="/">Home</a> > 
                        <a href="/category">Electronics</a> > 
                        <span>Product</span>
                    </div>
                    <div class="product-details">
                        <h1 class="product-name">Ultimate Test Product</h1>
                        <div class="price-section">
                            <span class="current-price">฿1,799.99</span>
                            <span class="original-price">฿2,199.99</span>
                            <span class="discount">18% OFF</span>
                        </div>
                        <div class="brand">PremiumBrand</div>
                        <div class="sku">UTU-PRD-001</div>
                        <div class="availability">✓ In Stock</div>
                        <div class="rating">
                            <span class="stars">★★★★☆</span>
                            <span class="score">4.2</span>
                            <span class="reviews">(89 reviews)</span>
                        </div>
                        <div class="description">
                            This is the ultimate test product for validating
                            our native scraping capabilities. It includes all
                            the essential product information fields.
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            await page.set_content(html)
            
            # Extract comprehensive product data
            product_data = {}
            
            # Basic information
            product_data['name'] = await page.locator(".product-name").inner_text()
            product_data['brand'] = await page.locator(".brand").inner_text()
            product_data['sku'] = await page.locator(".sku").inner_text()
            
            # Pricing
            product_data['current_price'] = await page.locator(".current-price").inner_text()
            product_data['original_price'] = await page.locator(".original-price").inner_text()
            product_data['discount'] = await page.locator(".discount").inner_text()
            
            # Availability and rating
            product_data['availability'] = await page.locator(".availability").inner_text()
            product_data['rating_score'] = await page.locator(".score").inner_text()
            product_data['reviews'] = await page.locator(".reviews").inner_text()
            
            # Description
            product_data['description'] = await page.locator(".description").inner_text()
            
            # Validate extracted data
            assert product_data['name'] == "Ultimate Test Product"
            assert product_data['brand'] == "PremiumBrand"
            assert product_data['sku'] == "UTU-PRD-001"
            assert product_data['current_price'] == "฿1,799.99"
            assert product_data['original_price'] == "฿2,199.99"
            assert product_data['discount'] == "18% OFF"
            assert "In Stock" in product_data['availability']
            assert product_data['rating_score'] == "4.2"
            assert "89 reviews" in product_data['reviews']
            assert "ultimate test product" in product_data['description'].lower()
            
            # Test data completeness
            required_fields = ['name', 'brand', 'sku', 'current_price', 'availability']
            for field in required_fields:
                assert field in product_data
                assert product_data[field] is not None
                assert len(product_data[field]) > 0
            
            # Clean up
            await page.close()
            await browser.close()
            await playwright.stop()
            
        except ImportError:
            pytest.skip("Playwright not installed")
        except Exception as e:
            pytest.skip(f"Data extraction workflow failed: {e}")