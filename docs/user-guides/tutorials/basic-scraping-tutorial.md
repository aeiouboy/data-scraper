# Basic Scraping Tutorial

This tutorial will walk you through your first scraping job using the RIS Data Scrap system.

## Prerequisites

- System is set up and running (see [Getting Started Guide](../getting-started.md))
- Dashboard accessible at http://localhost:3000
- API running at http://localhost:8001

## Step 1: Access the Dashboard

1. Open your web browser
2. Navigate to http://localhost:3000
3. You should see the RIS Data Scrap dashboard

## Step 2: Navigate to Scraping

1. In the main navigation, click on "Scraping"
2. You'll see the scraping management interface

## Step 3: Configure Your First Scraping Job

### Choose a Retailer
- Select "HomePro (HP)" from the retailer dropdown
- HomePro is recommended for beginners due to its reliability

### Select a Category
- Choose "Power Tools" or "Electrical" for manageable data volume
- These categories typically have good data structure

### Set Limits
- **Max Pages**: Start with 2-3 pages
- **Max Products**: Set to 50 for your first attempt
- **Delay**: Use default (2-3 seconds between requests)

## Step 4: Start the Scraping Job

1. Click "Start Scraping"
2. You'll see a progress indicator appear
3. Monitor the real-time progress updates

## Step 5: Monitor Progress

Watch for these status updates:
- "Initializing..." - Job setup in progress
- "Scraping page 1 of 3" - Active scraping
- "Processing products..." - Data processing
- "Completed" - Job finished successfully

## Step 6: Review Results

Once completed:
1. Navigate to "Products" in the main menu
2. Filter by the retailer you just scraped
3. Examine the scraped product data:
   - Product names and descriptions
   - Prices and availability
   - Categories and specifications
   - Images (if available)

## Step 7: Explore Price Comparisons

1. Go to "Price Comparisons"
2. Look for products that appear across multiple retailers
3. Notice the savings calculations and price differences

## Common Issues and Solutions

### "No products found"
- **Check category URL**: Ensure the category exists
- **Verify internet connection**: Confirm you can access retailer website
- **Review retailer status**: Some sites may be temporarily down

### "Scraping job failed"
- **Check API logs**: Look for error messages in the console
- **Verify Firecrawl key**: Ensure your API key is valid
- **Reduce limits**: Try fewer pages or products

### "Products look incomplete"
- **Normal variation**: Some products may have missing data
- **Retailer inconsistency**: Data quality varies by retailer
- **Site structure changes**: Retailers may update their websites

## Best Practices for Beginners

### Start Small
- Begin with 1-2 pages
- Use 20-50 product limits
- Test with reliable retailers (HomePro, Global House)

### Monitor Resource Usage
- Watch CPU and memory usage during scraping
- Don't run multiple large jobs simultaneously
- Use appropriate delays between requests

### Data Validation
- Spot-check scraped data against retailer website
- Look for reasonable prices and descriptions
- Report obvious data quality issues

## Next Steps

### Advanced Scraping
- Try different retailers and categories
- Experiment with larger data volumes
- Set up scheduled scraping jobs

### Data Analysis
- Export scraped data for analysis
- Set up price monitoring workflows
- Create custom product matching rules

### Integration
- Learn the API endpoints
- Set up automated data processing
- Build custom reporting dashboards

## Troubleshooting

If you encounter issues:

1. **Check the logs**: Look at the scraping job details
2. **Verify settings**: Confirm your configuration is correct
3. **Test connectivity**: Ensure you can access retailer websites
4. **Consult documentation**: Review the [FAQ](../faq.md) and [Troubleshooting Guide](../../development/troubleshooting.md)
5. **Report bugs**: Use the [Bug Report Template](../../templates/bug-report.md)

## Tutorial Complete!

You've successfully completed your first scraping job. You now know how to:
- ✅ Configure and start scraping jobs
- ✅ Monitor progress and handle issues
- ✅ Review and validate scraped data
- ✅ Access price comparison features

Ready to explore more advanced features? Check out the [Native Scraping User Manual](../native-scraping-user-manual.md) for advanced techniques.