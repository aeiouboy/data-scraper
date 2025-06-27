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
} from '@mui/material';
import { DataGrid, GridColDef, GridPaginationModel, GridSortModel } from '@mui/x-data-grid';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { productApi } from '../services/api';

export default function Products() {
  const queryClient = useQueryClient();
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
    queryKey: ['brands'],
    queryFn: async () => {
      const response = await productApi.getBrands();
      return response.data.brands;
    },
  });

  const { data: categoriesData } = useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const response = await productApi.getCategories();
      return response.data.categories;
    },
  });

  // Search products
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['products', searchParams],
    queryFn: async () => {
      const response = await productApi.search(searchParams);
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
    { field: 'category', headerName: 'Category', width: 120 },
    {
      field: 'current_price',
      headerName: 'Price',
      width: 120,
      renderCell: (params) => `฿${params.value?.toFixed(2) || 'N/A'}`,
    },
    {
      field: 'discount_percentage',
      headerName: 'Discount',
      width: 100,
      renderCell: (params) => params.value ? (
        <Chip
          label={`${params.value.toFixed(0)}%`}
          color="secondary"
          size="small"
        />
      ) : null,
    },
    {
      field: 'availability',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={params.value === 'in_stock' ? 'success' : 'default'}
          size="small"
        />
      ),
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