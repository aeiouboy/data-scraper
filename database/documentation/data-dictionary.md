# Database Data Dictionary

This document provides comprehensive information about all tables, columns, and relationships in the RIS Data Scrap database.

## Core Tables

### categories
Product categories hierarchy table.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | uuid_generate_v4() | Primary key |
| name | TEXT | No | - | Category name (Thai) |
| name_en | TEXT | Yes | - | Category name (English) |
| parent_id | UUID | Yes | - | Parent category reference |
| path | TEXT | Yes | - | Category path for hierarchy |
| level | INT | Yes | 0 | Category level in hierarchy |
| is_active | BOOLEAN | Yes | true | Whether category is active |
| created_at | TIMESTAMPTZ | Yes | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | Yes | NOW() | Last update timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (parent_id) REFERENCES categories(id)

**Business Rules:**
- Categories form a hierarchical structure
- Path represents full category hierarchy
- Level indicates depth in hierarchy (0 = root)

### products
Main product information table.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | uuid_generate_v4() | Primary key |
| name | TEXT | No | - | Product name |
| description | TEXT | Yes | - | Product description |
| brand | TEXT | Yes | - | Product brand |
| model | TEXT | Yes | - | Product model |
| sku | TEXT | Yes | - | Stock Keeping Unit |
| price | DECIMAL(10,2) | Yes | - | Current price |
| original_price | DECIMAL(10,2) | Yes | - | Original/list price |
| currency | TEXT | Yes | 'THB' | Price currency |
| availability | TEXT | Yes | - | Stock availability |
| category_id | UUID | Yes | - | Category reference |
| retailer_id | UUID | Yes | - | Retailer reference |
| retailer_product_id | TEXT | Yes | - | Retailer's product ID |
| url | TEXT | Yes | - | Product URL |
| image_url | TEXT | Yes | - | Product image URL |
| specifications | JSONB | Yes | - | Product specifications |
| created_at | TIMESTAMPTZ | Yes | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | Yes | NOW() | Last update timestamp |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (category_id) REFERENCES categories(id)
- FOREIGN KEY (retailer_id) REFERENCES retailers(id)
- INDEX on (sku)
- INDEX on (brand)
- INDEX on (retailer_id, retailer_product_id)

### retailers
Retailer information table.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | uuid_generate_v4() | Primary key |
| code | TEXT | No | - | Retailer code (HP, TWD, etc.) |
| name | TEXT | No | - | Retailer name |
| name_en | TEXT | Yes | - | Retailer name (English) |
| website | TEXT | Yes | - | Retailer website URL |
| description | TEXT | Yes | - | Retailer description |
| is_active | BOOLEAN | Yes | true | Whether retailer is active |
| created_at | TIMESTAMPTZ | Yes | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | Yes | NOW() | Last update timestamp |

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE (code)

**Business Rules:**
- Retailer codes must be unique
- Common codes: HP (HomePro), TWD (Thai Watsadu), GH (Global House)

## Scraping Tables

### scrape_jobs
Scraping job tracking and monitoring.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | uuid_generate_v4() | Primary key |
| retailer_code | VARCHAR(5) | Yes | - | Retailer code for the job |
| job_type | TEXT | No | - | Type of scraping job |
| status | TEXT | No | 'pending' | Job status |
| category | TEXT | Yes | - | Category being scraped |
| total_items | INT | Yes | - | Total items to process |
| processed_items | INT | Yes | 0 | Items processed so far |
| successful_items | INT | Yes | 0 | Successfully processed items |
| failed_items | INT | Yes | 0 | Failed processing items |
| started_at | TIMESTAMPTZ | Yes | - | Job start time |
| completed_at | TIMESTAMPTZ | Yes | - | Job completion time |
| duration_seconds | INT | Yes | - | Job duration in seconds |
| error_message | TEXT | Yes | - | Error message if failed |
| created_at | TIMESTAMPTZ | Yes | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | Yes | NOW() | Last update timestamp |

**Indexes:**
- PRIMARY KEY (id)
- INDEX on (retailer_code)
- INDEX on (retailer_code, created_at DESC)
- INDEX on (status)

**Constraints:**
- CHECK (duration_seconds IS NULL OR duration_seconds >= 0)

**Business Rules:**
- Job statuses: pending, running, completed, failed, cancelled
- Duration calculated from started_at and completed_at

### monitoring_schedules
Automated monitoring schedules.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | uuid_generate_v4() | Primary key |
| name | TEXT | No | - | Schedule name |
| retailer_code | TEXT | No | - | Target retailer |
| category | TEXT | Yes | - | Target category |
| frequency | TEXT | No | - | Schedule frequency |
| is_active | BOOLEAN | Yes | true | Whether schedule is active |
| last_run | TIMESTAMPTZ | Yes | - | Last execution time |
| next_run | TIMESTAMPTZ | Yes | - | Next scheduled execution |
| created_at | TIMESTAMPTZ | Yes | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | Yes | NOW() | Last update timestamp |

**Business Rules:**
- Frequency options: hourly, daily, weekly, monthly
- Next_run calculated based on frequency and last_run

## Product Matching Tables

### product_matches
Product matches across different retailers.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | uuid_generate_v4() | Primary key |
| match_group_id | UUID | Yes | - | Match group reference |
| products | JSONB | No | - | Array of matched products |
| match_confidence | DECIMAL(3,2) | Yes | - | Confidence score (0.00-1.00) |
| unified_name | TEXT | Yes | - | Unified product name |
| unified_brand | TEXT | Yes | - | Unified brand name |
| unified_category | TEXT | Yes | - | Unified category |
| price_range_min | DECIMAL(10,2) | Yes | - | Minimum price in match |
| price_range_max | DECIMAL(10,2) | Yes | - | Maximum price in match |
| price_variance_percentage | DECIMAL(5,2) | Yes | - | Price variance percentage |
| retailer_count | INT | Yes | - | Number of retailers |
| created_at | TIMESTAMPTZ | Yes | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | Yes | NOW() | Last update timestamp |

**Indexes:**
- PRIMARY KEY (id)
- INDEX on (unified_category)
- INDEX on (price_range_max)
- INDEX on (price_variance_percentage)
- INDEX on (match_confidence)
- FOREIGN KEY (match_group_id) REFERENCES match_groups(id)

### match_groups
Logical groupings of product matches.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | uuid_generate_v4() | Primary key |
| name | TEXT | No | - | Group name |
| description | TEXT | Yes | - | Group description |
| category | TEXT | Yes | - | Product category |
| brand | TEXT | Yes | - | Product brand |
| is_active | BOOLEAN | Yes | true | Whether group is active |
| created_at | TIMESTAMPTZ | Yes | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | Yes | NOW() | Last update timestamp |

### brand_aliases
Brand name aliases for improved matching.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | uuid_generate_v4() | Primary key |
| canonical_brand | TEXT | No | - | Standard brand name |
| alias_brand | TEXT | No | - | Alternative brand name |
| confidence | DECIMAL(3,2) | Yes | 1.00 | Alias confidence score |
| is_active | BOOLEAN | Yes | true | Whether alias is active |
| created_at | TIMESTAMPTZ | Yes | NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | Yes | NOW() | Last update timestamp |

**Indexes:**
- PRIMARY KEY (id)
- INDEX on (canonical_brand)
- INDEX on (alias_brand)
- UNIQUE (canonical_brand, alias_brand)

## Historical Tables

### price_history
Historical price tracking.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | uuid_generate_v4() | Primary key |
| product_id | UUID | No | - | Product reference |
| price | DECIMAL(10,2) | No | - | Historical price |
| original_price | DECIMAL(10,2) | Yes | - | Historical original price |
| currency | TEXT | No | 'THB' | Price currency |
| recorded_at | TIMESTAMPTZ | No | NOW() | Price recording time |
| source | TEXT | Yes | - | Price source/method |

**Indexes:**
- PRIMARY KEY (id)
- FOREIGN KEY (product_id) REFERENCES products(id)
- INDEX on (product_id, recorded_at DESC)

## Relationships

### Primary Relationships

1. **categories** ↔ **categories** (self-referential)
   - parent_id → id (hierarchical structure)

2. **products** → **categories**
   - category_id → categories.id

3. **products** → **retailers**
   - retailer_id → retailers.id

4. **product_matches** → **match_groups**
   - match_group_id → match_groups.id

5. **price_history** → **products**
   - product_id → products.id

### JSONB Column Structures

#### products.specifications
```json
{
  "weight": "5.2 kg",
  "dimensions": "30x40x50 cm",
  "power": "1800W",
  "features": ["Digital Display", "Timer", "Auto Shut-off"],
  "warranty": "2 years",
  "color": "Black"
}
```

#### product_matches.products
```json
[
  {
    "product_id": "uuid",
    "retailer_code": "HP",
    "name": "Product Name",
    "price": 1500.00,
    "url": "https://..."
  },
  {
    "product_id": "uuid", 
    "retailer_code": "TWD",
    "name": "Similar Product Name",
    "price": 1450.00,
    "url": "https://..."
  }
]
```

## Data Types Reference

| Type | PostgreSQL Type | Description |
|------|----------------|-------------|
| UUID | uuid | Universally unique identifier |
| TEXT | text | Variable length text |
| VARCHAR(n) | character varying(n) | Variable length text with limit |
| INT | integer | 32-bit integer |
| DECIMAL(p,s) | numeric(p,s) | Fixed-point decimal |
| BOOLEAN | boolean | True/false values |
| TIMESTAMPTZ | timestamp with time zone | Timestamp with timezone |
| JSONB | jsonb | Binary JSON with indexing |

## Naming Conventions

- **Tables**: snake_case, plural nouns
- **Columns**: snake_case, descriptive names
- **Indexes**: idx_table_column(s) format
- **Foreign Keys**: fk_table_column format
- **Constraints**: check_table_condition format

## Data Integrity Rules

1. **Referential Integrity**: All foreign keys must reference valid records
2. **Temporal Consistency**: created_at ≤ updated_at
3. **Price Validation**: Prices must be non-negative
4. **Status Validation**: Enum-like fields use predefined values
5. **JSON Schema**: JSONB fields follow documented schemas

---
*This data dictionary is maintained alongside schema changes and should be updated with each migration.*