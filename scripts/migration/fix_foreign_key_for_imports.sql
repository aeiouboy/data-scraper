-- Temporarily disable foreign key constraint for imported data
-- This allows importing virtual product matches from JSON without actual product records

-- Make master_product_id nullable for imported data
ALTER TABLE product_matches 
ALTER COLUMN master_product_id DROP NOT NULL;

-- Add a comment explaining the virtual IDs
COMMENT ON COLUMN product_matches.master_product_id IS 'Product ID. Can be NULL or virtual UUID for imported JSON data without actual product records';

-- Optional: Add a check to ensure either we have real product links OR it's imported JSON
-- ALTER TABLE product_matches ADD CONSTRAINT check_imported_or_real 
-- CHECK (
--     (master_product_id IS NOT NULL AND match_criteria->>'source' != 'imported_json')
--     OR 
--     (match_criteria->>'source' = 'imported_json')
-- );