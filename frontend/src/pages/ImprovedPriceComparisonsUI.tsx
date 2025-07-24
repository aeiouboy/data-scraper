import React, { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Grid,
  Stack,
  Avatar,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Skeleton,
  ToggleButton,
  ToggleButtonGroup,
  Container,
  Divider,
  IconButton,
  Tooltip,
  useTheme,
  alpha,
  Backdrop,
  CircularProgress,
} from '@mui/material';
import {
  TrendingDown as SavingsIcon,
  Store as StoreIcon,
  CompareArrows as CompareIcon,
  LocalOffer as OfferIcon,
  Refresh as RefreshIcon,
  ViewModule as GridViewIcon,
  ViewList as ListViewIcon,
  Analytics as AnalyticsIcon,
  TuneOutlined as TuneIcon,
  SearchOutlined as SearchIcon,
  TrendingUpOutlined as TrendingUpIcon,
  InfoOutlined as InfoIcon,
  ExpandMoreOutlined as ExpandMoreIcon,
  ExpandLessOutlined as ExpandLessIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { priceComparisonApi } from '../services/api';
import { useRetailer } from '../contexts/RetailerContext';
import RetailerSelector from '../components/RetailerSelector';
import PriceTrackingDashboard from '../components/PriceTrackingDashboard';
import FunctionalPriceComparisonCard from '../components/FunctionalPriceComparisonCard';



const ImprovedPriceComparisonsUI: React.FC = () => {
  const theme = useTheme();
  const { selectedRetailers, multiRetailerMode } = useRetailer();
  
  // Enhanced state management
  const [categoryFilter] = useState('');
  const [minSavings, setMinSavings] = useState(100);
  const [minSavingsInput, setMinSavingsInput] = useState(100);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'analytics'>('grid');
  const [currentPage, setCurrentPage] = useState(0);
  const [sortBy, setSortBy] = useState('savings_amount');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [matcherMode, setMatcherMode] = useState<'standard' | 'ultra-strict'>('standard');
  
  const itemsPerPage = 12;

  // Debounced update for minSavings
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setMinSavings(minSavingsInput);
      setCurrentPage(0);
    }, 500);
    return () => clearTimeout(timer);
  }, [minSavingsInput]);

  // Enhanced data fetching with better error handling
  const { 
    data: detailedData, 
    isLoading: loadingDetailed, 
    error: detailedError,
    refetch: refetchDetailed 
  } = useQuery({
    queryKey: ['price-comparisons-v2', 'detailed', minSavings, categoryFilter, currentPage, sortBy, sortOrder, matcherMode],
    queryFn: async () => {
      const response = await priceComparisonApi.getDetailedComparisons({
        limit: viewMode === 'grid' ? itemsPerPage : 50,
        offset: viewMode === 'grid' ? currentPage * itemsPerPage : 0,
        minSavings: minSavings,
        category: categoryFilter || undefined,
        matcher_mode: matcherMode, // Add matcher mode parameter
      });
      return response.data;
    },
    enabled: multiRetailerMode && selectedRetailers.length > 1,
    staleTime: 60000,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  // Quick stats with enhanced presentation
  const { data: quickStats, isLoading: loadingStats } = useQuery({
    queryKey: ['quick-stats-enhanced', categoryFilter],
    queryFn: async () => {
      const response = await priceComparisonApi.getQuickStats(categoryFilter || undefined);
      return response.data;
    },
    enabled: multiRetailerMode && selectedRetailers.length > 1,
    staleTime: 30000,
  });

  // Add matching analytics query
  const { data: matchingAnalytics } = useQuery({
    queryKey: ['matchingAnalytics'],
    queryFn: async () => {
      const response = await priceComparisonApi.getMatchingAnalytics();
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });

  const comparisons = useMemo(() => detailedData?.comparisons || [], [detailedData]);

  // Enhanced matching analytics display
  const renderMatchingAnalytics = () => {
    if (!matchingAnalytics) return null;

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Paper 
          sx={{ 
            p: 3, 
            mb: 3, 
            background: `linear-gradient(135deg, ${alpha(theme.palette.success.main, 0.1)} 0%, ${alpha(theme.palette.info.main, 0.1)} 100%)`,
            border: `1px solid ${alpha(theme.palette.success.main, 0.2)}`
          }}
        >
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon color="success" />
            Matching System Status
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" fontWeight="bold" color="success.main">
                  {matchingAnalytics.match_statistics?.total_products_matched || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Products Matched
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" fontWeight="bold" color="primary.main">
                  {matchingAnalytics.manual_review_stats?.accuracy_rate?.toFixed(1) || 0}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Matching Accuracy
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" fontWeight="bold" color="info.main">
                  {matchingAnalytics.manual_review_stats?.confirmed_matches || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Confirmed Matches
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" fontWeight="bold" color="warning.main">
                  {matchingAnalytics.manual_review_stats?.rejected_matches || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Rejected Matches
                </Typography>
              </Box>
            </Grid>
          </Grid>

          {matchingAnalytics.match_statistics?.average_price_variance && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Average Price Variance: {matchingAnalytics.match_statistics.average_price_variance.toFixed(1)}%
              </Typography>
            </Box>
          )}
        </Paper>
      </motion.div>
    );
  };

  // Enhanced filtering and sorting
  const filteredComparisons = useMemo(() => {
    let filtered = comparisons;
    
    if (searchQuery) {
      filtered = filtered.filter((comp: any) => 
        comp.productName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        comp.brand?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        comp.category?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    return filtered.sort((a: any, b: any) => {
      const aVal = a.priceAnalysis?.[sortBy] || 0;
      const bVal = b.priceAnalysis?.[sortBy] || 0;
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });
  }, [comparisons, searchQuery, sortBy, sortOrder]);

  const handleRefreshAll = useCallback(async () => {
    await Promise.all([refetchDetailed()]);
  }, [refetchDetailed]);

  // Enhanced loading states
  const renderEnhancedLoading = () => (
    <Box sx={{ position: 'relative', minHeight: '60vh' }}>
      <Backdrop open={true} data-testid="loading-backdrop" sx={{ bgcolor: alpha(theme.palette.background.default, 0.8), zIndex: 1 }}>
        <Box textAlign="center">
          <CircularProgress size={60} thickness={4} />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Loading price comparisons...
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Analyzing deals across {selectedRetailers.length} retailers
          </Typography>
        </Box>
      </Backdrop>
    </Box>
  );

  // Enhanced header with professional styling
  const renderEnhancedHeader = () => (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <Box data-testid="enhanced-header" sx={{ 
        background: `linear-gradient(135deg, ${theme.palette.primary.main}20 0%, ${theme.palette.secondary.main}20 100%)`,
        borderRadius: 3,
        p: 4,
        mb: 4,
        position: 'relative',
        overflow: 'hidden'
      }}>
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} alignItems={{ xs: 'flex-start', md: 'center' }} justifyContent="space-between">
            <Box>
              <Typography variant="h3" fontWeight="bold" gutterBottom sx={{ 
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                💰 Smart Price Comparisons
              </Typography>
              <Typography variant="h6" color="text.secondary">
                Find the best deals across {selectedRetailers.length} trusted retailers
              </Typography>
            </Box>
            
            <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap' }}>
              <ToggleButtonGroup
                value={matcherMode}
                exclusive
                onChange={(_, newMode) => newMode && setMatcherMode(newMode)}
                size="small"
                sx={{ 
                  borderRadius: 2,
                  '& .MuiToggleButton-root.Mui-selected': {
                    bgcolor: matcherMode === 'ultra-strict' ? 'error.main' : 'primary.main',
                    color: 'white',
                    '&:hover': {
                      bgcolor: matcherMode === 'ultra-strict' ? 'error.dark' : 'primary.dark',
                    }
                  }
                }}
              >
                <ToggleButton value="standard">
                  🔍 Standard
                </ToggleButton>
                <ToggleButton value="ultra-strict">
                  🎯 Ultra-Strict
                </ToggleButton>
              </ToggleButtonGroup>

              <Button
                variant="contained"
                startIcon={<RefreshIcon />}
                onClick={handleRefreshAll}
                disabled={loadingDetailed}
                sx={{ borderRadius: 2 }}
              >
                Refresh Data
              </Button>
              
              <ToggleButtonGroup
                value={viewMode}
                exclusive
                onChange={(_, newMode) => newMode && setViewMode(newMode)}
                size="medium"
                sx={{ 
                  '& .MuiToggleButton-root': { 
                    borderRadius: 2,
                    border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
                  }
                }}
              >
                <ToggleButton value="grid">
                  <GridViewIcon sx={{ mr: 1 }} />
                  Grid
                </ToggleButton>
                <ToggleButton value="list">
                  <ListViewIcon sx={{ mr: 1 }} />
                  List
                </ToggleButton>
                <ToggleButton value="analytics">
                  <AnalyticsIcon sx={{ mr: 1 }} />
                  Analytics
                </ToggleButton>
              </ToggleButtonGroup>
            </Stack>
          </Stack>
        </Box>
        
        {/* Decorative elements */}
        <Box sx={{
          position: 'absolute',
          top: -50,
          right: -50,
          width: 150,
          height: 150,
          borderRadius: '50%',
          background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
          zIndex: 0,
        }} />
      </Box>
    </motion.div>
  );

  // Enhanced statistics cards with animations
  const renderEnhancedStats = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
    >
      <Grid container spacing={3} sx={{ mb: 4 }} data-testid="stats-grid">
        {[
          {
            title: 'Total Savings',
            value: `฿${(quickStats?.totalSavings || 0).toLocaleString()}`,
            icon: SavingsIcon,
            color: theme.palette.success.main,
            description: 'Available across all retailers'
          },
          {
            title: 'Best Deals',
            value: filteredComparisons.length.toLocaleString(),
            icon: OfferIcon,
            color: theme.palette.warning.main,
            description: 'Products with significant savings'
          },
          {
            title: 'Average Savings',
            value: `${((quickStats?.averageSavings || 0) * 100).toFixed(1)}%`,
            icon: TrendingUpIcon,
            color: theme.palette.info.main,
            description: 'Typical discount across products'
          },
          {
            title: 'Retailers',
            value: selectedRetailers.length.toString(),
            icon: StoreIcon,
            color: theme.palette.primary.main,
            description: 'Active price sources'
          },
        ].map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={stat.title}>
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.1 * index }}
              whileHover={{ scale: 1.02 }}
            >
              <Card data-testid="stats-card" sx={{ 
                height: '100%',
                background: `linear-gradient(135deg, ${alpha(stat.color, 0.1)} 0%, ${alpha(stat.color, 0.05)} 100%)`,
                border: `1px solid ${alpha(stat.color, 0.2)}`,
                transition: 'all 0.3s ease',
                '&:hover': {
                  boxShadow: `0 8px 32px ${alpha(stat.color, 0.2)}`,
                  transform: 'translateY(-2px)',
                }
              }}>
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Avatar sx={{ 
                      bgcolor: stat.color, 
                      width: 56, 
                      height: 56,
                      boxShadow: `0 4px 12px ${alpha(stat.color, 0.3)}`,
                    }}>
                      <stat.icon fontSize="large" />
                    </Avatar>
                    <Box flex={1}>
                      <Typography variant="h4" fontWeight="bold" color={stat.color}>
                        {loadingStats ? <Skeleton width={80} /> : stat.value}
                      </Typography>
                      <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                        {stat.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {stat.description}
                      </Typography>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        ))}
      </Grid>
    </motion.div>
  );

  // Enhanced filters panel
  const renderEnhancedFilters = () => (
    <AnimatePresence>
      {showFilters && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Paper sx={{ 
            p: 3, 
            mb: 3, 
            background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.default, 0.9)} 100%)`,
            backdropFilter: 'blur(10px)',
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          }}>
            <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
              <TuneIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Smart Filters
              </Typography>
              <Chip label="Advanced" color="primary" size="small" />
            </Stack>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Search Products"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  InputProps={{
                    startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
                  }}
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Minimum Savings (฿)"
                  type="number"
                  value={minSavingsInput}
                  onChange={(e) => setMinSavingsInput(Number(e.target.value))}
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
                />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Sort By</InputLabel>
                  <Select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    sx={{ borderRadius: 2 }}
                  >
                    <MenuItem value="savings_amount">Savings Amount</MenuItem>
                    <MenuItem value="savings_percentage">Savings Percentage</MenuItem>
                    <MenuItem value="confidence">Match Confidence</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>
        </motion.div>
      )}
    </AnimatePresence>
  );

  // Enhanced control bar
  const renderControlBar = () => (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: 0.3 }}
    >
      <Paper sx={{ 
        p: 2, 
        mb: 3, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        background: alpha(theme.palette.background.paper, 0.9),
        backdropFilter: 'blur(10px)',
      }}>
        <Stack direction="row" alignItems="center" spacing={2}>
          <Button
            variant={showFilters ? "contained" : "outlined"}
            startIcon={showFilters ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            onClick={() => setShowFilters(!showFilters)}
            sx={{ borderRadius: 2 }}
          >
            {showFilters ? 'Hide' : 'Show'} Filters
          </Button>
          
          <Divider orientation="vertical" flexItem />
          
          <Typography variant="body2" color="text.secondary">
            {filteredComparisons.length} deals found
          </Typography>
          
          {searchQuery && (
            <Chip 
              label={`Search: "${searchQuery}"`} 
              onDelete={() => setSearchQuery('')}
              size="small"
              color="primary"
              variant="outlined"
            />
          )}
        </Stack>
        
        <Stack direction="row" alignItems="center" spacing={1}>
          <Tooltip title="Sort order">
            <IconButton 
              onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
              size="small"
            >
              <TrendingUpIcon sx={{ 
                transform: sortOrder === 'asc' ? 'rotate(180deg)' : 'none',
                transition: 'transform 0.3s ease'
              }} />
            </IconButton>
          </Tooltip>
          
          <Typography variant="caption" color="text.secondary">
            {sortOrder === 'desc' ? 'High to Low' : 'Low to High'}
          </Typography>
        </Stack>
      </Paper>
    </motion.div>
  );

  // Single retailer mode with enhanced styling
  if (!multiRetailerMode || selectedRetailers.length < 2) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
        >
          <Paper sx={{ 
            p: 6, 
            textAlign: 'center',
            background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
          }}>
            <Avatar sx={{ 
              width: 80, 
              height: 80, 
              bgcolor: theme.palette.primary.main,
              mx: 'auto',
              mb: 3,
              boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.3)}`,
            }}>
              <CompareIcon fontSize="large" />
            </Avatar>
            
            <Typography variant="h4" fontWeight="bold" gutterBottom>
              Enable Multi-Retailer Mode
            </Typography>
            
            <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
              Price comparisons require data from multiple retailers
            </Typography>
            
            <RetailerSelector variant="full" showStats={true} showMultiMode={true} />
            
            <Alert severity="info" sx={{ mt: 3, borderRadius: 2 }}>
              <Typography variant="body1">
                <strong>Getting Started:</strong> Enable Multi-Retailer mode above and select at least 2 retailers 
                to unlock powerful cross-retailer price analysis and discover savings opportunities.
              </Typography>
            </Alert>
          </Paper>
        </motion.div>
      </Container>
    );
  }

  if (loadingDetailed) {
    return renderEnhancedLoading();
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {renderEnhancedHeader()}
      
      {/* Ultra-Strict Mode Indicator */}
      {matcherMode === 'ultra-strict' && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Alert 
            severity="warning" 
            sx={{ 
              mb: 3, 
              borderRadius: 2,
              background: `linear-gradient(135deg, ${alpha(theme.palette.error.main, 0.1)} 0%, ${alpha(theme.palette.warning.main, 0.1)} 100%)`,
              border: `1px solid ${alpha(theme.palette.error.main, 0.3)}`,
            }}
          >
            <Typography variant="body1" fontWeight="bold">
              🎯 <strong>Ultra-Strict Mode Active:</strong> Maximum accuracy matching with strict model validation. 
              False positives are eliminated but fewer matches may be found.
            </Typography>
          </Alert>
        </motion.div>
      )}
      
      {renderMatchingAnalytics()}
      {renderEnhancedStats()}
      {renderControlBar()}
      {renderEnhancedFilters()}
      
      <RetailerSelector variant="compact" showStats={false} showMultiMode={true} />
      
      {detailedError ? (
        <Alert severity="error" sx={{ mt: 3, borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom>Failed to load price comparisons</Typography>
          <Typography variant="body2">Please try refreshing the page or contact support if the issue persists.</Typography>
        </Alert>
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          {viewMode === 'analytics' ? (
            <PriceTrackingDashboard />
          ) : (
            <Box>
              {filteredComparisons.length > 0 ? (
                <Grid container spacing={3}>
                  {filteredComparisons.map((comparison: any, index: number) => (
                    <Grid item xs={12} md={viewMode === 'grid' ? 6 : 12} lg={viewMode === 'grid' ? 4 : 12} key={comparison.matchId || index}>
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.4, delay: index * 0.1 }}
                      >
                        <FunctionalPriceComparisonCard
                          productName={comparison.productName}
                          category={comparison.category}
                          brand={comparison.brand}
                          retailers={comparison.retailerPrices?.map((retailer: any) => ({
                            retailer_code: retailer.retailerCode,
                            retailer_name: retailer.retailerName,
                            price: retailer.price,
                            currency: 'THB',
                            product_url: retailer.url,
                            last_updated: retailer.lastUpdated,
                            stock_status: retailer.inStock ? 'In Stock' : 'Out of Stock',
                            discount_percentage: retailer.discount,
                            is_promotion: retailer.discount > 0,
                            shipping_cost: 0, // Default to 0 for now
                          })) || []}
                          matchDetails={{
                            match_confidence: comparison.matchConfidence,
                            match_type: comparison.matchType || 'unknown',
                            rejection_reasons: comparison.rejectionReasons || [],
                            warnings: comparison.warnings || [],
                            matched_fields: comparison.matchedFields || [],
                          }}
                        />
                      </motion.div>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Paper sx={{ p: 6, textAlign: 'center' }}>
                  <InfoIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h5" gutterBottom>No price comparisons found</Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                    Try adjusting your filters or check back later for new deals
                  </Typography>
                  <Button 
                    variant="contained" 
                    onClick={() => setMinSavingsInput(0)}
                    sx={{ borderRadius: 2 }}
                  >
                    Clear Filters
                  </Button>
                </Paper>
              )}
            </Box>
          )}
        </motion.div>
      )}
    </Container>
  );
};

export default ImprovedPriceComparisonsUI;