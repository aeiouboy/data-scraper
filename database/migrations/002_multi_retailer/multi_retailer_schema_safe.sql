-- Safe version of schema update for constraint handling
-- This version uses DO blocks for better error handling

-- ====================================================================
-- SAFELY DROP AND RECREATE SKU CONSTRAINT
-- ====================================================================

DO $$
BEGIN
    -- Check if constraint exists and drop it
    IF EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'products_sku_key' 
        AND table_name = 'products'
    ) THEN
        ALTER TABLE products DROP CONSTRAINT products_sku_key;
        RAISE NOTICE 'Dropped existing products_sku_key constraint';
    END IF;
    
    -- Check if the new constraint already exists
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'products_retailer_sku_unique' 
        AND table_name = 'products'
    ) THEN
        ALTER TABLE products 
        ADD CONSTRAINT products_retailer_sku_unique UNIQUE (retailer_code, sku);
        RAISE NOTICE 'Added new products_retailer_sku_unique constraint';
    ELSE
        RAISE NOTICE 'Constraint products_retailer_sku_unique already exists';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error handling constraint: %', SQLERRM;
END;
$$;