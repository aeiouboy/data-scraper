import React, { useState, useMemo, useCallback, memo } from 'react';
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
  CircularProgress,
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
import PriceComparisonFilters from '../components/PriceComparisonFilters';
import useDebounce from '../hooks/useDebounce';

const retailerColors: Record<string, string> = {
  'HP': '#FF6B35',
  'TWD': '#1976D2',
  'GH': '#4CAF50',
  'DH': '#FF9800',
  'BT': '#9C27B0',
  'MH': '#607D8B',
};

// Memoized summary card component
const SummaryCard = memo(({ icon: Icon, value, label, color }: any) => (
  <Card>
    <CardContent>
      <Stack direction="row" alignItems="center" spacing={2}>
        <Avatar sx={{ bgcolor: `${color}.main` }}>
          <Icon />
        </Avatar>
        <Box>
          <Typography variant="h6">
            {value}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {label}
          </Typography>
        </Box>
      </Stack>
    </CardContent>
  </Card>
));

export default function PriceComparisonsOptimized() {
  const { selectedRetailers, multiRetailerMode } = useRetailer();
  const [categoryFilter, setCategoryFilter] = useState('');
  const [minSavingsInput, setMinSavingsInput] = useState(100);
  const [minSavingsPercent, setMinSavingsPercent] = useState(0);
  const [minConfidence, setMinConfidence] = useState(0.5);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'analytics'>('grid');
  const [currentPage, setCurrentPage] = useState(0);
  const itemsPerPage = 12;
  
  // Debounce the filter values
  const debouncedMinSavings = useDebounce(minSavingsInput, 500);
  const debouncedMinSavingsPercent = useDebounce(minSavingsPercent, 500);
  const debouncedMinConfidence = useDebounce(minConfidence, 500);

  // Fetch quick stats separately for better performance
  const { data: quickStats, refetch: refetchStats } = useQuery({
    queryKey: ['price-comparisons-stats', categoryFilter],
    queryFn: async () => {
      try {
        const response = await priceComparisonApi.getQuickStats(categoryFilter);
        return response.data;
      } catch (error) {
        console.error('Error fetching stats:', error);
        return {
          totalSavingsAvailable: 0,
          productsWithSavings: 0,
          avgPriceVariance: 0,
        };
      }
    },
    enabled: multiRetailerMode && selectedRetailers.length > 1,
    staleTime: 300000, // 5 minutes
    cacheTime: 600000, // 10 minutes
  });

  // Fetch categories list once with longer cache
  const { data: categoriesData } = useQuery({
    queryKey: ['categories-summary'],
    queryFn: async () => {
      try {
        const response = await priceComparisonApi.getCategoriesWithSavings();
        // Transform backend data structure to match frontend expectations
        const categories = response.data || [];
        return categories.map((cat: any) => ({
          category: cat.category,
          productCount: cat.totalProducts || 0
        }));
      } catch (error) {
        console.error('Error fetching categories:', error);
        return [];
      }
    },
    enabled: multiRetailerMode && selectedRetailers.length > 1,
    staleTime: 600000, // 10 minutes
    cacheTime: 1800000, // 30 minutes
  });

  // Optimized detailed comparisons with server-side pagination
  const { data: detailedData, isLoading: loadingDetailed, refetch: refetchDetailed } = useQuery({
    queryKey: ['price-comparisons-optimized', debouncedMinSavings, debouncedMinSavingsPercent, debouncedMinConfidence, categoryFilter, currentPage, viewMode],
    queryFn: async () => {
      try {
        // Use existing v2 endpoint with percentage filtering
        const response = await priceComparisonApi.getDetailedComparisons({
          limit: viewMode === 'grid' ? itemsPerPage : 50,
          offset: viewMode === 'grid' ? currentPage * itemsPerPage : 0,
          minSavings: debouncedMinSavings,
          minSavingsPercent: debouncedMinSavingsPercent,
          minConfidence: debouncedMinConfidence,
          category: categoryFilter || undefined,
        });
        
        return response.data;
      } catch (error) {
        console.error('Error fetching detailed comparisons:', error);
        return { comparisons: [], total: 0, totalPages: 0 };
      }
    },
    enabled: multiRetailerMode && selectedRetailers.length > 1 && viewMode !== 'analytics',
    staleTime: 60000, // 1 minute
    cacheTime: 300000, // 5 minutes
    keepPreviousData: true,
  });

  // Handle page change
  const handlePageChange = useCallback((newPage: number) => {
    setCurrentPage(newPage);
  }, []);

  // Handle category change
  const handleCategoryChange = useCallback((event: any) => {
    setCategoryFilter(event.target.value);
    setCurrentPage(0);
  }, []);

  // Handle refresh all
  const handleRefreshAll = useCallback(async () => {
    await Promise.all([
      refetchDetailed(),
      refetchStats(),
    ]);
  }, [refetchDetailed, refetchStats]);

  // Handle clear filters
  const handleClearFilters = useCallback(() => {
    setCategoryFilter('');
    setMinSavingsInput(0);
    setMinSavingsPercent(0);
    setMinConfidence(0.5);
    setCurrentPage(0);
  }, []);

  // Memoized table columns
  const savingsColumns: GridColDef[] = useMemo(() => [
    {
      field: 'productName',
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
      field: 'savingsAmount',
      headerName: 'Max Savings',
      width: 130,
      valueGetter: (params) => params.row.priceAnalysis?.savingsAmount || 0,
      renderCell: (params: GridRenderCellParams) => (
        <Typography
          variant="body2"
          sx={{ color: 'success.main', fontWeight: 'bold' }}
        >
          ฿{params.value?.toFixed(2) || '0.00'}
        </Typography>
      ),
    },
    {
      field: 'priceRange',
      headerName: 'Price Range',
      width: 180,
      valueGetter: (params) => params.row.priceAnalysis?.priceRange || '',
    },
    {
      field: 'bestRetailer',
      headerName: 'Best Price',
      width: 120,
      valueGetter: (params) => params.row.priceAnalysis?.bestRetailer || '',
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
      field: 'savingsPercentage',
      headerName: 'Price Variance',
      width: 130,
      valueGetter: (params) => params.row.priceAnalysis?.savingsPercentage || 0,
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
  ], []);

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

  const comparisons = detailedData?.comparisons || [];
  const totalPages = detailedData?.totalPages || 0;

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
            onClick={handleRefreshAll}
            disabled={loadingDetailed}
          >
            Refresh
          </Button>
        </Stack>
      </Stack>

      <RetailerSelector variant="full" showStats={true} showMultiMode={true} />

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <SummaryCard
            icon={SavingsIcon}
            value={`฿${(quickStats?.totalSavingsAvailable || 0).toLocaleString()}`}
            label="Total Savings Available"
            color="success"
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <SummaryCard
            icon={CompareIcon}
            value={(quickStats?.productsWithSavings || 0).toLocaleString()}
            label="Products with Savings"
            color="primary"
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <SummaryCard
            icon={OfferIcon}
            value={`${(quickStats?.avgPriceVariance || 0).toFixed(1)}%`}
            label="Avg Price Variance"
            color="warning"
          />
        </Grid>

        <Grid item xs={12} md={3}>
          <SummaryCard
            icon={StoreIcon}
            value={selectedRetailers.length}
            label="Retailers Compared"
            color="info"
          />
        </Grid>
      </Grid>

      {/* Enhanced Filters */}
      <PriceComparisonFilters
        minSavings={minSavingsInput}
        minSavingsPercent={minSavingsPercent}
        minConfidence={minConfidence}
        category={categoryFilter}
        categories={categoriesData || []}
        onMinSavingsChange={setMinSavingsInput}
        onMinSavingsPercentChange={setMinSavingsPercent}
        onMinConfidenceChange={setMinConfidence}
        onCategoryChange={(cat) => {
          setCategoryFilter(cat);
          setCurrentPage(0);
        }}
        onClearFilters={handleClearFilters}
      />

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
          
          {loadingDetailed ? (
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
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <CircularProgress />
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
              
              {totalPages > 1 && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                  <Button
                    disabled={currentPage === 0}
                    onClick={() => handlePageChange(currentPage - 1)}
                    sx={{ mr: 2 }}
                  >
                    Previous
                  </Button>
                  <Typography sx={{ mx: 2, display: 'flex', alignItems: 'center' }}>
                    Page {currentPage + 1} of {totalPages}
                  </Typography>
                  <Button
                    disabled={currentPage >= totalPages - 1}
                    onClick={() => handlePageChange(currentPage + 1)}
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
              rows={comparisons.map((item: any, index: number) => ({ id: index, ...item }))}
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
              loading={loadingDetailed}
            />
          )}
        </Paper>
      )}
    </Box>
  );
}