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
    max_price: 500000, // Increased from 10,000 to 500,000 to include all products
    on_sale_only: false,
    in_stock_only: false,
    sort_by: 'name',
    sort_order: 'asc',
    page: 1,
    page_size: 20,
  });

  // Separate pagination state to prevent loops
  const [paginationModel, setPaginationModel] = useState({
    page: 0, // DataGrid uses 0-based indexing
    pageSize: 20
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

  // Sync pagination state with search params when needed
  React.useEffect(() => {
    if (searchParams.page !== paginationModel.page + 1 || searchParams.page_size !== paginationModel.pageSize) {
      console.log('Syncing pagination: DataGrid page', paginationModel.page, '-> API page', paginationModel.page + 1);
      setSearchParams(prev => ({
        ...prev,
        page: paginationModel.page + 1,
        page_size: paginationModel.pageSize
      }));
    }
  }, [paginationModel.page, paginationModel.pageSize, searchParams.page, searchParams.page_size]);

  // Reset pagination when search filters change (except pagination itself)
  React.useEffect(() => {
    setPaginationModel(prev => ({ ...prev, page: 0 }));
  }, [searchParams.query, searchParams.brands, searchParams.categories, searchParams.min_price, searchParams.max_price, searchParams.on_sale_only, searchParams.in_stock_only, searchParams.sort_by, searchParams.sort_order, selectedRetailer, selectedRetailers]);

  // Search products
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['products', searchParams, multiRetailerMode ? selectedRetailers : selectedRetailer],
    queryFn: async () => {
      // Build search parameters, only including price filters if they're not at default values
      const baseParams = {
        query: searchParams.query,
        brands: searchParams.brands,
        categories: searchParams.categories,
        on_sale_only: searchParams.on_sale_only,
        in_stock_only: searchParams.in_stock_only,
        sort_by: searchParams.sort_by,
        sort_order: searchParams.sort_order,
        page: searchParams.page,
        page_size: searchParams.page_size,
        ...(multiRetailerMode ? 
          { retailer_codes: selectedRetailers } : 
          selectedRetailer ? { retailer_code: selectedRetailer } : {}
        )
      };
      
      // Only add price filters if user has modified them from defaults
      const searchParamsWithRetailer = {
        ...baseParams,
        ...(searchParams.min_price > 0 ? { min_price: searchParams.min_price } : {}),
        ...(searchParams.max_price < 500000 ? { max_price: searchParams.max_price } : {}),
      };
      console.log('Products API call with params:', searchParamsWithRetailer);
      const response = await productApi.search(searchParamsWithRetailer);
      console.log('Products API response:', { total: response.data.total, items: response.data.products?.length });
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    cacheTime: 300000, // 5 minutes
  });

  // React Query will automatically refetch when searchParams changes due to query key dependency

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
    { 
      field: 'sku', 
      headerName: 'SKU', 
      width: 120,
      renderCell: (params) => {
        const sku = params.value;
        const hasPrice = params.row.current_price || params.row.original_price;
        const hasBrand = params.row.brand && params.row.brand.trim();
        const hasCategory = params.row.category && params.row.category.trim();
        
        // Enhanced data completeness calculation
        const hasRetailer = params.row.retailer_code || (sku && sku.trim() !== '');
        const hasUrl = params.row.url && params.row.url.trim() !== '';
        const hasDescription = params.row.description && params.row.description.trim() !== '';
        
        const completenessScore = [sku, hasPrice, hasBrand, hasCategory, hasRetailer, hasUrl, hasDescription].filter(Boolean).length;
        const isIncomplete = completenessScore < 5; // Stricter threshold (out of 7 fields)
        
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography 
              variant="body2"
              sx={{ 
                fontFamily: 'monospace',
                fontSize: '0.875rem'
              }}
            >
              {sku || 'NO-SKU'}
            </Typography>
            {isIncomplete && (
              <Chip 
                label="⚠️" 
                size="small" 
                color="warning"
                sx={{ fontSize: '10px', height: '16px', minWidth: '24px' }}
                title={`Missing data (${7 - completenessScore}/7 fields incomplete)`}
              />
            )}
          </Box>
        );
      }
    },
    { 
      field: 'name', 
      headerName: 'Product Name', 
      width: 300, 
      flex: 1,
      renderCell: (params) => {
        let name = params.value || 'Unnamed Product';
        
        // Clean HTML/markdown from product names
        name = name
          .replace(/!\[.*?\]\(.*?\)/g, '') // Remove markdown images ![alt](url)
          .replace(/<[^>]*>/g, '') // Remove HTML tags
          .replace(/\[.*?\]\(.*?\)/g, '') // Remove markdown links [text](url) 
          .replace(/^-\s*/, '') // Remove leading dash
          .trim();
        
        // Enhanced name fallbacks
        if (!name || name.length < 3 || name === '-' || name === 'null' || name === 'undefined') {
          // Try to create a meaningful name from other fields
          const brand = params.row.brand;
          const category = params.row.category;
          const sku = params.row.sku;
          
          if (brand && brand !== 'No Brand' && brand.trim() !== '') {
            name = category && category !== 'General' ? `${brand} ${category} Product` : `${brand} Product`;
          } else if (category && category !== 'General') {
            name = `${category} Product`;
          } else if (sku) {
            name = `Product ${sku}`;
          } else {
            name = 'Unnamed Product';
          }
        }
        
        return (
          <Tooltip title={name} placement="top">
            <Typography 
              variant="body2" 
              sx={{ 
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {name}
            </Typography>
          </Tooltip>
        );
      }
    },
    { 
      field: 'brand', 
      headerName: 'Brand', 
      width: 120,
      renderCell: (params) => {
        let brand = params.value;
        
        // Enhanced brand fallbacks
        if (!brand || brand.trim() === '' || brand === '-' || brand === 'null' || brand === 'undefined' || brand.toLowerCase() === 'unknown') {
          brand = 'No Brand';
        }
        
        return (
          <Typography 
            variant="body2" 
            sx={{ 
              color: brand === 'No Brand' ? 'text.disabled' : 'text.primary',
              fontStyle: brand === 'No Brand' ? 'italic' : 'normal'
            }}
          >
            {brand}
          </Typography>
        );
      }
    },
    ...(multiRetailerMode ? [
      {
        field: 'retailer_code',
        headerName: 'Retailer',
        width: 100,
        renderCell: (params: any) => {
          // Derive retailer code from SKU if retailer_code is null
          let retailerCode = params.value;
          if (!retailerCode && params.row.sku) {
            const sku = params.row.sku;
            // Enhanced retailer code detection
            if (sku.startsWith('HP-') || sku.includes('HP-')) retailerCode = 'HP';
            else if (sku.startsWith('TWD-') || sku.includes('TWD-')) retailerCode = 'TWD';
            else if (sku.startsWith('GH-') || sku.includes('GH-')) retailerCode = 'GH';
            else if (sku.startsWith('DH-') || sku.includes('DH-')) retailerCode = 'DH';
            else if (sku.startsWith('BT-') || sku.includes('BT-')) retailerCode = 'BT';
            else if (sku.startsWith('MH-') || sku.includes('MH-')) retailerCode = 'MH';
            else if (/^\d{5,}$/.test(sku)) retailerCode = 'TWD'; // Long numeric SKUs are typically TWD
            else if (/^[A-Z]{2,}\d+/.test(sku)) retailerCode = 'HP'; // Letter+number patterns often HP
            else {
              // Fallback: derive from product URL if available
              const url = params.row.url || '';
              if (url.includes('homepro')) retailerCode = 'HP';
              else if (url.includes('thaiwatsadu')) retailerCode = 'TWD';
              else if (url.includes('globalhouse')) retailerCode = 'GH';
              else if (url.includes('dohome')) retailerCode = 'DH';
              else if (url.includes('boonthavorn')) retailerCode = 'BT';
              else if (url.includes('megahome')) retailerCode = 'MH';
              else retailerCode = 'GEN'; // Generic instead of UNK
            }
          }
          
          return (
            <Stack direction="row" alignItems="center" spacing={1}>
              <Avatar
                sx={{
                  bgcolor: retailerColors[retailerCode] || (retailerCode === 'GEN' ? '#9E9E9E' : '#666'),
                  width: 24,
                  height: 24,
                  fontSize: 12,
                }}
              >
                {retailerCode === 'GEN' ? '?' : retailerCode}
              </Avatar>
              <Typography variant="caption">{retailerCode}</Typography>
            </Stack>
          );
        },
      } as GridColDef
    ] : []),
    { 
      field: 'category', 
      headerName: 'Category', 
      width: 180,
      renderCell: (params) => {
        let category = params.value;
        
        // Enhanced category fallbacks
        if (!category || category.trim() === '' || category === '-' || category === 'null' || category === 'undefined') {
          category = 'General';
        }
        
        return (
          <Tooltip title={category} placement="top">
            <Typography 
              variant="body2" 
              sx={{ 
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                maxWidth: '160px',
                color: category === 'General' ? 'text.disabled' : 'text.primary'
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
        
        if (!originalPrice || originalPrice === 0 || originalPrice === null || originalPrice === undefined) {
          return <Typography variant="body2" color="text.disabled">No Price</Typography>;
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
        
        if (!currentPrice || currentPrice === 0 || currentPrice === null || currentPrice === undefined) {
          return <Typography variant="body2" color="text.disabled">No Price</Typography>;
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
                Save ฿{savings.toFixed(0)}
              </Typography>
            )}
          </Box>
        ) : (
          <Typography variant="caption" color="text.disabled" sx={{ fontStyle: 'italic' }}>
            No Discount
          </Typography>
        );
      },
    },
    {
      field: 'availability',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => {
        let status = params.value;
        const currentPrice = params.row.current_price;
        
        // If status is unknown/null but price exists, assume in stock
        if ((!status || status === 'unknown') && currentPrice) {
          status = 'in_stock';
        }
        
        const getStatusLabel = (status: string) => {
          switch (status) {
            case 'in_stock': return 'Available';
            case 'out_of_stock': return 'Out of Stock';
            case 'limited_stock': return 'Limited';
            case 'preorder': return 'Pre-order';
            case 'unknown': return 'Check Store';
            default: return 'Check Store';
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
            href={params.row.url || '#'}
            target={params.row.url ? "_blank" : "_self"}
            rel="noopener noreferrer"
            disabled={!params.row.url}
            sx={{ 
              opacity: params.row.url ? 1 : 0.5,
              cursor: params.row.url ? 'pointer' : 'not-allowed'
            }}
          >
            {params.row.url ? 'View' : 'No URL'}
          </Button>
        </Box>
      ),
    },
  ];

  const handleSearch = () => {
    setPaginationModel({ page: 0, pageSize: paginationModel.pageSize });
    setSearchParams({ ...searchParams, page: 1 });
    refetch();
  };

  const handleReset = () => {
    setPaginationModel({ page: 0, pageSize: 20 });
    setSearchParams({
      query: '',
      brands: [],
      categories: [],
      min_price: 0,
      max_price: 500000, // Updated to match new default
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
                    {categoriesData?.map((category: string) => (
                      <MenuItem key={category} value={category}>
                        {category}
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
                  max={500000}
                  step={1000}
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
          paginationModel={paginationModel}
          pageSizeOptions={[20, 50, 100]}
          onPaginationModelChange={(model: GridPaginationModel) => {
            console.log('Pagination model change:', model);
            setPaginationModel(model);
          }}
          onSortModelChange={(model: GridSortModel) => {
            if (model.length > 0) {
              setSearchParams({
                ...searchParams,
                sort_by: model[0].field,
                sort_order: model[0].sort || 'asc',
                page: 1, // Reset to first page when sorting
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