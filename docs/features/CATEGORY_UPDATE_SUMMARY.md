# Category Update Summary

## Updates Made to retailers.py

### Global House
- **Previous**: 10 categories
- **Updated**: 47 categories
- **Details**: Added all product categories, filtered out non-category URLs like:
  - /about/, /account/, /brand/, /articles/, /careers/
  - /promotions/, /service-, /store-finder, /investor
  - /directlink, /global-service, /globalidea, etc.

### DoHome
- **Previous**: 8 categories
- **Updated**: 54 categories
- **Details**: Added all unique product categories, removing duplicates between:
  - Base URLs (e.g., /adhesives)
  - Category URLs (e.g., /category/adhesives)

### MegaHome
- **Previous**: 8 categories
- **Updated**: 64 categories (52 descriptive + 12 category codes)
- **Details**: Included both URL patterns:
  - Descriptive URLs (e.g., /adhesives-sealants, /automotive-supplies)
  - Category code URLs (e.g., /c/BAT, /c/CON, /c/ELT)

## Summary Statistics

| Retailer | Previous Categories | Updated Categories | Increase |
|----------|-------------------|-------------------|----------|
| HomePro | 42 | 42 | No change |
| Thai Watsadu | 151 | 151 | No change |
| Global House | 10 | 47 | +370% |
| DoHome | 8 | 54 | +575% |
| Boonthavorn | 23 | 23 | No change |
| MegaHome | 8 | 64 | +700% |

## Total Category Coverage
- **Previous Total**: 242 categories
- **Updated Total**: 381 categories
- **Overall Increase**: 57% more categories

This comprehensive update ensures all discovered product categories are included for complete scraping coverage across all retailers.