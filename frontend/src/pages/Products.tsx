import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Typography,
  Grid,
  Slider,
  FormControlLabel,
  Checkbox,
  Alert,
  Snackbar,
  Tooltip,
  Avatar,
  Stack,
} from '@mui/material';
import { DataGrid, GridColDef, GridPaginationModel, GridSortModel } from '@mui/x-data-grid';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { productApi } from '../services/api';
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

export default function Products() {
  const queryClient = useQueryClient();
  const { selectedRetailer, multiRetailerMode, selectedRetailers } = useRetailer();
  const [searchParams, setSearchParams] = useState({
    query: '',
    brands: [] as string[],
    categories: [] as string[],
    min_price: 0,
    max_price: 10000,
    on_sale_only: false,
    in_stock_only: false,
    sort_by: 'name',
    sort_order: 'asc',
    page: 1,
    page_size: 20,
  });
  
  const [showFilters, setShowFilters] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  // Fetch brands and categories for filters
  const { data: brandsData } = useQuery({
    queryKey: ['brands', multiRetailerMode ? 'multi' : selectedRetailer],
    queryFn: async () => {
      const retailerCode = multiRetailerMode ? undefined : selectedRetailer || undefined;
      const response = await productApi.getBrands(retailerCode);
      return response.data.brands;
    },
  });

  const { data: categoriesData } = useQuery({
    queryKey: ['categories', multiRetailerMode ? 'multi' : selectedRetailer],
    queryFn: async () => {
      const retailerCode = multiRetailerMode ? undefined : selectedRetailer || undefined;
      const response = await productApi.getCategories(retailerCode);
      return response.data.categories;
    },
  });

  // Search products
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['products', searchParams, multiRetailerMode ? selectedRetailers : selectedRetailer],
    queryFn: async () => {
      const searchParamsWithRetailer = {
        ...searchParams,
        ...(multiRetailerMode ? 
          { retailer_codes: selectedRetailers } : 
          selectedRetailer ? { retailer_code: selectedRetailer } : {}
        )
      };
      const response = await productApi.search(searchParamsWithRetailer);
      return response.data;
    },
  });

  // Rescrape mutation
  const rescrapeMutation = useMutation({
    mutationFn: (productId: string) => productApi.rescrape(productId),
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Rescrape triggered successfully', severity: 'success' });
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to trigger rescrape', severity: 'error' });
    },
  });

  const columns: GridColDef[] = [
    { field: 'sku', headerName: 'SKU', width: 120 },
    { field: 'name', headerName: 'Product Name', width: 300, flex: 1 },
    { field: 'brand', headerName: 'Brand', width: 120 },
    ...(multiRetailerMode ? [
      {
        field: 'retailer_code',
        headerName: 'Retailer',
        width: 100,
        renderCell: (params: any) => (
          <Stack direction="row" alignItems="center" spacing={1}>
            <Avatar
              sx={{
                bgcolor: retailerColors[params.value] || '#666',
                width: 24,
                height: 24,
                fontSize: 12,
              }}
            >
              {params.value}
            </Avatar>
            <Typography variant="caption">{params.value}</Typography>
          </Stack>
        ),
      } as GridColDef
    ] : []),
    { 
      field: 'category', 
      headerName: 'Category', 
      width: 180,
      renderCell: (params) => {
        const category = params.value;
        if (!category) return <Typography variant="body2" color="text.disabled">-</Typography>;
        
        return (
          <Tooltip title={category} placement="top">
            <Typography 
              variant="body2" 
              sx={{ 
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                maxWidth: '160px'
              }}
            >
              {category}
            </Typography>
          </Tooltip>
        );
      }
    },
    {
      field: 'original_price',
      headerName: 'Original Price',
      width: 130,
      renderCell: (params) => {
        const originalPrice = params.value;
        const currentPrice = params.row.current_price;
        const hasDiscount = originalPrice && currentPrice && originalPrice > currentPrice;
        
        if (!originalPrice) {
          return <Typography variant="body2" color="text.disabled">-</Typography>;
        }
        
        return (
          <Typography
            variant="body2"
            sx={{
              color: hasDiscount ? 'text.secondary' : 'text.primary',
              textDecoration: hasDiscount ? 'line-through' : 'none',
              fontWeight: 'normal'
            }}
          >
            ฿{originalPrice.toFixed(2)}
          </Typography>
        );
      },
    },
    {
      field: 'current_price',
      headerName: 'Sale Price',
      width: 130,
      renderCell: (params) => {
        const currentPrice = params.value;
        const originalPrice = params.row.original_price;
        const hasDiscount = originalPrice && originalPrice > currentPrice;
        
        if (!currentPrice) {
          return <Typography variant="body2" color="text.disabled">N/A</Typography>;
        }
        
        return (
          <Typography
            variant="body2"
            sx={{
              color: hasDiscount ? 'error.main' : 'text.primary',
              fontWeight: hasDiscount ? 'bold' : 'normal'
            }}
          >
            ฿{currentPrice.toFixed(2)}
          </Typography>
        );
      },
    },
    {
      field: 'discount_percentage',
      headerName: 'Discount',
      width: 120,
      renderCell: (params) => {
        const discountPercent = params.value;
        const currentPrice = params.row.current_price;
        const originalPrice = params.row.original_price;
        const savings = originalPrice && currentPrice ? (originalPrice - currentPrice) : 0;
        
        return discountPercent ? (
          <Box>
            <Chip
              label={`${discountPercent.toFixed(0)}%`}
              color="secondary"
              size="small"
              sx={{ mb: 0.5 }}
            />
            {savings > 0 && (
              <Typography
                variant="caption"
                sx={{
                  color: 'success.main',
                  display: 'block',
                  fontSize: '0.7rem',
                  fontWeight: 'bold'
                }}
              >
                Save ฿{savings.toFixed(2)}
              </Typography>
            )}
          </Box>
        ) : null;
      },
    },
    {
      field: 'availability',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => {
        const status = params.value;
        const getStatusLabel = (status: string) => {
          switch (status) {
            case 'in_stock': return 'In Stock';
            case 'out_of_stock': return 'Out of Stock';
            case 'limited_stock': return 'Limited';
            case 'preorder': return 'Pre-order';
            case 'unknown': return 'Unknown';
            default: return status || 'Unknown';
          }
        };
        
        const getStatusColor = (status: string) => {
          switch (status) {
            case 'in_stock': return 'success';
            case 'out_of_stock': return 'error';
            case 'limited_stock': return 'warning';
            case 'preorder': return 'info';
            default: return 'default';
          }
        };
        
        return (
          <Chip
            label={getStatusLabel(status)}
            color={getStatusColor(status) as any}
            size="small"
          />
        );
      },
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 150,
      renderCell: (params) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => rescrapeMutation.mutate(params.row.id)}
            disabled={rescrapeMutation.isPending}
          >
            <RefreshIcon />
          </IconButton>
          <Button
            size="small"
            href={params.row.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            View
          </Button>
        </Box>
      ),
    },
  ];

  const handleSearch = () => {
    setSearchParams({ ...searchParams, page: 1 });
    refetch();
  };

  const handleReset = () => {
    setSearchParams({
      query: '',
      brands: [],
      categories: [],
      min_price: 0,
      max_price: 10000,
      on_sale_only: false,
      in_stock_only: false,
      sort_by: 'name',
      sort_order: 'asc',
      page: 1,
      page_size: 20,
    });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Products
      </Typography>

      <RetailerSelector variant="full" showStats={true} showMultiMode={true} />

      {/* Search Bar */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Search products"
              placeholder="Search by name, SKU, or description"
              value={searchParams.query}
              onChange={(e) => setSearchParams({ ...searchParams, query: e.target.value })}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              InputProps={{
                endAdornment: <SearchIcon />,
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <Box display="flex" gap={1}>
              <Button
                variant="contained"
                onClick={handleSearch}
                startIcon={<SearchIcon />}
              >
                Search
              </Button>
              <Button
                variant="outlined"
                onClick={() => setShowFilters(!showFilters)}
                startIcon={<FilterIcon />}
              >
                Filters
              </Button>
              <Button
                variant="outlined"
                onClick={handleReset}
              >
                Reset
              </Button>
              <Button
                variant="outlined"
                startIcon={<ExportIcon />}
                disabled
              >
                Export
              </Button>
            </Box>
          </Grid>
        </Grid>

        {/* Filters */}
        {showFilters && (
          <Box mt={3}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Brands</InputLabel>
                  <Select
                    multiple
                    value={searchParams.brands}
                    onChange={(e) => setSearchParams({
                      ...searchParams,
                      brands: e.target.value as string[],
                    })}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {brandsData?.map((brand: string) => (
                      <MenuItem key={brand} value={brand}>
                        {brand}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Categories</InputLabel>
                  <Select
                    multiple
                    value={searchParams.categories}
                    onChange={(e) => setSearchParams({
                      ...searchParams,
                      categories: e.target.value as string[],
                    })}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {categoriesData?.map((category: any) => (
                      <MenuItem key={category.id} value={category.id}>
                        {category.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={3}>
                <Typography gutterBottom>Price Range</Typography>
                <Slider
                  value={[searchParams.min_price, searchParams.max_price]}
                  onChange={(e, value) => {
                    const [min, max] = value as number[];
                    setSearchParams({
                      ...searchParams,
                      min_price: min,
                      max_price: max,
                    });
                  }}
                  valueLabelDisplay="auto"
                  max={50000}
                  step={100}
                />
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="caption">฿{searchParams.min_price}</Typography>
                  <Typography variant="caption">฿{searchParams.max_price}</Typography>
                </Box>
              </Grid>

              <Grid item xs={12} md={3}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={searchParams.on_sale_only}
                      onChange={(e) => setSearchParams({
                        ...searchParams,
                        on_sale_only: e.target.checked,
                      })}
                    />
                  }
                  label="On Sale Only"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={searchParams.in_stock_only}
                      onChange={(e) => setSearchParams({
                        ...searchParams,
                        in_stock_only: e.target.checked,
                      })}
                    />
                  }
                  label="In Stock Only"
                />
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>

      {/* Products Grid */}
      <Paper sx={{ height: 600 }}>
        <DataGrid
          rows={data?.products || []}
          columns={columns}
          loading={isLoading}
          pagination
          paginationMode="server"
          rowCount={data?.total || 0}
          initialState={{
            pagination: {
              paginationModel: {
                pageSize: searchParams.page_size,
                page: searchParams.page - 1,
              },
            },
          }}
          pageSizeOptions={[20, 50, 100]}
          onPaginationModelChange={(model: GridPaginationModel) => {
            setSearchParams({
              ...searchParams,
              page: model.page + 1,
              page_size: model.pageSize,
            });
          }}
          onSortModelChange={(model: GridSortModel) => {
            if (model.length > 0) {
              setSearchParams({
                ...searchParams,
                sort_by: model[0].field,
                sort_order: model[0].sort || 'asc',
              });
            }
          }}
        />
      </Paper>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}