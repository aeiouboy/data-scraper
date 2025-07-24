import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Grid,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Skeleton,
  Fade,
  ToggleButton,
  ToggleButtonGroup,
  Container,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
} from '@mui/material';
import {
  TrendingDown as SavingsIcon,
  CompareArrows as CompareIcon,
  LocalOffer as OfferIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  ViewModule as GridViewIcon,
  ViewList as ListViewIcon,
  Analytics as AnalyticsIcon,
  Psychology as OptimizeIcon,
  ExpandMore as ExpandMoreIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { priceComparisonApi } from '../services/api';
import { optimizedMatchingApi, matchingUtils } from '../services/optimizedMatchingApi';
import { useRetailer } from '../contexts/RetailerContext';
import RetailerSelector from '../components/RetailerSelector';
import OptimizedPriceComparison from '../components/OptimizedPriceComparison';

const retailerColors: Record<string, string> = {
  'HP': '#FF6B35',   // HomePro Orange
  'TWD': '#1976D2',  // Thai Watsadu Blue
  'GH': '#4CAF50',   // Global House Green
  'DH': '#FF9800',   // DoHome Orange
  'BT': '#9C27B0',   // Boonthavorn Purple
  'MH': '#E91E63',   // MegaHome Pink
};

interface ComparisonFilters {
  minSavings: number;
  minSavingsPercent: number;
  minConfidence: number;
  category: string;
  sortBy: string;
  order: 'asc' | 'desc';
  limit: number;
  useOptimized: boolean;
}

const OptimizedPriceComparisons: React.FC = () => {
  useRetailer();
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [showOptimizedFeatures] = useState(true);
  
  const [filters, setFilters] = useState<ComparisonFilters>({
    minSavings: 100,
    minSavingsPercent: 5,
    minConfidence: 0.6,
    category: '',
    sortBy: 'savings_amount',
    order: 'desc',
    limit: 50,
    useOptimized: true,
  });

  // Fetch optimized price comparisons
  const { data: optimizedComparisons, isLoading: optimizedLoading, error: optimizedError } = useQuery({
    queryKey: ['optimized-price-comparisons', filters],
    queryFn: () => priceComparisonApi.getDetailedComparisonsOptimized({
      minSavings: filters.minSavings,
      minSavingsPercent: filters.minSavingsPercent,
      minConfidence: filters.minConfidence,
      category: filters.category || undefined,
      sortBy: filters.sortBy,
      order: filters.order,
      limit: filters.limit,
    }),
    enabled: filters.useOptimized,
  });

  // Fetch standard price comparisons for comparison
  const { data: standardComparisons, isLoading: standardLoading } = useQuery({
    queryKey: ['standard-price-comparisons', filters],
    queryFn: () => priceComparisonApi.getDetailedComparisons({
      minSavings: filters.minSavings,
      minSavingsPercent: filters.minSavingsPercent,
      minConfidence: filters.minConfidence,
      category: filters.category || undefined,
      limit: filters.limit,
    }),
    enabled: !filters.useOptimized,
  });

  // Fetch optimized matching statistics
  const { data: matchingStats } = useQuery({
    queryKey: ['optimized-matching-stats'],
    queryFn: () => optimizedMatchingApi.getStatistics(),
    refetchInterval: 60000, // Refresh every minute
  });

  // Fetch categories for filtering
  const { data: categories } = useQuery({
    queryKey: ['categories-with-savings'],
    queryFn: () => priceComparisonApi.getCategoriesWithSavings(),
  });

  // Fetch quick stats
  const { data: quickStats } = useQuery({
    queryKey: ['quick-stats', filters.category],
    queryFn: () => priceComparisonApi.getQuickStats(filters.category || undefined),
  });

  const currentData = filters.useOptimized ? optimizedComparisons : standardComparisons;
  const isLoading = filters.useOptimized ? optimizedLoading : standardLoading;
  const currentError = filters.useOptimized ? optimizedError : null;

  const handleFilterChange = (key: keyof ComparisonFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('th-TH', {
      style: 'currency',
      currency: 'THB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercent = (value: number): string => {
    return `${value.toFixed(1)}%`;
  };

  const getRetailerChip = (retailerCode: string, productName: string) => (
    <Chip
      label={retailerCode}
      size="small"
      style={{
        backgroundColor: retailerColors[retailerCode] || '#666',
        color: 'white',
        fontWeight: 'bold',
      }}
    />
  );

  const renderOptimizedFeaturesBanner = () => (
    <Fade in={showOptimizedFeatures}>
      <Card sx={{ mb: 3, bgcolor: 'primary.main', color: 'white' }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box display="flex" alignItems="center" gap={2}>
              <OptimizeIcon fontSize="large" />
              <Box>
                <Typography variant="h6" gutterBottom>
                  🚀 Optimized Price Matching Active
                </Typography>
                <Typography variant="body2">
                  Enhanced with 50% better accuracy, Thai-English support, and progressive matching
                </Typography>
              </Box>
            </Box>
            <Box textAlign="right">
              <FormControlLabel
                control={
                  <Switch
                    checked={filters.useOptimized}
                    onChange={(e) => handleFilterChange('useOptimized', e.target.checked)}
                    color="secondary"
                  />
                }
                label="Use Optimized Matching"
              />
            </Box>
          </Box>
          
          {matchingStats?.data?.statistics?.matcher_info && (
            <Box mt={2}>
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <Box textAlign="center">
                    <Typography variant="h6">
                      {matchingStats.data.statistics.matcher_info.enhanced_brands || 0}
                    </Typography>
                    <Typography variant="caption">
                      Brand Variations
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box textAlign="center">
                    <Typography variant="h6">
                      {matchingStats.data.statistics.matcher_info.progressive_tiers?.length || 0}
                    </Typography>
                    <Typography variant="caption">
                      Matching Tiers
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box textAlign="center">
                    <Typography variant="h6">
                      {matchingStats.data.statistics.cache_size || 0}
                    </Typography>
                    <Typography variant="caption">
                      Cached Results
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box textAlign="center">
                    <Typography variant="h6">
                      {matchingStats.data.statistics.configuration?.max_workers || 4}
                    </Typography>
                    <Typography variant="caption">
                      Worker Threads
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>
    </Fade>
  );

  const renderQuickStats = () => (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="between">
              <Box>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Total Comparisons
                </Typography>
                <Typography variant="h6">
                  {quickStats?.data?.total_comparisons?.toLocaleString() || 0}
                </Typography>
              </Box>
              <CompareIcon color="primary" />
            </Box>
            {filters.useOptimized && (
              <Chip
                label="Optimized"
                color="success"
                size="small"
                icon={<OptimizeIcon />}
                sx={{ mt: 1 }}
              />
            )}
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="between">
              <Box>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Total Savings
                </Typography>
                <Typography variant="h6">
                  {formatCurrency(quickStats?.data?.total_savings || 0)}
                </Typography>
              </Box>
              <SavingsIcon color="success" />
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="between">
              <Box>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Avg Confidence
                </Typography>
                <Typography variant="h6">
                  {formatPercent((quickStats?.data?.average_confidence || 0) * 100)}
                </Typography>
              </Box>
              <AnalyticsIcon color="info" />
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} sm={6} md={3}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="between">
              <Box>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  Best Deal
                </Typography>
                <Typography variant="h6">
                  {formatPercent(quickStats?.data?.max_savings_percent || 0)}
                </Typography>
              </Box>
              <OfferIcon color="warning" />
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderFilters = () => (
    <Accordion sx={{ mb: 3 }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box display="flex" alignItems="center" gap={1}>
          <FilterIcon />
          <Typography variant="h6">Filters & Configuration</Typography>
          {filters.useOptimized && (
            <Chip label="Optimized" color="success" size="small" />
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              label="Min Savings (฿)"
              type="number"
              value={filters.minSavings}
              onChange={(e) => handleFilterChange('minSavings', Number(e.target.value))}
              fullWidth
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              label="Min Savings (%)"
              type="number"
              value={filters.minSavingsPercent}
              onChange={(e) => handleFilterChange('minSavingsPercent', Number(e.target.value))}
              fullWidth
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              label="Min Confidence"
              type="number"
              value={filters.minConfidence}
              onChange={(e) => handleFilterChange('minConfidence', Number(e.target.value))}
              inputProps={{ min: 0, max: 1, step: 0.1 }}
              fullWidth
              helperText={filters.useOptimized ? "Optimized: Lower thresholds for better recall" : "Standard matching"}
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                label="Category"
              >
                <MenuItem value="">All Categories</MenuItem>
                {categories?.data?.map((cat: any) => (
                  <MenuItem key={cat.category} value={cat.category}>
                    {cat.category} ({cat.comparison_count})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth>
              <InputLabel>Sort By</InputLabel>
              <Select
                value={filters.sortBy}
                onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                label="Sort By"
              >
                <MenuItem value="savings_amount">Savings Amount</MenuItem>
                <MenuItem value="savings_percent">Savings Percent</MenuItem>
                <MenuItem value="confidence">Confidence</MenuItem>
                <MenuItem value="created_at">Date Created</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              label="Results Limit"
              type="number"
              value={filters.limit}
              onChange={(e) => handleFilterChange('limit', Number(e.target.value))}
              inputProps={{ min: 10, max: 200 }}
              fullWidth
            />
          </Grid>
        </Grid>
        
        {filters.useOptimized && matchingStats?.data?.statistics?.configuration?.confidence_thresholds && (
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Optimized Configuration:</strong> {' '}
              Auto-accept: {((matchingStats.data.statistics.configuration.confidence_thresholds.auto_accept || 0.85) * 100).toFixed(0)}%, {' '}
              Manual review: {((matchingStats.data.statistics.configuration.confidence_thresholds.manual_review || 0.45) * 100).toFixed(0)}%, {' '}
              Auto-reject: {((matchingStats.data.statistics.configuration.confidence_thresholds.auto_reject || 0.25) * 100).toFixed(0)}%
            </Typography>
          </Alert>
        )}
      </AccordionDetails>
    </Accordion>
  );

  const renderComparisonCard = (comparison: any) => {
    const confidenceColor = matchingUtils.getConfidenceColor(comparison.confidence);
    const savings = comparison.best_deal_price && comparison.worst_deal_price
      ? comparison.worst_deal_price - comparison.best_deal_price
      : 0;
    const savingsPercent = comparison.worst_deal_price > 0
      ? ((comparison.worst_deal_price - comparison.best_deal_price) / comparison.worst_deal_price) * 100
      : 0;

    return (
      <Card key={comparison.id} sx={{ mb: 2, border: `2px solid ${confidenceColor}20` }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box flex={1}>
              <Typography variant="h6" gutterBottom>
                {comparison.product_name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {comparison.brand} • {comparison.category}
              </Typography>
              
              {filters.useOptimized && (
                <Box display="flex" gap={1} mt={1}>
                  <Chip
                    label={`${(comparison.confidence * 100).toFixed(1)}% confidence`}
                    size="small"
                    style={{ backgroundColor: confidenceColor, color: 'white' }}
                  />
                  <Chip
                    label="Optimized Match"
                    size="small"
                    color="success"
                    icon={<OptimizeIcon />}
                  />
                </Box>
              )}
            </Box>
            
            <Box textAlign="right">
              <Typography variant="h5" color="success.main">
                {formatCurrency(savings)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Save {formatPercent(savingsPercent)}
              </Typography>
              <Button
                variant="outlined"
                size="small"
                startIcon={<CompareIcon />}
                onClick={() => setSelectedProduct(comparison.id)}
                sx={{ mt: 1 }}
              >
                Compare
              </Button>
            </Box>
          </Box>

          {/* Price comparison details */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Price Range:
            </Typography>
            <Box display="flex" gap={2} flexWrap="wrap">
              <Box display="flex" alignItems="center" gap={1}>
                {getRetailerChip(comparison.best_deal_retailer, '')}
                <Typography variant="body2">
                  {formatCurrency(comparison.best_deal_price)} (Best)
                </Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={1}>
                {getRetailerChip(comparison.worst_deal_retailer, '')}
                <Typography variant="body2">
                  {formatCurrency(comparison.worst_deal_price)} (Highest)
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* Optimized matching details */}
          {filters.useOptimized && comparison.matching_details && (
            <Box mt={2}>
              <Typography variant="subtitle2" gutterBottom>
                Match Quality:
              </Typography>
              <Grid container spacing={1}>
                {Object.entries(comparison.matching_details).map(([key, value]: [string, any]) => (
                  <Grid item xs={6} sm={3} key={key}>
                    <Box textAlign="center">
                      <Typography variant="caption" display="block">
                        {key.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={value * 100}
                        color={value > 0.8 ? 'success' : value > 0.5 ? 'warning' : 'error'}
                        sx={{ height: 6, borderRadius: 3 }}
                      />
                      <Typography variant="caption">
                        {(value * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  if (isLoading) {
    return (
      <Container maxWidth="xl">
        <Box py={3}>
          <Skeleton variant="rectangular" height={200} sx={{ mb: 3 }} />
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="rectangular" height={150} sx={{ mb: 2 }} />
          ))}
        </Box>
      </Container>
    );
  }

  if (currentError) {
    return (
      <Container maxWidth="xl">
        <Box py={3}>
          <Alert severity="error" action={
            <Button color="inherit" startIcon={<RefreshIcon />}>
              Retry
            </Button>
          }>
            Failed to load price comparisons: {currentError && typeof currentError === 'object' && 'message' in currentError ? String(currentError.message) : 'Unknown error'}
          </Alert>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box py={3}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            {filters.useOptimized ? '🚀 Optimized' : '📊 Standard'} Price Comparisons
          </Typography>
          
          <Box display="flex" gap={2} alignItems="center">
            <ToggleButtonGroup
              value={view}
              exclusive
              onChange={(_, newView) => newView && setView(newView)}
              size="small"
            >
              <ToggleButton value="grid">
                <GridViewIcon />
              </ToggleButton>
              <ToggleButton value="list">
                <ListViewIcon />
              </ToggleButton>
            </ToggleButtonGroup>
            
            <RetailerSelector />
          </Box>
        </Box>

        {/* Optimized features banner */}
        {renderOptimizedFeaturesBanner()}

        {/* Quick stats */}
        {renderQuickStats()}

        {/* Filters */}
        {renderFilters()}

        {/* Results */}
        {currentData?.data?.comparisons?.length > 0 ? (
          <Box>
            <Typography variant="h6" gutterBottom>
              Found {currentData?.data?.comparisons?.length || 0} price comparisons
              {filters.useOptimized && (
                <Chip
                  label="Enhanced Matching"
                  color="success"
                  size="small"
                  icon={<TrendingUpIcon />}
                  sx={{ ml: 1 }}
                />
              )}
            </Typography>
            
            {currentData?.data?.comparisons?.map((comparison: any) => (
              renderComparisonCard(comparison)
            )) || []}
          </Box>
        ) : (
          <Alert severity="info">
            No price comparisons found with current filters.
            {filters.useOptimized && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                💡 Try lowering the confidence threshold for more results with optimized matching.
              </Typography>
            )}
          </Alert>
        )}

        {/* Selected product detailed comparison */}
        {selectedProduct && (
          <Box mt={4}>
            <OptimizedPriceComparison
              productId={selectedProduct}
              showConfiguration={true}
              autoRefresh={false}
              minConfidence={filters.minConfidence}
            />
          </Box>
        )}
      </Box>
    </Container>
  );
};

export default OptimizedPriceComparisons;