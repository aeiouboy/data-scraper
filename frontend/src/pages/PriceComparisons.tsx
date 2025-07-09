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
  Fade,
  Zoom,
  ToggleButton,
  ToggleButtonGroup,
  Container,
} from '@mui/material';
import {
  TrendingDown as SavingsIcon,
  Store as StoreIcon,
  CompareArrows as CompareIcon,
  LocalOffer as OfferIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  ViewModule as GridViewIcon,
  ViewList as ListViewIcon,
  Analytics as AnalyticsIcon,
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
  const { selectedRetailers, multiRetailerMode } = useRetailer();
  const [categoryFilter, setCategoryFilter] = useState('');
  const [minSavings, setMinSavings] = useState(100);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'analytics'>('grid');
  const [currentPage, setCurrentPage] = useState(0);
  const [minSavingsInput, setMinSavingsInput] = useState(100);
  const itemsPerPage = 12;
  
  // Debounced update for minSavings
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setMinSavings(minSavingsInput);
      setCurrentPage(0);
    }, 500);
    
    return () => clearTimeout(timer);
  }, [minSavingsInput]);

  // Fetch detailed price comparisons (new V2 API)
  const { data: detailedData, isLoading: loadingDetailed, refetch: refetchDetailed } = useQuery({
    queryKey: ['price-comparisons-v2', 'detailed', minSavings, categoryFilter, currentPage],
    queryFn: async () => {
      try {
        const response = await priceComparisonApi.getDetailedComparisons({
          limit: viewMode === 'grid' ? itemsPerPage : 50,
          offset: viewMode === 'grid' ? currentPage * itemsPerPage : 0,
          minSavings: minSavings,
          category: categoryFilter || undefined,
        });
        return response.data;
      } catch (error) {
        console.error('Error fetching detailed comparisons:', error);
        return { comparisons: [], total: 0 };
      }
    },
    enabled: multiRetailerMode && selectedRetailers.length > 1,
    staleTime: 60000, // Cache for 1 minute
    cacheTime: 300000, // Keep in cache for 5 minutes
    keepPreviousData: true, // Keep previous data while fetching new page
  });

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
    enabled: multiRetailerMode && selectedRetailers.length > 1 && viewMode === 'list',
  });

  // Fetch retailer competitiveness
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
    enabled: multiRetailerMode && selectedRetailers.length > 1,
  });

  // Refresh all matches
  const handleRefreshMatches = async () => {
    try {
      await priceComparisonApi.refreshMatches();
      refetchDetailed();
      refetchSavings();
    } catch (error) {
      console.error('Failed to refresh matches:', error);
    }
  };

  // Filter savings data for table view
  const filteredSavings = savingsData?.filter((item: SavingsOpportunity) => {
    const meetsMinSavings = item.savings_amount >= minSavings;
    const meetsCategory = !categoryFilter || item.category === categoryFilter;
    return meetsMinSavings && meetsCategory;
  }) || [];
  
  // Get comparisons from detailed data with memoization
  const comparisons = useMemo(() => detailedData?.comparisons || [], [detailedData]);
  
  // Calculate summary statistics with memoization
  const { totalSavings, avgVariance } = useMemo(() => {
    const total = comparisons.reduce((sum: number, item: any) => 
      sum + (item.priceAnalysis?.savingsAmount || 0), 0
    );
    const avg = comparisons.length > 0 
      ? comparisons.reduce((sum: number, item: any) => 
          sum + (item.priceAnalysis?.savingsPercentage || 0), 0) / comparisons.length 
      : 0;
    return { totalSavings: total, avgVariance: avg };
  }, [comparisons]);

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

  // Single retailer mode message
  if (!multiRetailerMode || selectedRetailers.length < 2) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Price Comparisons
        </Typography>
        
        <RetailerSelector variant="full" showStats={true} showMultiMode={true} />

        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="h6" gutterBottom>
            Enable Multi-Retailer Mode
          </Typography>
          <Typography>
            Price comparisons require data from multiple retailers. Please enable Multi-Retailer mode 
            above and select at least 2 retailers to view cross-retailer price analysis and savings opportunities.
          </Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Price Comparisons
        </Typography>
        
        <Stack direction="row" spacing={2}>
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => newMode && setViewMode(newMode)}
            size="small"
          >
            <ToggleButton value="grid">
              <GridViewIcon sx={{ mr: 1 }} />
              Cards
            </ToggleButton>
            <ToggleButton value="list">
              <ListViewIcon sx={{ mr: 1 }} />
              Table
            </ToggleButton>
            <ToggleButton value="analytics">
              <AnalyticsIcon sx={{ mr: 1 }} />
              Analytics
            </ToggleButton>
          </ToggleButtonGroup>
          
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefreshMatches}
            disabled={loadingSavings}
          >
            Refresh
          </Button>
        </Stack>
      </Stack>

      <RetailerSelector variant="full" showStats={true} showMultiMode={true} />

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
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
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <CompareIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {comparisons.length.toLocaleString()}
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
          <Card>
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
          <Card>
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

      {/* Filters */}
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
                      />
                    </Box>
                  </Grid>
                ))}
              </Grid>
              
              {(detailedData?.total || 0) > itemsPerPage && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                  <Button
                    disabled={currentPage === 0}
                    onClick={() => setCurrentPage(currentPage - 1)}
                    sx={{ mr: 2 }}
                  >
                    Previous
                  </Button>
                  <Typography sx={{ mx: 2, display: 'flex', alignItems: 'center' }}>
                    Page {currentPage + 1} of {Math.ceil((detailedData?.total || 0) / itemsPerPage)}
                  </Typography>
                  <Button
                    disabled={currentPage >= Math.ceil((detailedData?.total || 0) / itemsPerPage) - 1}
                    onClick={() => setCurrentPage(currentPage + 1)}
                    sx={{ ml: 2 }}
                  >
                    Next
                  </Button>
                </Box>
              )}
              
              {comparisons.length === 0 && (
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <Typography variant="h6" color="text.secondary">
                    No price comparisons found
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Try adjusting your filters or refresh the data
                  </Typography>
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