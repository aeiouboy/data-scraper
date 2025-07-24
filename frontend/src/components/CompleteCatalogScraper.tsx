import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  LinearProgress,
  Grid,
  Chip,
  Alert,
  AlertTitle,
} from '@mui/material';
import {
  Inventory as InventoryIcon,
  RocketLaunch as RocketIcon,
  Timeline as TimelineIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { scrapingApi, productApi } from '../services/api';
import QuickLaunch50K from './QuickLaunch50K';

interface CompleteCatalogStats {
  current_products: number;
  estimated_total: number;
  coverage_percentage: number;
  missing_categories: string[];
}

export default function CompleteCatalogScraper() {
  const [isLaunching, setIsLaunching] = useState(false);
  const [campaignStatus, setCampaignStatus] = useState<'idle' | 'running' | 'completed'>('idle');

  // Get current product count
  const { data: currentStats } = useQuery({
    queryKey: ['complete-catalog-stats'],
    queryFn: async () => {
      const response = await productApi.search({ retailer_code: 'HP', page: 1, page_size: 1 });
      return {
        current_products: response.data.total,
        estimated_total: 50000, // Based on our analysis
        coverage_percentage: (response.data.total / 50000) * 100,
        missing_categories: ['Many subcategories', 'Brand sections', 'Seasonal items']
      } as CompleteCatalogStats;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Launch complete catalog scraping
  const launchCompleteCatalog = useMutation({
    mutationFn: async () => {
      setIsLaunching(true);
      setCampaignStatus('running');
      
      // Generate ALL possible HomePro categories
      const mainCategories = ['APP', 'TOO', 'ELT', 'CON', 'FUR', 'BAT', 'KIT', 'LIG', 'PAI', 'PLU', 
                             'HHP', 'TVA', 'FLO', 'DOW', 'OUT', 'SMA', 'SPO', 'BEA', 'MOM', 'HEA', 
                             'PET', 'ATM', 'CLE', 'GAR', 'TIL', 'WOO', 'MET', 'PLA'];
      
      const allCategoryJobs = [];
      
      // Create jobs for all possible category combinations
      for (const mainCat of mainCategories) {
        // Main category with unlimited pages
        allCategoryJobs.push({
          job_type: 'category',
          target_url: `https://www.homepro.co.th/c/${mainCat}`,
          retailer_code: 'HP',
          max_pages: 999 // Unlimited - scrape until no more products
        });
        
        // Numbered subcategories (01-50)
        for (let i = 1; i <= 50; i++) {
          const subcat = `${mainCat}${i.toString().padStart(2, '0')}`;
          allCategoryJobs.push({
            job_type: 'category',
            target_url: `https://www.homepro.co.th/c/${subcat}`,
            retailer_code: 'HP',
            max_pages: 999
          });
        }
        
        // Letter subcategories (A-Z)
        for (let charCode = 65; charCode <= 90; charCode++) {
          const letter = String.fromCharCode(charCode);
          const subcat = `${mainCat}${letter}`;
          allCategoryJobs.push({
            job_type: 'category',
            target_url: `https://www.homepro.co.th/c/${subcat}`,
            retailer_code: 'HP',
            max_pages: 999
          });
        }
      }
      
      console.log(`🚀 Launching ${allCategoryJobs.length} jobs for complete catalog scraping`);
      
      // Launch jobs in batches to prevent overwhelming the system
      const batchSize = 10;
      const results = [];
      
      for (let i = 0; i < allCategoryJobs.length; i += batchSize) {
        const batch = allCategoryJobs.slice(i, i + batchSize);
        
        const batchPromises = batch.map(async (job) => {
          try {
            const response = await scrapingApi.createJob(job);
            return response.data;
          } catch (error) {
            // Category doesn't exist - this is expected for many combinations
            return null;
          }
        });
        
        const batchResults = await Promise.all(batchPromises);
        results.push(...batchResults.filter(result => result !== null));
        
        // Brief pause between batches
        if (i + batchSize < allCategoryJobs.length) {
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }
      
      return results;
    },
    onSuccess: (results) => {
      setIsLaunching(false);
      console.log(`✅ Successfully launched ${results.length} scraping jobs`);
    },
    onError: (error) => {
      setIsLaunching(false);
      setCampaignStatus('idle');
      console.error('❌ Failed to launch complete catalog scraping:', error);
    }
  });

  const completionPercentage = currentStats ? 
    Math.min((currentStats.current_products / currentStats.estimated_total) * 100, 100) : 0;

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Paper elevation={3} sx={{ p: 4, mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <InventoryIcon color="primary" fontSize="large" />
          Complete HomePro Catalog Scraping
        </Typography>
        
        <Typography variant="body1" color="text.secondary" paragraph>
          Scrape ALL available SKUs from HomePro's complete online catalog. This comprehensive 
          campaign discovers and scrapes every category, subcategory, and product variation.
        </Typography>

        {/* Current Status */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Current Products
                </Typography>
                <Typography variant="h3" color="primary">
                  {currentStats?.current_products.toLocaleString() || '0'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  SKUs in database
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Estimated Total
                </Typography>
                <Typography variant="h3" color="success.main">
                  {currentStats?.estimated_total.toLocaleString() || '50,000'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Complete catalog size
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Coverage
                </Typography>
                <Typography variant="h3" color="info.main">
                  {completionPercentage.toFixed(1)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={completionPercentage} 
                  sx={{ mt: 1, height: 8, borderRadius: 4 }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Campaign Strategy */}
        <Alert severity="info" sx={{ mb: 3 }}>
          <AlertTitle>Complete Catalog Strategy</AlertTitle>
          This campaign will discover and scrape:
          <Box sx={{ mt: 1 }}>
            <Chip label="28 main categories" size="small" sx={{ mr: 1, mb: 1 }} />
            <Chip label="1,400+ subcategories" size="small" sx={{ mr: 1, mb: 1 }} />
            <Chip label="Unlimited pagination" size="small" sx={{ mr: 1, mb: 1 }} />
            <Chip label="All product variants" size="small" sx={{ mr: 1, mb: 1 }} />
          </Box>
        </Alert>

        {/* Launch Controls */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="contained"
            size="large"
            startIcon={campaignStatus === 'running' ? <TimelineIcon /> : <RocketIcon />}
            onClick={() => launchCompleteCatalog.mutate()}
            disabled={isLaunching || campaignStatus === 'running'}
            color={campaignStatus === 'running' ? 'success' : 'primary'}
            sx={{ minWidth: 200 }}
          >
            {campaignStatus === 'running' ? 'Campaign Running...' : 
             isLaunching ? 'Launching...' : 
             'Launch Complete Catalog Scraping'}
          </Button>
          
          {campaignStatus === 'running' && (
            <Chip 
              icon={<CheckIcon />} 
              label="Campaign Active" 
              color="success" 
              variant="outlined" 
            />
          )}
        </Box>

        {/* Progress Information */}
        {(isLaunching || campaignStatus === 'running') && (
          <Box sx={{ mt: 3 }}>
            <Alert severity="warning">
              <AlertTitle>Campaign in Progress</AlertTitle>
              <Typography variant="body2">
                • Discovering and launching jobs for all possible HomePro categories<br/>
                • Each category will be scraped with unlimited pagination<br/>
                • Expected completion time: 15-30 hours<br/>
                • Monitor progress in the Jobs tab
              </Typography>
            </Alert>
          </Box>
        )}
      </Paper>
      
      {/* Quick Launch Section */}
      <Paper elevation={3} sx={{ mt: 3 }}>
        <QuickLaunch50K />
      </Paper>
    </Box>
  );
}