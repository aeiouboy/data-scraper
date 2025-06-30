import React, { useState } from 'react';
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
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { priceComparisonApi } from '../services/api';
import { useRetailer } from '../contexts/RetailerContext';
import RetailerSelector from '../components/RetailerSelector';

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

  // Fetch top savings opportunities
  const { data: savingsData, isLoading: loadingSavings, refetch: refetchSavings } = useQuery({
    queryKey: ['price-comparisons', 'top-savings', minSavings],
    queryFn: async () => {
      const response = await priceComparisonApi.getTopSavings(50);
      return response.data.savings_opportunities as SavingsOpportunity[];
    },
    enabled: multiRetailerMode && selectedRetailers.length > 1,
  });

  // Fetch retailer competitiveness
  const { data: competitivenessData, isLoading: loadingCompetitiveness } = useQuery({
    queryKey: ['price-comparisons', 'competitiveness'],
    queryFn: async () => {
      const response = await priceComparisonApi.getRetailerCompetitiveness();
      return response.data as RetailerCompetitiveness;
    },
    enabled: multiRetailerMode && selectedRetailers.length > 1,
  });

  // Refresh all matches
  const handleRefreshMatches = async () => {
    try {
      await priceComparisonApi.refreshMatches();
      refetchSavings();
    } catch (error) {
      console.error('Failed to refresh matches:', error);
    }
  };

  // Filter savings data
  const filteredSavings = savingsData?.filter(item => {
    const meetsMinSavings = item.savings_amount >= minSavings;
    const meetsCategory = !categoryFilter || item.category === categoryFilter;
    return meetsMinSavings && meetsCategory;
  }) || [];

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
      renderCell: (params) => (
        <Chip label={params.value} size="small" variant="outlined" />
      ),
    },
    {
      field: 'savings_amount',
      headerName: 'Max Savings',
      width: 130,
      renderCell: (params) => (
        <Typography
          variant="body2"
          sx={{
            color: 'success.main',
            fontWeight: 'bold',
          }}
        >
          ฿{params.value.toFixed(2)}
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
      renderCell: (params) => (
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
      renderCell: (params) => (
        <Typography
          variant="body2"
          sx={{
            color: params.value > 20 ? 'error.main' : 'warning.main',
            fontWeight: 'bold',
          }}
        >
          {params.value.toFixed(1)}%
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
        
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefreshMatches}
          disabled={loadingSavings}
        >
          Refresh Matches
        </Button>
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
                    ฿{filteredSavings.reduce((sum, item) => sum + item.savings_amount, 0).toLocaleString()}
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
                    {filteredSavings.length.toLocaleString()}
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
                    {filteredSavings.length > 0 ? 
                      Math.max(...filteredSavings.map(item => item.variance_percentage)).toFixed(1) : 0}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Max Price Variance
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
            value={minSavings}
            onChange={(e) => setMinSavings(Number(e.target.value))}
            size="small"
            sx={{ width: 200 }}
          />
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              label="Category"
            >
              <MenuItem value="">All Categories</MenuItem>
              {Array.from(new Set(savingsData?.map(item => item.category) || [])).map(category => (
                <MenuItem key={category} value={category}>
                  {category}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </Paper>

      {/* Savings Opportunities Table */}
      <Paper sx={{ height: 600, mb: 3 }}>
        <Typography variant="h6" sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          💰 Top Savings Opportunities
        </Typography>
        
        {loadingSavings ? (
          <Box sx={{ p: 3 }}>
            {[...Array(5)].map((_, index) => (
              <Skeleton key={index} height={60} sx={{ mb: 1 }} />
            ))}
          </Box>
        ) : (
          <DataGrid
            rows={filteredSavings.map((item, index) => ({ id: index, ...item }))}
            columns={savingsColumns}
            pagination
            pageSizeOptions={[25, 50, 100]}
            initialState={{
              pagination: { paginationModel: { pageSize: 25 } },
            }}
            sx={{
              border: 0,
              '& .MuiDataGrid-cell:focus': {
                outline: 'none',
              },
            }}
          />
        )}
      </Paper>

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
            {Object.entries(competitivenessData).map(([category, retailers]) => (
              <Grid item xs={12} md={6} lg={4} key={category}>
                <Fade in timeout={300}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                        {category}
                      </Typography>
                      
                      <Stack spacing={1}>
                        {Object.entries(retailers)
                          .sort(([,a], [,b]) => b.competitiveness_score - a.competitiveness_score)
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
                                  {data.competitiveness_score.toFixed(1)}%
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