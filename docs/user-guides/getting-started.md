# Getting Started Guide

Welcome to RIS Data Scrap - a comprehensive web scraping and price comparison system for Thai home improvement retailers.

## Quick Setup

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- PostgreSQL database (via Supabase)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ris-data-scrap
   ```

2. **Set up environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your credentials
   # Required: SUPABASE_URL, SUPABASE_ANON_KEY, FIRECRAWL_API_KEY
   ```

3. **Install dependencies**
   ```bash
   # Python dependencies
   pip install -r requirements.txt
   
   # Frontend dependencies
   cd frontend && npm install
   ```

4. **Run the application**
   ```bash
   # Option 1: Run both services
   make run-all
   
   # Option 2: Run separately
   make run-api      # http://localhost:8001
   make run-frontend # http://localhost:3000
   ```

## Key Features

### Web Scraping
- Automated product data collection from 6 major Thai retailers
- Real-time price monitoring and updates
- Category-based scraping with pagination support
- Rate limiting and retry mechanisms

### Price Comparison
- Cross-retailer price analysis
- Historical price tracking
- Automated deal detection
- Savings calculation and reporting

### Product Matching
- Intelligent product matching across retailers
- Multiple matching algorithms with confidence scoring
- Manual matching interface for review
- Brand and model standardization

### Data Management
- Supabase database integration
- Data quality validation
- Automated data cleanup
- Export capabilities

## Your First Scraping Job

1. **Access the dashboard**
   Open http://localhost:3000 in your browser

2. **Start a scraping job**
   - Navigate to Scraping page
   - Select a retailer (e.g., HomePro)
   - Choose a category
   - Set limits and click "Start Scraping"

3. **Monitor progress**
   - View real-time progress updates
   - Check job status and logs
   - Review scraped products

4. **Analyze results**
   - Navigate to Products page
   - Filter and search products
   - View price comparisons
   - Export data if needed

## Common Use Cases

### Price Monitoring
Set up automated monitoring for specific product categories to track price changes and identify deals.

### Market Analysis
Compare prices across retailers to understand market positioning and competitive dynamics.

### Inventory Management
Track product availability and stock levels across different retailers.

### Data Export
Export product and pricing data for external analysis or reporting.

## Next Steps

- [Native Scraping User Manual](native-scraping-user-manual.md)
- [API Documentation](../api/index.md)
- [Feature Guides](../features/index.md)
- [Troubleshooting](../development/troubleshooting.md)

## Support

For issues or questions:
1. Check the [Troubleshooting Guide](../development/troubleshooting.md)
2. Review [Known Issues](../development/troubleshooting-report.md)
3. Submit a bug report using our [Bug Report Template](../templates/bug-report.md)