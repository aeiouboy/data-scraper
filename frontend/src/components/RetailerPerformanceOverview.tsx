import React, { useState, useMemo, useCallback } from 'react';
import {
  Paper,
  Typography,
  Grid,
  Box,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  TextField,
  InputAdornment,
  Chip,
  Alert,
  Skeleton,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Search as SearchIcon,
  Sort as SortIcon,
  FilterList as FilterIcon,
  ViewModule as GridViewIcon,
  ViewList as ListViewIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  Store as StoreIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import RetailerPerformanceCard from './RetailerPerformanceCard';

interface RetailerStats {
  code: string;
  name: string;
  actual_products: number;
  in_stock_products: number;
  priced_products: number;
  avg_price: number;
  min_price: number;
  max_price: number;
  ultra_critical_count: number;
  high_value_count: number;
  standard_count: number;
  low_priority_count: number;
  category_coverage_percentage: number;
  brand_coverage_percentage: number;
  last_scraped_at: string;
  market_position?: string;
}

interface RetailerPerformanceOverviewProps {
  retailerStats: RetailerStats[];
  selectedRetailers: string[];
  retailerColors: Record<string, string>;
  isLoading?: boolean;
  error?: string | null;
  onRetailerClick?: (retailerCode: string) => void;
  onRefresh?: () => void;
  showComparison?: boolean;
  comparisonData?: Record<string, {
    productsChange?: number;
    priceChange?: number;
    coverageChange?: number;
  }>;
}

type SortOption = 'name' | 'products' | 'coverage' | 'price' | 'health';
type ViewMode = 'grid' | 'list';
type FilterOption = 'all' | 'healthy' | 'warning' | 'critical';

const RetailerPerformanceOverview: React.FC<RetailerPerformanceOverviewProps> = ({
  retailerStats,
  selectedRetailers,
  retailerColors,
  isLoading = false,
  error = null,
  onRetailerClick,
  onRefresh,
  showComparison = false,
  comparisonData = {},
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('products');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [healthFilter, setHealthFilter] = useState<FilterOption>('all');
  const [sortMenuAnchor, setSortMenuAnchor] = useState<null | HTMLElement>(null);

  // Filter and sort retailers
  const processedRetailers = useMemo(() => {
    let filtered = retailerStats.filter(stat => 
      selectedRetailers.includes(stat.code)
    );

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(retailer =>
        retailer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        retailer.code.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply health filter
    if (healthFilter !== 'all') {
      filtered = filtered.filter(retailer => {
        const stockRate = retailer.actual_products > 0 
          ? (retailer.in_stock_products / retailer.actual_products) * 100 
          : 0;
        const pricingRate = retailer.actual_products > 0 
          ? (retailer.priced_products / retailer.actual_products) * 100 
          : 0;

        if (healthFilter === 'healthy') return stockRate >= 90 && pricingRate >= 90;
        if (healthFilter === 'warning') return (stockRate >= 70 && pricingRate >= 70) && !(stockRate >= 90 && pricingRate >= 90);
        if (healthFilter === 'critical') return stockRate < 70 || pricingRate < 70;
        return true;
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let valueA: number, valueB: number;

      switch (sortBy) {
        case 'name':
          return sortOrder === 'asc' 
            ? a.name.localeCompare(b.name)
            : b.name.localeCompare(a.name);
        case 'products':
          valueA = a.actual_products;
          valueB = b.actual_products;
          break;
        case 'coverage':
          valueA = a.category_coverage_percentage || 0;
          valueB = b.category_coverage_percentage || 0;
          break;
        case 'price':
          valueA = a.avg_price || 0;
          valueB = b.avg_price || 0;
          break;
        case 'health':
          valueA = (a.in_stock_products / Math.max(a.actual_products, 1)) * 100;
          valueB = (b.in_stock_products / Math.max(b.actual_products, 1)) * 100;
          break;
        default:
          valueA = a.actual_products;
          valueB = b.actual_products;
      }

      return sortOrder === 'asc' ? valueA - valueB : valueB - valueA;
    });

    return filtered;
  }, [retailerStats, selectedRetailers, searchTerm, sortBy, sortOrder, healthFilter]);

  // Calculate summary statistics
  const summaryStats = useMemo(() => {
    const stats = processedRetailers.reduce(
      (acc, retailer) => ({
        totalProducts: acc.totalProducts + retailer.actual_products,
        totalInStock: acc.totalInStock + retailer.in_stock_products,
        avgCoverage: acc.avgCoverage + (retailer.category_coverage_percentage || 0),
        healthyCount: acc.healthyCount + (
          (retailer.in_stock_products / Math.max(retailer.actual_products, 1)) * 100 >= 90 ? 1 : 0
        ),
      }),
      { totalProducts: 0, totalInStock: 0, avgCoverage: 0, healthyCount: 0 }
    );

    return {
      ...stats,
      avgCoverage: processedRetailers.length > 0 ? stats.avgCoverage / processedRetailers.length : 0,
      stockRate: stats.totalProducts > 0 ? (stats.totalInStock / stats.totalProducts) * 100 : 0,
    };
  }, [processedRetailers]);

  const handleSortMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>) => {
    setSortMenuAnchor(event.currentTarget);
  }, []);

  const handleSortMenuClose = useCallback(() => {
    setSortMenuAnchor(null);
  }, []);

  const handleSortChange = useCallback((newSortBy: SortOption) => {
    if (sortBy === newSortBy) {
      setSortOrder(order => order === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
    handleSortMenuClose();
  }, [sortBy, handleSortMenuClose]);

  if (error) {
    return (
      <Paper sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        {onRefresh && (
          <Box textAlign="center">
            <IconButton onClick={onRefresh} color="primary">
              <RefreshIcon />
            </IconButton>
          </Box>
        )}
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={3}>
        <Stack direction="row" alignItems="center" spacing={2}>
          <AssessmentIcon color="primary" />
          <Typography variant="h6" fontWeight="bold">
            📊 Retailer Performance Overview
          </Typography>
          {showComparison && (
            <Chip
              icon={<TrendingUpIcon />}
              label="Comparison Mode"
              color="primary"
              variant="outlined"
              size="small"
            />
          )}
        </Stack>
        {onRefresh && (
          <Tooltip title="Refresh data">
            <IconButton onClick={onRefresh} disabled={isLoading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        )}
      </Stack>

      {/* Summary Statistics */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Box textAlign="center" p={1}>
            <Typography variant="h4" fontWeight="bold" color="primary.main">
              {summaryStats.totalProducts.toLocaleString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Products
            </Typography>
          </Box>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Box textAlign="center" p={1}>
            <Typography variant="h4" fontWeight="bold" color="success.main">
              {summaryStats.stockRate.toFixed(1)}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Overall Stock Rate
            </Typography>
          </Box>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Box textAlign="center" p={1}>
            <Typography variant="h4" fontWeight="bold" color="info.main">
              {summaryStats.avgCoverage.toFixed(1)}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Avg Coverage
            </Typography>
          </Box>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Box textAlign="center" p={1}>
            <Typography variant="h4" fontWeight="bold" color="warning.main">
              {summaryStats.healthyCount}/{processedRetailers.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Healthy Retailers
            </Typography>
          </Box>
        </Grid>
      </Grid>

      {/* Controls */}
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        spacing={2}
        alignItems={{ xs: 'stretch', sm: 'center' }}
        mb={3}
      >
        <TextField
          placeholder="Search retailers..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          size="small"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ minWidth: 200 }}
        />

        <ToggleButtonGroup
          value={healthFilter}
          exclusive
          onChange={(_, value) => value && setHealthFilter(value)}
          size="small"
        >
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="healthy">Healthy</ToggleButton>
          <ToggleButton value="warning">Warning</ToggleButton>
          <ToggleButton value="critical">Critical</ToggleButton>
        </ToggleButtonGroup>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Sort options">
            <IconButton onClick={handleSortMenuOpen} size="small">
              <SortIcon />
            </IconButton>
          </Tooltip>

          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(_, value) => value && setViewMode(value)}
            size="small"
          >
            <ToggleButton value="grid">
              <GridViewIcon />
            </ToggleButton>
            <ToggleButton value="list">
              <ListViewIcon />
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </Stack>

      {/* Sort Menu */}
      <Menu
        anchorEl={sortMenuAnchor}
        open={Boolean(sortMenuAnchor)}
        onClose={handleSortMenuClose}
      >
        <MenuItem onClick={() => handleSortChange('products')}>
          <ListItemIcon>
            <StoreIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Products {sortBy === 'products' && `(${sortOrder})`}</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('coverage')}>
          <ListItemIcon>
            <AssessmentIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Coverage {sortBy === 'coverage' && `(${sortOrder})`}</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('health')}>
          <ListItemIcon>
            <TrendingUpIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Health {sortBy === 'health' && `(${sortOrder})`}</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleSortChange('name')}>
          <ListItemIcon>
            <FilterIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Name {sortBy === 'name' && `(${sortOrder})`}</ListItemText>
        </MenuItem>
      </Menu>

      {/* Results Count */}
      <Typography variant="body2" color="text.secondary" mb={2}>
        Showing {processedRetailers.length} of {selectedRetailers.length} selected retailers
      </Typography>

      {/* Retailer Cards */}
      {isLoading ? (
        <Grid container spacing={3}>
          {Array.from({ length: 3 }).map((_, index) => (
            <Grid item xs={12} md={viewMode === 'grid' ? 6 : 12} lg={viewMode === 'grid' ? 4 : 12} key={index}>
              <Skeleton variant="rectangular" height={400} />
            </Grid>
          ))}
        </Grid>
      ) : processedRetailers.length === 0 ? (
        <Box textAlign="center" py={4}>
          <StoreIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No retailers found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your search or filter criteria
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {processedRetailers.map((retailer, index) => (
            <Grid 
              item 
              xs={12} 
              md={viewMode === 'grid' ? 6 : 12} 
              lg={viewMode === 'grid' ? 4 : 12} 
              key={retailer.code}
            >
              <RetailerPerformanceCard
                retailer={retailer}
                index={index}
                retailerColor={retailerColors[retailer.code] || '#666'}
                onCardClick={onRetailerClick}
                showComparison={showComparison}
                comparisonMetrics={comparisonData[retailer.code]}
              />
            </Grid>
          ))}
        </Grid>
      )}
    </Paper>
  );
};

export default RetailerPerformanceOverview;