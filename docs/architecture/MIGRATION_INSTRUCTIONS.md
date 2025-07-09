# Brand Aliases Migration Instructions

To complete the price matching functionality setup, you need to execute the brand aliases migration SQL script in your Supabase database.

## Steps to Execute:

1. **Open Supabase Dashboard**
   - Go to your Supabase project dashboard
   - Navigate to the SQL Editor

2. **Execute the Migration Script**
   - Copy the entire contents of `scripts/add_brand_aliases_table.sql`
   - Paste it into the SQL Editor
   - Click "Run" to execute
   
   **Note**: The script has been updated to fix duplicate alias entries that were causing conflicts.

3. **What This Migration Does:**
   - Creates `brand_aliases` table for mapping Thai/English brand names
   - Creates `product_models` table for tracking specific product models
   - Creates `match_history` table for learning from manual match corrections
   - Adds indexes for performance optimization
   - Inserts common brand mappings (Samsung/ซัมซุง, LG/แอลจี, etc.)
   - Creates a `get_canonical_brand` function for brand normalization
   - Creates a `brand_distribution` view for analytics

## Testing the New API Endpoints

Once the migration is complete, you can test the new price matching endpoints:

### 1. Test Product Matching
```bash
curl -X POST "http://localhost:8000/api/matching/test-match" \
  -H "Content-Type: application/json" \
  -d '{
    "product1_name": "MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU",
    "product2_name": "มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู",
    "brand1": "MITSUBISHI",
    "brand2": "มิตซูบิชิ"
  }'
```

### 2. Process New Products for Matching
```bash
curl -X POST "http://localhost:8000/api/matching/process-new-products?limit=50"
```

### 3. Get Match Suggestions for a Product
```bash
curl "http://localhost:8000/api/matching/match-suggestions/{product_id}?min_confidence=0.7"
```

### 4. Get Matching Analytics
```bash
curl "http://localhost:8000/api/matching/analytics"
```

## Features Now Available:

1. **Advanced Text Normalization**
   - Thai/English brand name mapping
   - Unit conversion (นิ้ว → inch, ลิตร → L)
   - Stop word removal
   - Model/SKU extraction

2. **Smart Product Matching**
   - SKU-based matching (highest confidence)
   - Fuzzy name matching with similarity scoring
   - Specification matching (BTU, size, volume, etc.)
   - Brand alias resolution

3. **Match Management**
   - Manual match confirmation/rejection
   - Match history tracking for continuous improvement
   - Confidence scoring for automated matching

4. **Analytics**
   - Cross-retailer price comparison
   - Retailer competitiveness analysis
   - Savings opportunity identification

## Next Steps:

After running the migration, the price matching system will be fully operational. You can:
- Start processing products to find cross-retailer matches
- Build a dashboard to visualize price comparisons
- Set up automated alerts for significant price differences
- Train the matching algorithm with manual confirmations