import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Chip,
  Alert,
  Avatar,
  Stack,
  Divider,
  LinearProgress,
  Fade,
  Zoom,
} from '@mui/material';
import {
  Inventory as InventoryIcon,
  Store as StoreIcon,
  Category as CategoryIcon,
  CompareArrows as CompareIcon,
  Savings as SavingsIcon,
  AttachMoney as PriceIcon,
} from '@mui/icons-material';
import { analyticsApi, retailerApi, priceComparisonApi } from '../services/api';
import { useRetailer } from '../contexts/RetailerContext';
import RetailerSelector from '../components/RetailerSelector';
import LoadingWrapper from '../components/LoadingWrapper';

const retailerColors: Record<string, string> = {
  'HP': '#FF6B35',   // HomePro Orange
  'TWD': '#1976D2',  // Thai Watsadu Blue
  'GH': '#4CAF50',   // Global House Green
  'DH': '#FF9800',   // DoHome Orange
  'BT': '#9C27B0',   // Boonthavorn Purple
  'MH': '#607D8B',   // MegaHome Blue Grey
};

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
  progress?: number;
  delay?: number;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color, subtitle, progress, delay = 0 }) => (
  <Zoom in timeout={300 + delay}>
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" alignItems="flex-start" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h5" component="div" fontWeight="bold">
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
            {progress !== undefined && (
              <Box sx={{ mt: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={progress}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    bgcolor: 'grey.200',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: color,
                    },
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  {progress.toFixed(1)}% coverage
                </Typography>
              </Box>
            )}
          </Box>
          <Avatar sx={{ bgcolor: color, width: 48, height: 48 }}>
            {icon}
          </Avatar>
        </Stack>
      </CardContent>
    </Card>
  </Zoom>
);

export default function Dashboard() {
  const { 
    selectedRetailer, 
    multiRetailerMode, 
    selectedRetailers, 
    retailerStats,
    getRetailerStats,
    isLoadingRetailers,
    isLoadingStats
  } = useRetailer();

  // Fetch dashboard data based on mode
  const { isLoading: loadingDashboard } = useQuery({
    queryKey: ['dashboard', multiRetailerMode ? 'multi' : selectedRetailer],
    queryFn: async () => {
      if (multiRetailerMode) {
        return await analyticsApi.getMultiRetailerDashboard();
      } else {
        return await analyticsApi.getDashboard(selectedRetailer || undefined);
      }
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch retailer summary for multi-retailer view
  const { isLoading: loadingSummary } = useQuery({
    queryKey: ['retailer-summary'],
    queryFn: async () => {
      const response = await retailerApi.getSummary();
      return response.data;
    },
    enabled: multiRetailerMode,
    refetchInterval: 30000,
  });

  // Fetch price comparison summary for multi-retailer view
  const { data: priceComparisonData } = useQuery({
    queryKey: ['price-comparison-summary'],
    queryFn: async () => {
      const response = await priceComparisonApi.getTopSavings(10);
      return response.data;
    },
    enabled: multiRetailerMode && selectedRetailers.length > 1,
    refetchInterval: 60000, // Refresh every minute
  });

  const isLoading = isLoadingRetailers || isLoadingStats || loadingDashboard || (multiRetailerMode && loadingSummary);

  // Show loading state while retailers are being loaded
  if (isLoadingRetailers) {
    return (
      <LoadingWrapper loading={true} loadingText="Loading retailers..." minHeight="100vh">
        <div />
      </LoadingWrapper>
    );
  }

  // Single retailer dashboard
  if (!multiRetailerMode && selectedRetailer) {
    const currentRetailerStats = getRetailerStats(selectedRetailer);
    
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>

        <RetailerSelector variant="full" showStats={true} showMultiMode={true} />

        {isLoading ? (
          <Box display="flex" justifyContent="center" mt={4}>
            <CircularProgress />
          </Box>
        ) : currentRetailerStats ? (
          <Fade in timeout={500}>
            <Grid container spacing={3} mt={1}>
              <Grid item xs={12} sm={6} md={3}>
                <StatCard
                  title="Total Products"
                  value={currentRetailerStats.actual_products?.toLocaleString() || '0'}
                  icon={<InventoryIcon />}
                  color={retailerColors[selectedRetailer]}
                  subtitle={`Est: ${currentRetailerStats.actual_products?.toLocaleString() || '0'}`}
                  delay={0}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <StatCard
                  title="In Stock"
                  value={currentRetailerStats.in_stock_products?.toLocaleString() || '0'}
                  icon={<StoreIcon />}
                  color="#4CAF50"
                  progress={currentRetailerStats.actual_products > 0 ? 
                    (currentRetailerStats.in_stock_products / currentRetailerStats.actual_products) * 100 : 0}
                  delay={100}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <StatCard
                  title="Average Price"
                  value={`฿${currentRetailerStats.avg_price?.toFixed(0) || '0'}`}
                  icon={<PriceIcon />}
                  color="#FF9800"
                  subtitle={`Range: ฿${currentRetailerStats.min_price?.toFixed(0) || '0'} - ฿${currentRetailerStats.max_price?.toFixed(0) || '0'}`}
                  delay={200}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <StatCard
                  title="Category Coverage"
                  value={`${currentRetailerStats.category_coverage_percentage?.toFixed(1) || '0'}%`}
                  icon={<CategoryIcon />}
                  color="#9C27B0"
                  progress={currentRetailerStats.category_coverage_percentage || 0}
                  delay={300}
                />
              </Grid>
            </Grid>
          </Fade>
        ) : (
          <Alert severity="warning" sx={{ mt: 2 }}>
            No data available for the selected retailer.
          </Alert>
        )}
      </Box>
    );
  }

  // Multi-retailer dashboard
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Multi-Retailer Dashboard
      </Typography>

      <RetailerSelector variant="full" showStats={true} showMultiMode={true} />

      {isLoading ? (
        <Box display="flex" justifyContent="center" mt={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Overview Stats */}
          <Grid container spacing={3} mt={1}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Products"
                value={retailerStats.reduce((sum, stat) => sum + stat.actual_products, 0).toLocaleString()}
                icon={<InventoryIcon />}
                color="#1976D2"
                subtitle={`Across ${selectedRetailers.length} retailers`}
                delay={0}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Products In Stock"
                value={retailerStats.reduce((sum, stat) => sum + stat.in_stock_products, 0).toLocaleString()}
                icon={<StoreIcon />}
                color="#4CAF50"
                subtitle="Available for purchase"
                delay={100}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Active Retailers"
                value={selectedRetailers.length}
                icon={<CompareIcon />}
                color="#FF9800"
                subtitle="Being monitored"
                delay={200}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Potential Savings"
                value={priceComparisonData?.savings_opportunities ? 
                  `฿${priceComparisonData.savings_opportunities.slice(0, 10).reduce((sum: number, item: any) => sum + item.savings_amount, 0).toLocaleString()}` : 
                  '฿0'}
                icon={<SavingsIcon />}
                color="#E91E63"
                subtitle="Top 10 opportunities"
                delay={300}
              />
            </Grid>
          </Grid>

          {/* Retailer Breakdown */}
          <Paper sx={{ mt: 3, p: 3 }}>
            <Typography variant="h6" gutterBottom>
              📊 Retailer Performance Overview
            </Typography>
            
            <Grid container spacing={2}>
              {retailerStats
                .filter(stat => selectedRetailers.includes(stat.code))
                .map((stat, index) => (
                  <Grid item xs={12} md={6} lg={4} key={stat.code}>
                    <Fade in timeout={300 + index * 100}>
                      <Card variant="outlined" sx={{ height: '100%' }}>
                        <CardContent>
                          <Stack direction="row" alignItems="center" spacing={2} mb={2}>
                            <Avatar
                              sx={{
                                bgcolor: retailerColors[stat.code] || '#666',
                                width: 40,
                                height: 40,
                              }}
                            >
                              {stat.code}
                            </Avatar>
                            <Box flex={1}>
                              <Typography variant="h6" fontWeight="bold">
                                {stat.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Market Position: Leading Retailer
                              </Typography>
                            </Box>
                          </Stack>

                          <Divider sx={{ mb: 2 }} />

                          <Grid container spacing={2}>
                            <Grid item xs={6}>
                              <Typography variant="body2" color="text.secondary">
                                Products
                              </Typography>
                              <Typography variant="h6" fontWeight="bold">
                                {stat.actual_products.toLocaleString()}
                              </Typography>
                            </Grid>
                            <Grid item xs={6}>
                              <Typography variant="body2" color="text.secondary">
                                In Stock
                              </Typography>
                              <Typography variant="h6" fontWeight="bold" color="success.main">
                                {stat.in_stock_products.toLocaleString()}
                              </Typography>
                            </Grid>
                            <Grid item xs={6}>
                              <Typography variant="body2" color="text.secondary">
                                Avg Price
                              </Typography>
                              <Typography variant="h6" fontWeight="bold">
                                ฿{stat.avg_price?.toFixed(0) || '0'}
                              </Typography>
                            </Grid>
                            <Grid item xs={6}>
                              <Typography variant="body2" color="text.secondary">
                                Coverage
                              </Typography>
                              <Typography variant="h6" fontWeight="bold">
                                {stat.category_coverage_percentage?.toFixed(1) || '0'}%
                              </Typography>
                            </Grid>
                          </Grid>

                          {/* Monitoring Tier Distribution */}
                          <Box mt={2}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              Monitoring Tiers
                            </Typography>
                            <Stack direction="row" spacing={1} flexWrap="wrap">
                              <Chip
                                label={`Ultra: ${stat.ultra_critical_count}`}
                                size="small"
                                color="error"
                                variant="outlined"
                              />
                              <Chip
                                label={`High: ${stat.high_value_count}`}
                                size="small"
                                color="warning"
                                variant="outlined"
                              />
                              <Chip
                                label={`Standard: ${stat.standard_count}`}
                                size="small"
                                color="info"
                                variant="outlined"
                              />
                              <Chip
                                label={`Low: ${stat.low_priority_count}`}
                                size="small"
                                color="default"
                                variant="outlined"
                              />
                            </Stack>
                          </Box>
                        </CardContent>
                      </Card>
                    </Fade>
                  </Grid>
                ))}
            </Grid>
          </Paper>

          {/* Price Comparison Preview */}
          {selectedRetailers.length > 1 && priceComparisonData?.savings_opportunities && (
            <Paper sx={{ mt: 3, p: 3 }}>
              <Typography variant="h6" gutterBottom>
                💰 Top Savings Opportunities
              </Typography>
              
              <Grid container spacing={2}>
                {priceComparisonData.savings_opportunities.slice(0, 6).map((opportunity: any, index: number) => (
                  <Grid item xs={12} md={6} lg={4} key={index}>
                    <Zoom in timeout={300 + index * 100}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle2" fontWeight="bold" gutterBottom noWrap>
                            {opportunity.product_name}
                          </Typography>
                          
                          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
                            <Chip label={opportunity.category} size="small" variant="outlined" />
                            <Typography variant="h6" color="success.main" fontWeight="bold">
                              ฿{opportunity.savings_amount.toFixed(2)}
                            </Typography>
                          </Stack>

                          <Typography variant="body2" color="text.secondary" mb={1}>
                            {opportunity.price_range}
                          </Typography>

                          <Stack direction="row" justifyContent="space-between" alignItems="center">
                            <Typography variant="caption" color="text.secondary">
                              Best at:
                            </Typography>
                            <Chip
                              label={opportunity.best_retailer}
                              size="small"
                              sx={{
                                bgcolor: `${retailerColors[opportunity.best_retailer] || '#666'}15`,
                                color: retailerColors[opportunity.best_retailer] || '#666',
                                fontWeight: 'bold',
                              }}
                            />
                          </Stack>
                        </CardContent>
                      </Card>
                    </Zoom>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          )}
        </>
      )}
    </Box>
  );
}