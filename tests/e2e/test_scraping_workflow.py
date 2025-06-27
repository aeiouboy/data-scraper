"""
End-to-end tests for scraping workflows
"""
import pytest
import asyncio
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import requests


@pytest.mark.e2e
@pytest.mark.slow
class TestScrapingWorkflowE2E:
    """End-to-end tests for complete scraping workflows"""
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        """Base URL for API endpoints"""
        return "http://localhost:8000/api"
    
    @pytest.fixture(scope="class")
    def frontend_url(self):
        """Base URL for frontend application"""
        return "http://localhost:3000"
    
    @pytest.fixture(scope="class")
    def webdriver(self):
        """Selenium WebDriver instance"""
        options = Options()
        options.add_argument("--headless")  # Run in headless mode for CI
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        
        yield driver
        driver.quit()
    
    def wait_for_api_ready(self, api_base_url, timeout=30):
        """Wait for API to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{api_base_url}/products/filters/brands")
                if response.status_code == 200:
                    return True
            except requests.exceptions.ConnectionError:
                time.sleep(1)
        return False
    
    def wait_for_frontend_ready(self, frontend_url, timeout=30):
        """Wait for frontend to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(frontend_url)
                if response.status_code == 200:
                    return True
            except requests.exceptions.ConnectionError:
                time.sleep(1)
        return False
    
    def test_complete_scraping_workflow_api(self, api_base_url):
        """Test complete scraping workflow via API"""
        # Check if API is ready
        assert self.wait_for_api_ready(api_base_url), "API is not ready"
        
        # Step 1: Create a scraping job
        job_data = {
            "job_type": "category",
            "target_url": "https://www.homepro.co.th/c/tools",
            "max_pages": 2
        }
        
        response = requests.post(f"{api_base_url}/scraping/jobs", json=job_data)
        assert response.status_code == 200
        
        job = response.json()
        job_id = job["id"]
        assert job["status"] == "pending"
        
        # Step 2: Monitor job progress
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            response = requests.get(f"{api_base_url}/scraping/jobs/{job_id}")
            assert response.status_code == 200
            
            job_status = response.json()
            status = job_status["status"]
            
            if status in ["completed", "failed"]:
                break
            
            time.sleep(5)  # Wait 5 seconds between checks
        
        # Step 3: Verify job completion
        assert status == "completed", f"Job failed or timed out. Status: {status}"
        assert job_status.get("total_items", 0) > 0, "No items were processed"
        assert job_status.get("success_items", 0) > 0, "No items were successful"
        
        # Step 4: Verify products were created
        response = requests.post(f"{api_base_url}/products/search", json={
            "query": "",
            "page": 1,
            "page_size": 10
        })
        assert response.status_code == 200
        
        products = response.json()
        assert products["total"] > 0, "No products found after scraping"
    
    def test_product_search_and_details(self, api_base_url):
        """Test product search and details retrieval"""
        assert self.wait_for_api_ready(api_base_url), "API is not ready"
        
        # Step 1: Search for products
        search_data = {
            "query": "เครื่อง",  # Thai word meaning "machine"
            "page": 1,
            "page_size": 5
        }
        
        response = requests.post(f"{api_base_url}/products/search", json=search_data)
        assert response.status_code == 200
        
        search_results = response.json()
        
        if search_results["total"] > 0:
            # Step 2: Get details for first product
            first_product = search_results["products"][0]
            product_id = first_product["id"]
            
            response = requests.get(f"{api_base_url}/products/{product_id}")
            assert response.status_code == 200
            
            product_details = response.json()
            assert product_details["id"] == product_id
            assert "sku" in product_details
            assert "name" in product_details
            
            # Step 3: Get price history
            response = requests.get(f"{api_base_url}/products/{product_id}/price-history")
            assert response.status_code == 200
            
            price_history = response.json()
            assert "history" in price_history
            assert price_history["product_id"] == product_id
    
    @pytest.mark.external
    def test_url_discovery_workflow(self, api_base_url):
        """Test URL discovery workflow"""
        assert self.wait_for_api_ready(api_base_url), "API is not ready"
        
        # Test URL discovery for a category
        discovery_data = {
            "url": "https://www.homepro.co.th/c/electrical",
            "max_pages": 1
        }
        
        response = requests.post(f"{api_base_url}/scraping/discover", json=discovery_data)
        assert response.status_code == 200
        
        discovery_results = response.json()
        assert "discovered_urls" in discovery_results
        assert "total" in discovery_results
        assert isinstance(discovery_results["discovered_urls"], list)
        
        # URLs should follow HomePro pattern
        for url in discovery_results["discovered_urls"][:5]:  # Check first 5
            assert "homepro.co.th" in url
            assert "/p/" in url  # Product URL pattern
    
    def test_analytics_workflow(self, api_base_url):
        """Test analytics data retrieval"""
        assert self.wait_for_api_ready(api_base_url), "API is not ready"
        
        # Get dashboard analytics
        response = requests.get(f"{api_base_url}/analytics/dashboard")
        assert response.status_code == 200
        
        analytics = response.json()
        assert "product_stats" in analytics
        assert "daily_stats" in analytics
        assert "brand_distribution" in analytics
        assert "category_distribution" in analytics
        
        # Verify structure of analytics data
        product_stats = analytics["product_stats"]
        assert isinstance(product_stats, dict)
        
        # Get filter options
        response = requests.get(f"{api_base_url}/products/filters/brands")
        assert response.status_code == 200
        brands = response.json()
        assert "brands" in brands
        
        response = requests.get(f"{api_base_url}/products/filters/categories")
        assert response.status_code == 200
        categories = response.json()
        assert "categories" in categories


@pytest.mark.e2e
@pytest.mark.slow
class TestFrontendWorkflowE2E:
    """End-to-end tests for frontend user workflows"""
    
    def test_dashboard_loads(self, webdriver, frontend_url):
        """Test that dashboard loads correctly"""
        if not self.wait_for_frontend_ready(frontend_url):
            pytest.skip("Frontend is not ready")
        
        webdriver.get(frontend_url)
        
        # Wait for page to load
        wait = WebDriverWait(webdriver, 10)
        
        # Should redirect to dashboard
        assert "/dashboard" in webdriver.current_url or webdriver.current_url == frontend_url + "/"
        
        # Check for main dashboard elements
        try:
            # Look for dashboard title or main content
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            
            # Check for navigation elements
            nav_elements = webdriver.find_elements(By.CSS_SELECTOR, "nav a, .MuiTab-root")
            assert len(nav_elements) > 0, "No navigation elements found"
            
        except TimeoutException:
            # Take screenshot for debugging
            webdriver.save_screenshot("dashboard_load_failure.png")
            pytest.fail("Dashboard did not load properly")
    
    def test_navigation_between_pages(self, webdriver, frontend_url):
        """Test navigation between different pages"""
        if not self.wait_for_frontend_ready(frontend_url):
            pytest.skip("Frontend is not ready")
        
        webdriver.get(frontend_url)
        wait = WebDriverWait(webdriver, 10)
        
        # Test navigation to different pages
        pages_to_test = [
            ("Products", "/products"),
            ("Scraping", "/scraping"),
            ("Analytics", "/analytics"),
            ("Dashboard", "/dashboard")
        ]
        
        for page_name, expected_path in pages_to_test:
            try:
                # Find navigation link by text or data attribute
                nav_link = wait.until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, page_name))
                )
                nav_link.click()
                
                # Wait for navigation to complete
                wait.until(lambda driver: expected_path in driver.current_url)
                
                # Verify page content loads
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
                
            except TimeoutException:
                webdriver.save_screenshot(f"navigation_{page_name.lower()}_failure.png")
                pytest.fail(f"Navigation to {page_name} failed")
    
    def test_scraping_job_creation_workflow(self, webdriver, frontend_url):
        """Test creating a scraping job through the UI"""
        if not self.wait_for_frontend_ready(frontend_url):
            pytest.skip("Frontend is not ready")
        
        webdriver.get(f"{frontend_url}/scraping")
        wait = WebDriverWait(webdriver, 10)
        
        try:
            # Look for "New Scraping Job" button
            new_job_button = wait.until(
                EC.element_to_be_clickable((By.TEXT, "New Scraping Job"))
            )
            new_job_button.click()
            
            # Wait for dialog to open
            dialog = wait.until(EC.presence_of_element_located((By.ROLE, "dialog")))
            
            # Fill in job details
            job_type_select = dialog.find_element(By.CSS_SELECTOR, "select, .MuiSelect-root")
            # Select category scraping
            
            url_input = dialog.find_element(By.CSS_SELECTOR, "input[placeholder*='URL'], input[label*='URL']")
            url_input.send_keys("https://www.homepro.co.th/c/tools")
            
            max_pages_input = dialog.find_element(By.CSS_SELECTOR, "input[type='number']")
            max_pages_input.clear()
            max_pages_input.send_keys("2")
            
            # Submit the form
            create_button = dialog.find_element(By.TEXT, "Create Job")
            create_button.click()
            
            # Wait for dialog to close and job to appear in list
            wait.until(EC.invisibility_of_element(dialog))
            
            # Check that job appears in the jobs table
            jobs_table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".MuiDataGrid-root, table")))
            
            # Look for the created job
            job_rows = jobs_table.find_elements(By.CSS_SELECTOR, "tr, .MuiDataGrid-row")
            assert len(job_rows) > 1, "No jobs found in table"  # Header + at least one job
            
        except TimeoutException:
            webdriver.save_screenshot("scraping_job_creation_failure.png")
            pytest.fail("Scraping job creation workflow failed")
    
    def test_product_search_workflow(self, webdriver, frontend_url):
        """Test product search functionality in the UI"""
        if not self.wait_for_frontend_ready(frontend_url):
            pytest.skip("Frontend is not ready")
        
        webdriver.get(f"{frontend_url}/products")
        wait = WebDriverWait(webdriver, 10)
        
        try:
            # Wait for page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            
            # Look for search input
            search_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='search'], input[type='search']"))
            )
            
            # Perform search
            search_input.send_keys("เครื่อง")  # Thai search term
            
            # Look for search button or trigger search
            search_button = webdriver.find_elements(By.CSS_SELECTOR, "button[type='submit'], .search-button")
            if search_button:
                search_button[0].click()
            else:
                # If no button, search might be triggered automatically
                search_input.send_keys("\n")
            
            # Wait for results or no results message
            wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".MuiDataGrid-root, .product-list")),
                    EC.presence_of_element_located((By.TEXT, "No products"))
                )
            )
            
        except TimeoutException:
            webdriver.save_screenshot("product_search_failure.png")
            pytest.fail("Product search workflow failed")
    
    def test_analytics_dashboard_workflow(self, webdriver, frontend_url):
        """Test analytics dashboard functionality"""
        if not self.wait_for_frontend_ready(frontend_url):
            pytest.skip("Frontend is not ready")
        
        webdriver.get(f"{frontend_url}/analytics")
        wait = WebDriverWait(webdriver, 10)
        
        try:
            # Wait for analytics page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            
            # Look for charts or analytics components
            analytics_elements = wait.until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "canvas, .recharts-wrapper, .chart")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".MuiCard-root, .stats-card"))
                )
            )
            
            # Verify analytics content is displayed
            assert analytics_elements is not None, "No analytics content found"
            
            # Check for key metrics or stats
            stats_elements = webdriver.find_elements(By.CSS_SELECTOR, ".MuiCard-root, .stat-item, .metric")
            assert len(stats_elements) > 0, "No statistics displayed"
            
        except TimeoutException:
            webdriver.save_screenshot("analytics_dashboard_failure.png")
            pytest.fail("Analytics dashboard workflow failed")


@pytest.mark.e2e
@pytest.mark.external
class TestExternalIntegrationE2E:
    """End-to-end tests that interact with external services"""
    
    @pytest.mark.slow
    def test_real_firecrawl_integration(self, api_base_url):
        """Test integration with real Firecrawl API (requires valid API key)"""
        # This test requires actual Firecrawl API key and should be run sparingly
        pytest.skip("Skipping real external API test - run manually when needed")
        
        # Uncomment and modify when running real integration tests
        # assert self.wait_for_api_ready(api_base_url), "API is not ready"
        
        # discovery_data = {
        #     "url": "https://www.homepro.co.th/c/electrical",
        #     "max_pages": 1
        # }
        
        # response = requests.post(f"{api_base_url}/scraping/discover", json=discovery_data)
        # assert response.status_code == 200
        
        # results = response.json()
        # assert len(results["discovered_urls"]) > 0, "No URLs discovered from real site"
    
    def test_error_handling_with_invalid_urls(self, api_base_url):
        """Test error handling with invalid URLs"""
        assert self.wait_for_api_ready(api_base_url), "API is not ready"
        
        invalid_urls = [
            "https://nonexistent-domain-12345.com",
            "https://www.homepro.co.th/invalid-path",
            "not-a-url-at-all",
            "ftp://invalid-protocol.com"
        ]
        
        for invalid_url in invalid_urls:
            discovery_data = {
                "url": invalid_url,
                "max_pages": 1
            }
            
            response = requests.post(f"{api_base_url}/scraping/discover", json=discovery_data)
            
            # Should handle gracefully (either 400 for validation or 200 with empty results)
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                results = response.json()
                # Should return empty results for invalid URLs
                assert len(results["discovered_urls"]) == 0


# Utility functions for E2E tests
class E2ETestUtils:
    """Utility functions for E2E tests"""
    
    @staticmethod
    def wait_for_element_text(webdriver, selector, expected_text, timeout=10):
        """Wait for element to contain specific text"""
        wait = WebDriverWait(webdriver, timeout)
        return wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, selector), expected_text)
        )
    
    @staticmethod
    def wait_for_job_completion(api_base_url, job_id, timeout=300):
        """Wait for scraping job to complete"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = requests.get(f"{api_base_url}/scraping/jobs/{job_id}")
            if response.status_code == 200:
                job = response.json()
                if job["status"] in ["completed", "failed"]:
                    return job
            time.sleep(5)
        return None
    
    @staticmethod
    def create_test_job(api_base_url, job_type="category", max_pages=1):
        """Create a test scraping job"""
        job_data = {
            "job_type": job_type,
            "target_url": "https://www.homepro.co.th/c/tools",
            "max_pages": max_pages
        }
        
        response = requests.post(f"{api_base_url}/scraping/jobs", json=job_data)
        if response.status_code == 200:
            return response.json()
        return None