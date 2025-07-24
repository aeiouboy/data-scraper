import React from 'react';
import {
  Box,
  Button,
  Typography,
  Alert,
  AlertTitle,
} from '@mui/material';
import {
  RocketLaunch as RocketIcon,
  Inventory as InventoryIcon,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { scrapingApi } from '../services/api';

export default function QuickLaunch50K() {
  // Launch 50K complete catalog scraping
  const launch50K = useMutation({
    mutationFn: async () => {
      // Generate ALL possible HomePro categories for complete catalog
      const mainCategories = ['APP', 'TOO', 'ELT', 'CON', 'FUR', 'BAT', 'KIT', 'LIG', 'PAI', 'PLU', 
                             'HHP', 'TVA', 'FLO', 'DOW', 'OUT', 'SMA', 'SPO', 'BEA', 'MOM', 'HEA', 
                             'PET', 'ATM', 'CLE', 'GAR', 'TIL', 'WOO', 'MET', 'PLA'];
      
      const allJobs = [];
      
      // Create comprehensive job list with unlimited pagination
      for (const mainCat of mainCategories) {
        // Main category with unlimited pages
        allJobs.push({
          job_type: 'category',
          target_url: `https://www.homepro.co.th/c/${mainCat}`,
          retailer_code: 'HP',
          max_pages: 999 // Unlimited - scrape until no more products
        });
        
        // Add 20 numbered subcategories per main category
        for (let i = 1; i <= 20; i++) {
          const subcat = `${mainCat}${i.toString().padStart(2, '0')}`;
          allJobs.push({
            job_type: 'category',
            target_url: `https://www.homepro.co.th/c/${subcat}`,
            retailer_code: 'HP',
            max_pages: 999
          });
        }
      }
      
      console.log(`🚀 Launching ${allJobs.length} jobs for 50K+ products`);
      
      // Launch jobs in small batches to avoid overwhelming the system
      const batchSize = 5;
      const successfulJobs = [];
      
      for (let i = 0; i < allJobs.length; i += batchSize) {
        const batch = allJobs.slice(i, i + batchSize);
        
        const batchPromises = batch.map(async (job) => {
          try {
            const response = await scrapingApi.createJob(job);
            return response.data;
          } catch (error) {
            // Category doesn't exist - expected for many combinations
            return null;
          }
        });
        
        const batchResults = await Promise.all(batchPromises);
        const validResults = batchResults.filter(result => result !== null);
        successfulJobs.push(...validResults);
        
        // Brief pause between batches for resource management
        if (i + batchSize < allJobs.length) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      return successfulJobs;
    },
  });

  return (
    <Box sx={{ p: 3 }}>
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>🎯 Complete HomePro Catalog Scraping</AlertTitle>
        <Typography variant="body2">
          Launch comprehensive scraping to get ALL available SKUs from HomePro. 
          This will create jobs for all possible categories with unlimited pagination.
        </Typography>
      </Alert>

      <Box sx={{ textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          startIcon={launch50K.isPending ? <InventoryIcon /> : <RocketIcon />}
          onClick={() => launch50K.mutate()}
          disabled={launch50K.isPending}
          color="primary"
          sx={{
            minWidth: 250,
            height: 60,
            fontSize: '1.1rem',
            background: launch50K.isPending 
              ? 'linear-gradient(45deg, #4CAF50 30%, #8BC34A 90%)'
              : 'linear-gradient(45deg, #FF6B35 30%, #F7931E 90%)',
            boxShadow: '0 3px 10px 2px rgba(255, 107, 53, .3)',
            '&:hover': {
              background: 'linear-gradient(45deg, #E65100 30%, #FF8F00 90%)',
            }
          }}
        >
          {launch50K.isPending ? 'Launching Campaign...' : '🚀 Launch 50K+ Product Scraping'}
        </Button>
        
        {launch50K.isSuccess && (
          <Alert severity="success" sx={{ mt: 2 }}>
            <AlertTitle>Campaign Launched Successfully!</AlertTitle>
            Created {launch50K.data?.length || 0} scraping jobs. Monitor progress in the Jobs tabs above.
          </Alert>
        )}
        
        {launch50K.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            <AlertTitle>Launch Failed</AlertTitle>
{(launch50K.error as any)?.message || 'Failed to launch campaign'}
          </Alert>
        )}
      </Box>
      
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
        Expected: 50,000+ products • Time: 15-30 hours • Categories: 500+
      </Typography>
    </Box>
  );
}