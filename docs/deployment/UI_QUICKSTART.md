# HomePro Product Manager - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Start the Backend API
```bash
# In the project root directory
source venv/bin/activate
python3 run_api.py
```
API will be available at http://localhost:8000

### 2. Start the Frontend UI
```bash
# In a new terminal
cd frontend
npm install  # First time only
npm start
```
UI will open automatically at http://localhost:3000

## 📸 UI Overview

### Dashboard
The main dashboard shows:
- **Total Products**: Number of products in database
- **Average Price**: Average product price
- **Products on Sale**: Count of discounted products  
- **Total Brands**: Number of unique brands
- **Daily Activity**: Scraping performance chart
- **Top Brands**: Most common brands
- **Price Distribution**: Price range breakdown

### Products Page
Search and manage products:
- **Search Bar**: Search by name, SKU, or description
- **Filters**: 
  - Brand selection (multi-select)
  - Category selection (multi-select)
  - Price range slider (฿0 - ฿50,000)
  - On Sale Only checkbox
  - In Stock Only checkbox
- **Data Grid**: 
  - Sortable columns
  - Pagination (20/50/100 per page)
  - Rescrape button for each product
  - Direct link to HomePro product page

### Scraping Page
Manage scraping operations:
- **Job Stats**: Active, completed, and failed job counts
- **Create New Job**:
  - Category Scraping: Enter category URL (e.g., https://www.homepro.co.th/c/electrical)
  - Product Scraping: Paste multiple product URLs
  - Max Pages: Set crawl depth (1-50)
- **Job Monitoring**:
  - Real-time progress bars
  - Success rate calculation
  - Cancel running jobs
  - Auto-refresh every 5 seconds

### Settings Page
Configure the scraper:
- **Enable/Disable Scraping**: Master switch
- **Max Concurrent Jobs**: 1-10 simultaneous jobs
- **Default Max Pages**: Default crawl depth
- **Rate Limit Delay**: Seconds between requests

## 🎯 Common Tasks

### Search for Products
1. Go to **Products** page
2. Type in search box (e.g., "เครื่องกรองน้ำ")
3. Select filters if needed
4. Click **Search**

### Start a Category Scrape
1. Go to **Scraping** page
2. Click **New Scraping Job**
3. Select **Category Scraping**
4. Enter URL: `https://www.homepro.co.th/c/electrical`
5. Set **Max Pages**: 5
6. Click **Create Job**

### Check Scraping Progress
1. Go to **Scraping** page
2. Click **Running** tab
3. Watch progress bars update in real-time
4. Check success rate percentage

### Update Product Prices
1. Go to **Products** page
2. Find the product to update
3. Click the **refresh** icon in Actions column
4. Check notification for success

## 🔧 Troubleshooting

### "Failed to load data"
- Check if backend API is running (`python3 run_api.py`)
- Verify database connection in `.env` file
- Check browser console for errors

### "No products found"
- Run a scraping job first to populate database
- Check if search filters are too restrictive
- Try searching without filters

### "Job failed"
- Check Firecrawl API key in `.env`
- Verify the URL is valid
- Check rate limits (wait and retry)

## 📊 Sample URLs for Testing

### Categories
- Electrical: `https://www.homepro.co.th/c/electrical`
- Tools: `https://www.homepro.co.th/c/tools`
- Bathroom: `https://www.homepro.co.th/c/bathroom`

### Products
- `https://www.homepro.co.th/p/1083389`
- `https://www.homepro.co.th/p/1243357`
- `https://www.homepro.co.th/p/1262725`

## 💡 Tips

1. **Start Small**: Test with 1-2 pages first
2. **Monitor Jobs**: Keep Scraping page open to track progress
3. **Use Filters**: Narrow searches for better performance
4. **Export Data**: Use the Export button for reports
5. **Check Stats**: Dashboard updates every page refresh

## 🆘 Need Help?

1. Check API status: http://localhost:8000/docs
2. View API logs in terminal running `run_api.py`
3. Check browser console (F12) for frontend errors
4. Restart both backend and frontend if needed