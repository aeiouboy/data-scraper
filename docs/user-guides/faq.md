# Frequently Asked Questions

## General Questions

### What is RIS Data Scrap?
RIS Data Scrap is a comprehensive web scraping and price comparison system designed specifically for Thai home improvement retailers. It automatically collects product data from major retailers and provides price comparison and monitoring capabilities.

### Which retailers are supported?
Currently supported retailers:
- **HomePro (HP)** - Thailand's largest home improvement retailer
- **Thai Watsadu (TWD)** - Major building materials retailer  
- **Global House (GH)** - Home improvement and furniture
- **DoHome (DH)** - Home improvement superstore
- **Boonthavorn (BT)** - Building materials and hardware
- **MegaHome (MH)** - Home improvement retailer

### How often is data updated?
- **Real-time scraping**: On-demand via the dashboard
- **Scheduled monitoring**: Configurable intervals (daily, weekly)
- **Price updates**: Tracked with historical data
- **Stock status**: Updated during each scrape cycle

## Technical Questions

### What technologies are used?
- **Backend**: FastAPI (Python)
- **Frontend**: React with Material-UI
- **Database**: Supabase (PostgreSQL)
- **Scraping**: Firecrawl API + native scraping
- **Deployment**: Docker support

### How do I set up the development environment?
See the [Getting Started Guide](getting-started.md) for detailed setup instructions.

### Can I add support for new retailers?
Yes! Follow the [Scraper Development Guide](../development/frontend-integration-guide.md) to add new retailers.

## Data and Scraping

### How accurate is the scraped data?
- **Product names**: >95% accuracy with normalization
- **Prices**: >98% accuracy with validation
- **Categories**: >90% accuracy with manual validation
- **Stock status**: Real-time when available

### How does product matching work?
Our system uses multiple matching algorithms:
1. **Exact SKU matching**: Highest confidence
2. **Brand + model matching**: High confidence  
3. **Fuzzy text matching**: Medium confidence
4. **Specification matching**: Variable confidence

### What if products are mismatched?
- Use the manual matching interface in the dashboard
- Report false positives for algorithm improvement
- Review confidence scores before trusting matches

### How much data can I scrape?
- **No hard limits** on data volume
- **Rate limiting** to respect retailer servers
- **Configurable limits** per scraping job
- **Resource management** for optimal performance

## Pricing and Monitoring

### How are price comparisons calculated?
- **Lowest price**: Across all matched products
- **Savings**: Difference from highest price
- **Average price**: Mean across retailers
- **Price trends**: Historical price changes

### Can I set up price alerts?
Currently available through:
- Dashboard monitoring
- Scheduled scraping jobs
- Manual price comparison checks

*Note: Automated alerts are planned for future releases*

### What about product availability?
- Stock status tracked when available from retailer
- "Out of stock" vs "Available" indicators
- Historical availability patterns
- Cross-retailer availability comparison

## Performance and Limits

### How fast is the scraping?
- **HomePro**: ~50-100 products/minute
- **Thai Watsadu**: ~30-60 products/minute
- **Other retailers**: ~20-50 products/minute

*Speed varies by retailer complexity and rate limits*

### Are there any usage restrictions?
- Respectful scraping with delays
- No reselling of scraped data
- Compliance with retailer terms of service
- Fair use for personal/business analysis

### How do I optimize scraping performance?
1. **Batch processing**: Use reasonable page limits
2. **Category focus**: Target specific categories
3. **Off-peak timing**: Schedule during low-traffic hours
4. **Resource monitoring**: Check system resources

## Troubleshooting

### Common Issues

**"Scraping job failed"**
- Check internet connection
- Verify Firecrawl API key
- Review retailer website status
- Check rate limit settings

**"No products found"**
- Verify category URL is correct
- Check if retailer website structure changed
- Review scraping logs for errors

**"Price matching seems wrong"**
- Check product specifications
- Review confidence scores
- Use manual matching interface
- Report issues for investigation

### Getting Help

1. **Check logs**: Review scraping job logs for errors
2. **Troubleshooting guide**: See [Troubleshooting](../development/troubleshooting.md)
3. **Bug reports**: Use [Bug Report Template](../templates/bug-report.md)
4. **Feature requests**: Use [Feature Spec Template](../templates/feature-spec.md)

## Best Practices

### Scraping Guidelines
- Start with small batches to test
- Monitor scraping job progress
- Respect retailer rate limits
- Regularly validate data quality

### Data Management
- Regular data cleanup and validation
- Export important data for backup
- Monitor database storage usage
- Review and remove obsolete data

### Performance Tips
- Use specific category targeting
- Limit concurrent scraping jobs
- Monitor system resource usage
- Schedule heavy operations during off-peak hours

## Roadmap

### Planned Features
- Automated price alerts and notifications
- Advanced analytics and reporting
- Mobile app for monitoring
- Additional retailer support
- Machine learning for better matching

### Contributing
Interested in contributing? Check our development guides and submit feature requests using the appropriate templates.