# Database Organization

This directory contains all database-related files for the RIS Data Scrap project, organized into a professional schema management structure.

## Directory Structure

```
database/
├── README.md                          # This documentation
├── schema/                            # Core schema definitions
│   ├── core/                         # Main application schema
│   ├── extensions/                   # Optional schema extensions
│   └── archive/                      # Historical schema versions
├── migrations/                        # Database migrations (chronological)
│   ├── 001_initial_schema/           # Initial database setup
│   ├── 002_multi_retailer/           # Multi-retailer support
│   ├── 003_adaptive_scraping/        # Adaptive scraping features
│   ├── 004_scrape_jobs/              # Scrape jobs enhancements
│   ├── 005_monitoring/               # Monitoring schedules
│   ├── 006_brand_aliases/            # Brand aliases system
│   ├── 007_match_groups/             # Product match groups
│   └── 008_performance_optimizations/ # Performance improvements
├── indexes/                          # Index definitions
│   ├── performance/                  # Performance indexes
│   ├── constraints/                  # Constraint definitions
│   └── full_text/                    # Full-text search indexes
├── data/                             # Reference/seed data
│   ├── retailers/                    # Retailer reference data
│   ├── categories/                   # Category reference data
│   └── configuration/                # Configuration data
├── maintenance/                      # Database maintenance
│   ├── cleanup/                      # Cleanup scripts
│   ├── optimization/                 # Optimization scripts
│   └── monitoring/                   # Monitoring queries
└── documentation/                    # Database documentation
    ├── entity-relationship.md        # ER diagrams and relationships
    ├── data-dictionary.md            # Data dictionary
    └── migration-guide.md            # Migration procedures
```

## Migration Management

### Running Migrations

Migrations are numbered sequentially and should be run in order:

1. **001_initial_schema** - Creates core database structure
2. **002_multi_retailer** - Adds multi-retailer support
3. **003_adaptive_scraping** - Implements adaptive scraping features
4. **004_scrape_jobs** - Enhances scrape jobs tracking
5. **005_monitoring** - Adds monitoring schedules
6. **006_brand_aliases** - Implements brand aliases system
7. **007_match_groups** - Creates product match groups
8. **008_performance_optimizations** - Applies performance improvements

### Migration Dependencies

- Migrations 002-008 depend on 001_initial_schema
- Migration 008 may depend on previous data being present
- Always backup before running migrations

## Index Management

Performance indexes are organized by purpose:

- **performance/general_indexes.sql** - Core performance indexes
- **performance/price_comparisons_optimization.sql** - Price comparison optimizations

## Database Technology

- **Platform**: Supabase (PostgreSQL)
- **Extensions**: UUID, full-text search
- **Connection**: Direct Supabase client (no ORM)

## Key Tables

### Core Tables
- `categories` - Product categories hierarchy
- `products` - Product information
- `retailers` - Retailer information
- `scrape_jobs` - Scraping job tracking

### Matching Tables
- `product_matches` - Product matches across retailers
- `match_groups` - Grouped product matches
- `brand_aliases` - Brand name aliases

### Monitoring Tables
- `monitoring_schedules` - Automated monitoring schedules
- `price_history` - Historical price tracking

## Usage Guidelines

### For Developers
- Always use migrations for schema changes
- Test migrations on development environment first
- Document all schema changes in migration files

### For Database Administrators
- Regular index maintenance recommended
- Monitor query performance with included monitoring scripts
- Use cleanup scripts for data maintenance

### For Application Code
- Reference tables through Supabase client
- Use proper error handling for database operations
- Follow connection pooling best practices

## Security Notes

- Service role key required for schema changes
- Anon key sufficient for regular operations
- Row Level Security (RLS) policies may apply
- Backup sensitive operations

## Support

For database-related issues:
1. Check migration logs
2. Verify Supabase connection
3. Review query performance
4. Consult documentation files

---
*Database organization follows RIS Data Scrap project file organization standards*