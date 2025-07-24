import React, { useState, useMemo } from 'react';
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
  Fade,
  Zoom,
} from '@mui/material';
import {
  TrendingDown as SavingsIcon,
  Store as StoreIcon,
  CompareArrows as CompareIcon,
  LocalOffer as OfferIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { priceComparisonApi } from '../services/api';
import { useRetailer } from '../contexts/RetailerContext';
import RetailerSelector from '../components/RetailerSelector';
import PriceTrackingDashboard from '../components/PriceTrackingDashboard';
import PriceComparisonCard from '../components/PriceComparisonCard';

const retailerColors: Record<string, string> = {
  'HP': '#FF6B35',   // HomePro Orange
  'TWD': '#1976D2',  // Thai Watsadu Blue
  'GH': '#4CAF50',   // Global House Green
  'DH': '#FF9800',   // DoHome Orange
  'BT': '#9C27B0',   // Boonthavorn Purple
  'MH': '#607D8B',   // MegaHome Blue Grey
};

interface SavingsOpportunity {
  product_name: string;
  category: string;
  savings_amount: number;
  price_range: string;
  best_retailer: string;
  variance_percentage: number;
}

interface RetailerCompetitiveness {
  [category: string]: {
    [retailer: string]: {
      best_price_count: number;
      total_products: number;
      competitiveness_score: number;
    };
  };
}

export default function PriceComparisons() {
  const { selectedRetailers } = useRetailer();
  const [categoryFilter, setCategoryFilter] = useState('');
  const [minSavings, setMinSavings] = useState(100);
  const [viewMode] = useState<'grid' | 'list' | 'analytics'>('grid');
  const [currentPage, setCurrentPage] = useState(0);
  const [minSavingsInput, setMinSavingsInput] = useState(100);
  const [showFilters, setShowFilters] = useState(false);
  const [matcherMode] = useState<'standard' | 'ultra-strict'>('standard');
  const itemsPerPage = 12;
  
  // Debounced update for minSavings with pagination reset
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setMinSavings(minSavingsInput);
      setCurrentPage(0); // Reset to first page when filter changes
    }, 500);
    
    return () => clearTimeout(timer);
  }, [minSavingsInput]);

  // Reset pagination when filters change
  React.useEffect(() => {
    setCurrentPage(0);
  }, [categoryFilter, matcherMode, viewMode]);

  // Fetch detailed price comparisons with proper pagination
  const { data: detailedData, isLoading: loadingDetailed, refetch: refetchDetailed, error: detailedError } = useQuery({
    queryKey: ['price-comparisons-optimized', minSavings, categoryFilter, currentPage, matcherMode, viewMode],
    queryFn: async () => {
      try {
        const limit = viewMode === 'grid' ? itemsPerPage : 50;
        const offset = currentPage * limit;
        
        console.log(`Fetching page ${currentPage + 1} with limit=${limit}, offset=${offset}`);
        
        const response = await priceComparisonApi.getDetailedComparisonsOptimized({
          limit,
          offset,
          minSavings: minSavings,
          category: categoryFilter || undefined,
        });
        
        if (!response.data) {
          throw new Error('No data received from API');
        }
        
        console.log(`Received ${response.data.comparisons?.length || 0} items, total: ${response.data.total}`);
        return response.data;
      } catch (error) {
        console.error('Error fetching detailed comparisons:', error);
        throw error; // Re-throw to let React Query handle the error
      }
    },
    enabled: true, // Always enabled to show price comparisons
    staleTime: 30000, // Cache for 30 seconds (shorter for better pagination UX)
    cacheTime: 300000, // Keep in cache for 5 minutes
    keepPreviousData: true, // Keep previous data while fetching new page
    retry: 2, // Retry failed requests
  });

  // Keyboard navigation for pagination
  React.useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.target !== document.body) return; // Only work when not in input fields
      
      const totalPages = Math.ceil((detailedData?.total || 0) / itemsPerPage);
      
      if (event.key === 'ArrowLeft' && currentPage > 0) {
        event.preventDefault();
        setCurrentPage(currentPage - 1);
      } else if (event.key === 'ArrowRight' && currentPage < totalPages - 1) {
        event.preventDefault();
        setCurrentPage(currentPage + 1);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentPage, detailedData?.total, itemsPerPage]);

  // Fetch top savings opportunities (legacy API for table view)
  const { data: savingsData, isLoading: loadingSavings, refetch: refetchSavings } = useQuery({
    queryKey: ['price-comparisons', 'top-savings', minSavings],
    queryFn: async () => {
      try {
        const response = await priceComparisonApi.getTopSavings(50);
        return response.data?.savings_opportunities || [];
      } catch (error) {
        console.error('Error fetching savings data:', error);
        return [];
      }
    },
    enabled: viewMode === 'list',
  });

  // Fetch retailer competitiveness (only when analytics view is active)
  const { data: competitivenessData, isLoading: loadingCompetitiveness } = useQuery({
    queryKey: ['price-comparisons', 'competitiveness'],
    queryFn: async () => {
      try {
        const response = await priceComparisonApi.getRetailerCompetitiveness();
        return response.data || {};
      } catch (error) {
        console.error('Error fetching competitiveness data:', error);
        return {};
      }
    },
    enabled: viewMode === 'analytics',
    staleTime: 300000, // Cache for 5 minutes
  });


  // Filter savings data for table view
  const filteredSavings = savingsData?.filter((item: SavingsOpportunity) => {
    const meetsMinSavings = item.savings_amount >= minSavings;
    const meetsCategory = !categoryFilter || item.category === categoryFilter;
    return meetsMinSavings && meetsCategory;
  }) || [];
  
  // Get comparisons from detailed data with memoization
  const comparisons = useMemo(() => detailedData?.comparisons || [], [detailedData]);
  
  // Fetch quick stats from API
  const { data: quickStats } = useQuery({
    queryKey: ['price-comparisons-quick-stats', categoryFilter],
    queryFn: async () => {
      try {
        const response = await priceComparisonApi.getQuickStats(categoryFilter || undefined);
        return response.data;
      } catch (error) {
        console.error('Error fetching quick stats:', error);
        return {
          totalSavingsAvailable: 0,
          productsWithSavings: 0,
          avgPriceVariance: 0,
          lastUpdated: new Date().toISOString()
        };
      }
    },
    enabled: true, // Always enabled to show price comparisons
    staleTime: 60000, // Cache for 1 minute
  });

  // Extract values with fallback calculations
  const totalSavings = quickStats?.totalSavingsAvailable || 
    comparisons.reduce((sum: number, item: any) => sum + (item.priceAnalysis?.savingsAmount || 0), 0);
  const avgVariance = quickStats?.avgPriceVariance || 
    (comparisons.length > 0 
      ? comparisons.reduce((sum: number, item: any) => sum + (item.priceAnalysis?.savingsPercentage || 0), 0) / comparisons.length 
      : 0);
  const productsWithSavings = quickStats?.productsWithSavings || comparisons.length;
  
  // Calculate TWD Market Leadership (percentage of products where TWD has best price)

  const savingsColumns: GridColDef[] = [
    {
      field: 'product_name',
      headerName: 'Product',
      width: 300,
      flex: 1,
    },
    {
      field: 'category',
      headerName: 'Category',
      width: 150,
      renderCell: (params: GridRenderCellParams) => (
        <Chip label={params.value} size="small" variant="outlined" />
      ),
    },
    {
      field: 'savings_amount',
      headerName: 'Max Savings',
      width: 130,
      renderCell: (params: GridRenderCellParams) => (
        <Typography
          variant="body2"
          sx={{
            color: 'success.main',
            fontWeight: 'bold',
          }}
        >
          ฿{params.value?.toFixed(2) || '0.00'}
        </Typography>
      ),
    },
    {
      field: 'price_range',
      headerName: 'Price Range',
      width: 180,
    },
    {
      field: 'best_retailer',
      headerName: 'Best Price',
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Chip
          label={params.value}
          size="small"
          data-testid="retailer-chip"
          sx={{
            bgcolor: `${retailerColors[params.value] || '#666'}15`,
            color: retailerColors[params.value] || '#666',
            fontWeight: 'bold',
          }}
        />
      ),
    },
    {
      field: 'variance_percentage',
      headerName: 'Price Variance',
      width: 130,
      renderCell: (params: GridRenderCellParams) => (
        <Typography
          variant="body2"
          sx={{
            color: params.value > 20 ? 'error.main' : 'warning.main',
            fontWeight: 'bold',
          }}
        >
          {params.value?.toFixed(1) || '0.0'}%
        </Typography>
      ),
    },
  ];


  return (
    <Box>
      <Typography variant="h4" sx={{
        background: 'linear-gradient(45deg, #FF6B35 30%, #F7931E 90%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
        flexShrink: 0,
        mb: 2
      }}>
        💰 Smart Price Comparisons
      </Typography>
      
      <div style={{display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px'}}>
        <div style={{padding: '8px', background: 'blue', color: 'white'}}>TEST 1</div>
        <div style={{padding: '8px', background: 'green', color: 'white'}}>TEST 2</div>
        <div style={{padding: '8px', background: 'red', color: 'white'}}>TEST 3</div>
      </div>

      <RetailerSelector variant="full" showStats={true} showMultiMode={true} />

      {/* Ultra-Strict Mode Indicator */}
      {matcherMode === 'ultra-strict' && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            🎯 <strong>Ultra-Strict Mode Active:</strong> Maximum accuracy matching with strict model validation. 
            False positives are eliminated but fewer matches may be found.
          </Typography>
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card data-testid="stats-card">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <SavingsIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    ฿{totalSavings.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Savings Available
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card data-testid="stats-card">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <CompareIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {productsWithSavings.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Products with Savings
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card data-testid="stats-card">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'warning.main' }}>
                  <OfferIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {avgVariance.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg Price Variance
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card data-testid="stats-card">
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <StoreIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {selectedRetailers.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Retailers Compared
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filter Toggle */}
      <Box sx={{ mb: 2 }}>
        <Button
          variant="outlined"
          startIcon={<FilterIcon />}
          onClick={() => setShowFilters(!showFilters)}
          size="small"
        >
          Show Filters
        </Button>
      </Box>

      {/* Filters */}
      {showFilters && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Stack direction="row" spacing={2} alignItems="center">
            <FilterIcon color="action" />
            <TextField
              label="Minimum Savings (฿)"
              type="number"
              value={minSavingsInput}
              onChange={(e) => setMinSavingsInput(Number(e.target.value))}
              size="small"
              sx={{ width: 200 }}
            />
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                onChange={(e) => {
                  setCategoryFilter(e.target.value);
                  setCurrentPage(0);
                }}
                label="Category"
              >
                <MenuItem value="">All Categories</MenuItem>
                {Array.from(new Set(savingsData?.map((item: SavingsOpportunity) => item.category) || [])).map((category) => (
                  <MenuItem key={String(category)} value={String(category)}>
                    {String(category)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </Paper>
      )}

      {/* View Mode Content */}
      {viewMode === 'analytics' ? (
        <Paper sx={{ mb: 3, p: 2 }}>
          <PriceTrackingDashboard />
        </Paper>
      ) : (
        <Paper sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            💰 Top Savings Opportunities
          </Typography>
          
          {loadingDetailed || loadingSavings ? (
            viewMode === 'grid' ? (
              <Box sx={{ p: 2 }}>
                <Grid container spacing={2}>
                  {[...Array(6)].map((_, index) => (
                    <Grid item xs={12} md={6} lg={4} key={index}>
                      <Skeleton variant="rectangular" height={350} sx={{ borderRadius: 1 }} />
                    </Grid>
                  ))}
                </Grid>
              </Box>
            ) : (
              <Box sx={{ p: 3 }}>
                {[...Array(5)].map((_, index) => (
                  <Skeleton key={index} height={60} sx={{ mb: 1 }} />
                ))}
              </Box>
            )
          ) : viewMode === 'grid' ? (
            <Box sx={{ p: 2 }}>
              <Grid container spacing={2}>
                {comparisons.map((comparison: any, index: number) => (
                  <Grid item xs={12} md={6} lg={4} key={comparison.matchId || `comp-${index}`}>
                    <Box sx={{ height: '100%' }}>
                      <PriceComparisonCard
                        productName={comparison.productName}
                        category={comparison.category}
                        brand={comparison.brand}
                        retailers={comparison.retailerPrices}
                        bestRetailerCode={comparison.priceAnalysis?.bestRetailer}
                        savingsAmount={comparison.priceAnalysis?.savingsAmount || 0}
                        savingsPercentage={comparison.priceAnalysis?.savingsPercentage || 0}
                        matchConfidence={comparison.matchConfidence}
                        matcherMode={matcherMode}
                      />
                    </Box>
                  </Grid>
                ))}
              </Grid>
              
              {(detailedData?.total || 0) > itemsPerPage && (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mt: 3 }}>
                  <Button
                    variant="outlined"
                    disabled={currentPage === 0 || loadingDetailed}
                    onClick={() => setCurrentPage(currentPage - 1)}
                    sx={{ mr: 2, minWidth: 100 }}
                  >
                    Previous
                  </Button>
                  <Box sx={{ 
                    mx: 2, 
                    display: 'flex', 
                    alignItems: 'center',
                    minWidth: 150,
                    justifyContent: 'center'
                  }}>
                    {loadingDetailed ? (
                      <Typography variant="body2" color="text.secondary">
                        Loading...
                      </Typography>
                    ) : detailedError ? (
                      <Typography variant="body2" color="error">
                        Error loading
                      </Typography>
                    ) : (
                      <Typography>
                        Page {currentPage + 1} of {Math.ceil((detailedData?.total || 0) / itemsPerPage)}
                      </Typography>
                    )}
                  </Box>
                  <Button
                    variant="outlined"
                    disabled={currentPage >= Math.ceil((detailedData?.total || 0) / itemsPerPage) - 1 || loadingDetailed}
                    onClick={() => setCurrentPage(currentPage + 1)}
                    sx={{ ml: 2, minWidth: 100 }}
                  >
                    Next
                  </Button>
                </Box>
              )}
              
              {comparisons.length === 0 && !loadingDetailed && (
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  {detailedError ? (
                    <>
                      <Typography variant="h6" color="error">
                        Error loading price comparisons
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {(detailedError as any)?.message || 'Please check your connection and try again'}
                      </Typography>
                      <Button 
                        onClick={() => refetchDetailed()} 
                        variant="outlined" 
                        sx={{ mt: 2 }}
                      >
                        Retry
                      </Button>
                    </>
                  ) : (
                    <>
                      <Typography variant="h6" color="text.secondary">
                        No price comparisons found
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        Try adjusting your filters or refresh the data
                      </Typography>
                    </>
                  )}
                </Box>
              )}
            </Box>
          ) : (
            <DataGrid
              rows={filteredSavings.map((item: SavingsOpportunity, index: number) => ({ id: index, ...item }))}
              columns={savingsColumns}
              pagination
              pageSizeOptions={[25, 50, 100]}
              initialState={{
                pagination: { paginationModel: { pageSize: 25 } },
              }}
              sx={{
                height: 600,
                border: 0,
                '& .MuiDataGrid-cell:focus': {
                  outline: 'none',
                },
              }}
            />
          )}
        </Paper>
      )}

      {/* Retailer Competitiveness Analysis */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          🏆 Retailer Competitiveness by Category
        </Typography>
        
        {loadingCompetitiveness ? (
          <Box>
            {[...Array(3)].map((_, index) => (
              <Skeleton key={index} height={100} sx={{ mb: 2 }} />
            ))}
          </Box>
        ) : competitivenessData ? (
          <Grid container spacing={2}>
            {Object.entries(competitivenessData as RetailerCompetitiveness).map(([category, retailers]) => (
              <Grid item xs={12} md={6} lg={4} key={category}>
                <Fade in timeout={300}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                        {category}
                      </Typography>
                      
                      <Stack spacing={1}>
                        {Object.entries(retailers)
                          .sort(([,a], [,b]) => (b as any).competitiveness_score - (a as any).competitiveness_score)
                          .map(([retailerCode, data], index) => (
                            <Zoom in timeout={300 + index * 100} key={retailerCode}>
                              <Box
                                sx={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                  p: 1,
                                  borderRadius: 1,
                                  bgcolor: index === 0 ? 'success.50' : 'transparent',
                                  border: index === 0 ? 1 : 0,
                                  borderColor: 'success.200',
                                }}
                              >
                                <Stack direction="row" alignItems="center" spacing={1}>
                                  <Avatar
                                    sx={{
                                      width: 24,
                                      height: 24,
                                      bgcolor: retailerColors[retailerCode] || '#666',
                                      fontSize: 12,
                                    }}
                                  >
                                    {retailerCode}
                                  </Avatar>
                                  <Typography variant="body2">
                                    {retailerCode}
                                  </Typography>
                                  {index === 0 && (
                                    <Chip label="Best" color="success" size="small" />
                                  )}
                                </Stack>
                                
                                <Typography
                                  variant="body2"
                                  fontWeight="bold"
                                  color={index === 0 ? 'success.main' : 'text.secondary'}
                                >
                                  {(data as any).competitiveness_score?.toFixed(1) || '0.0'}%
                                </Typography>
                              </Box>
                            </Zoom>
                          ))}
                      </Stack>
                    </CardContent>
                  </Card>
                </Fade>
              </Grid>
            ))}
          </Grid>
        ) : (
          <Alert severity="info">
            No competitiveness data available. Please ensure product matching has been completed.
          </Alert>
        )}
      </Paper>
    </Box>
  );
}