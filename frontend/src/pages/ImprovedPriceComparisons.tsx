import React, { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Slider,
  Switch,
  FormControlLabel,
  Button,
  Chip,
  Stack,
  Paper,
  IconButton,
  Tooltip,
  useTheme,
  alpha,
  LinearProgress,
  Avatar,
} from '@mui/material';
import {
  TuneOutlined as FilterIcon,
  ViewModuleOutlined as GridIcon,
  ViewListOutlined as ListIcon,
  TableViewOutlined as TableIcon,
  DownloadOutlined as ExportIcon,
  RefreshOutlined as RefreshIcon,
  TrendingUpOutlined as TrendingIcon,
  PsychologyOutlined as AIIcon,
  SpeedOutlined as PerformanceIcon,
  AnalyticsOutlined as AnalyticsIcon,
  AutoAwesomeOutlined as MagicIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { optimizedMatchingApi } from '../services/optimizedMatchingApi';
import { priceComparisonApi } from '../services/api';
import ImprovedPriceComparisonCard from '../components/ImprovedPriceComparisonCard';

interface FilterState {
  minConfidence: number;
  minSavings: number;
  minSavingsPercent: number;
  useOptimized: boolean;
  category: string;
  maxResults: number;
}

type ViewMode = 'grid' | 'list' | 'table';

const ImprovedPriceComparisons: React.FC = () => {
  const theme = useTheme();
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [showFilters, setShowFilters] = useState(true);
  
  const [filters, setFilters] = useState<FilterState>({
    minConfidence: 0.6,
    minSavings: 100,
    minSavingsPercent: 5,
    useOptimized: true,
    category: '',
    maxResults: 50,
  });

  // Fetch optimized comparisons
  const { data: comparisonsData, isLoading, refetch } = useQuery({
    queryKey: ['improved-price-comparisons', filters],
    queryFn: () => priceComparisonApi.getDetailedComparisonsOptimized({
      minSavings: filters.minSavings,
      minSavingsPercent: filters.minSavingsPercent,
      minConfidence: filters.minConfidence,
      category: filters.category || undefined,
      limit: filters.maxResults,
    }),
    enabled: filters.useOptimized,
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Fetch statistics
  useQuery({
    queryKey: ['matching-statistics'],
    queryFn: () => optimizedMatchingApi.getStatistics(),
    refetchInterval: 60000,
  });

  const comparisons = comparisonsData?.data?.comparisons || [];

  // Calculate summary statistics
  const summaryStats = useMemo(() => {
    if (!comparisons.length) {
      return {
        totalSavings: 0,
        avgConfidence: 0,
        bestDeal: 0,
        productsCount: 0,
      };
    }

    const totalSavings = comparisons.reduce((sum: number, comp: any) => 
      sum + (comp.priceAnalysis?.savingsAmount || 0), 0
    );
    
    const avgConfidence = comparisons.reduce((sum: number, comp: any) => 
      sum + (comp.matchConfidence || 0), 0
    ) / comparisons.length;

    const bestDeal = Math.max(...comparisons.map((comp: any) => 
      comp.priceAnalysis?.savingsPercentage || 0
    ));

    return {
      totalSavings,
      avgConfidence,
      bestDeal,
      productsCount: comparisons.length,
    };
  }, [comparisons]);

  const handleFilterChange = useCallback((key: keyof FilterState, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const handleExport = useCallback(() => {
    const csvData = comparisons.map((comp: any) => ({
      product: comp.productName,
      brand: comp.brand,
      category: comp.category,
      savings: comp.priceAnalysis?.savingsAmount || 0,
      savingsPercent: comp.priceAnalysis?.savingsPercentage || 0,
      confidence: comp.matchConfidence || 0,
      bestPrice: comp.priceAnalysis?.bestPrice || 0,
      worstPrice: comp.priceAnalysis?.worstPrice || 0,
    }));

    const csv = [
      Object.keys(csvData[0]).join(','),
      ...csvData.map((row: any) => Object.values(row).join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `price-comparisons-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  }, [comparisons]);

  // Enhanced statistics display
  const renderStatsDashboard = () => (
    <Grid container spacing={3} sx={{ mb: 4 }}>
      <Grid item xs={12} md={3}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card sx={{ 
            background: `linear-gradient(135deg, ${theme.palette.success.main} 0%, ${theme.palette.success.dark} 100%)`,
            color: 'white'
          }}>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: alpha('#fff', 0.2) }}>
                  <TrendingIcon />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    ฿{summaryStats.totalSavings.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Total Savings Available
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </motion.div>
      </Grid>

      <Grid item xs={12} md={3}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card sx={{ 
            background: `linear-gradient(135deg, ${theme.palette.info.main} 0%, ${theme.palette.info.dark} 100%)`,
            color: 'white'
          }}>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: alpha('#fff', 0.2) }}>
                  <AIIcon />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {(summaryStats.avgConfidence * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Average Match Confidence
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </motion.div>
      </Grid>

      <Grid item xs={12} md={3}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card sx={{ 
            background: `linear-gradient(135deg, ${theme.palette.warning.main} 0%, ${theme.palette.warning.dark} 100%)`,
            color: 'white'
          }}>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: alpha('#fff', 0.2) }}>
                  <AnalyticsIcon />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {summaryStats.bestDeal.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Best Deal Found
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </motion.div>
      </Grid>

      <Grid item xs={12} md={3}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card sx={{ 
            background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
            color: 'white'
          }}>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: alpha('#fff', 0.2) }}>
                  <PerformanceIcon />
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {summaryStats.productsCount}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Products with Savings
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </motion.div>
      </Grid>
    </Grid>
  );

  // Enhanced filters panel
  const renderFiltersPanel = () => (
    <AnimatePresence>
      {showFilters && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Paper 
            sx={{ 
              p: 3, 
              mb: 3, 
              background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
              border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`
            }}
          >
            <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
              <MagicIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Smart Filters
              </Typography>
              <Chip 
                label={filters.useOptimized ? "AI Enhanced" : "Standard"} 
                color={filters.useOptimized ? "success" : "default"}
                icon={<AIIcon />}
              />
            </Stack>

            <Grid container spacing={4}>
              <Grid item xs={12} md={4}>
                <Typography gutterBottom fontWeight="medium">
                  Match Confidence: {(filters.minConfidence * 100).toFixed(0)}%
                </Typography>
                <Slider
                  value={filters.minConfidence}
                  min={0.1}
                  max={0.9}
                  step={0.05}
                  onChange={(_, value) => handleFilterChange('minConfidence', value)}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
                  sx={{
                    '& .MuiSlider-thumb': {
                      background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    },
                    '& .MuiSlider-track': {
                      background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    },
                  }}
                />
              </Grid>

              <Grid item xs={12} md={4}>
                <Typography gutterBottom fontWeight="medium">
                  Min Savings: ฿{filters.minSavings.toLocaleString()}
                </Typography>
                <Slider
                  value={filters.minSavings}
                  min={0}
                  max={5000}
                  step={50}
                  onChange={(_, value) => handleFilterChange('minSavings', value)}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `฿${value.toLocaleString()}`}
                  sx={{
                    '& .MuiSlider-thumb': {
                      background: `linear-gradient(45deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`,
                    },
                    '& .MuiSlider-track': {
                      background: `linear-gradient(45deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`,
                    },
                  }}
                />
              </Grid>

              <Grid item xs={12} md={4}>
                <Typography gutterBottom fontWeight="medium">
                  Min Savings %: {filters.minSavingsPercent.toFixed(1)}%
                </Typography>
                <Slider
                  value={filters.minSavingsPercent}
                  min={0}
                  max={50}
                  step={1}
                  onChange={(_, value) => handleFilterChange('minSavingsPercent', value)}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${value}%`}
                  sx={{
                    '& .MuiSlider-thumb': {
                      background: `linear-gradient(45deg, ${theme.palette.warning.main}, ${theme.palette.warning.dark})`,
                    },
                    '& .MuiSlider-track': {
                      background: `linear-gradient(45deg, ${theme.palette.warning.main}, ${theme.palette.warning.dark})`,
                    },
                  }}
                />
              </Grid>
            </Grid>

            <Box sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={filters.useOptimized}
                    onChange={(e) => handleFilterChange('useOptimized', e.target.checked)}
                    color="primary"
                  />
                }
                label="Use AI-Enhanced Matching"
              />
              
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                {filters.useOptimized ? 
                  "🚀 50% better accuracy with progressive matching" : 
                  "📊 Standard algorithm"
                }
              </Typography>
            </Box>
          </Paper>
        </motion.div>
      )}
    </AnimatePresence>
  );

  const renderViewModeControls = () => (
    <Stack direction="row" spacing={2} alignItems="center">
      <Paper sx={{ p: 0.5 }}>
        <Stack direction="row" spacing={0}>
          {(['grid', 'list', 'table'] as ViewMode[]).map((mode) => (
            <Tooltip key={mode} title={`${mode.charAt(0).toUpperCase() + mode.slice(1)} View`}>
              <IconButton
                onClick={() => setViewMode(mode)}
                sx={{
                  borderRadius: 1,
                  bgcolor: viewMode === mode ? theme.palette.primary.main : 'transparent',
                  color: viewMode === mode ? 'white' : 'inherit',
                  '&:hover': {
                    bgcolor: viewMode === mode ? theme.palette.primary.dark : alpha(theme.palette.primary.main, 0.1),
                  },
                }}
              >
                {mode === 'grid' && <GridIcon />}
                {mode === 'list' && <ListIcon />}
                {mode === 'table' && <TableIcon />}
              </IconButton>
            </Tooltip>
          ))}
        </Stack>
      </Paper>

      <Button
        startIcon={<FilterIcon />}
        variant={showFilters ? "contained" : "outlined"}
        onClick={() => setShowFilters(!showFilters)}
        sx={{ textTransform: 'none' }}
      >
        Filters
      </Button>

      <Button
        startIcon={<RefreshIcon />}
        variant="outlined"
        onClick={() => refetch()}
        disabled={isLoading}
        sx={{ textTransform: 'none' }}
      >
        Refresh
      </Button>

      <Button
        startIcon={<ExportIcon />}
        variant="outlined"
        onClick={handleExport}
        disabled={!comparisons.length}
        sx={{ textTransform: 'none' }}
      >
        Export
      </Button>
    </Stack>
  );

  if (isLoading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Stack spacing={3} alignItems="center">
          <LinearProgress sx={{ width: '100%', mb: 2 }} />
          <Typography variant="h6">Loading enhanced price comparisons...</Typography>
          <Typography variant="body2" color="text.secondary">
            AI is analyzing {filters.useOptimized ? 'optimized' : 'standard'} matches
          </Typography>
        </Stack>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 4 }}>
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <Typography variant="h3" fontWeight="bold" gutterBottom>
            🚀 Enhanced Price Comparisons
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            AI-powered matching with 50% better accuracy
          </Typography>
        </motion.div>

        {renderViewModeControls()}
      </Box>

      {/* Statistics Dashboard */}
      {renderStatsDashboard()}

      {/* Filters */}
      {renderFiltersPanel()}

      {/* Results */}
      {comparisons.length > 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Box sx={{ mb: 3 }}>
            <Typography variant="h5" gutterBottom>
              Found {comparisons.length} enhanced matches
              <Chip 
                label={`${filters.useOptimized ? 'AI Enhanced' : 'Standard'}`}
                color={filters.useOptimized ? 'success' : 'default'}
                sx={{ ml: 2 }}
              />
            </Typography>
          </Box>

          <Grid container spacing={3}>
            {comparisons.map((comparison: any, index: number) => (
              <Grid item xs={12} lg={viewMode === 'grid' ? 6 : 12} key={comparison.matchId || index}>
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <ImprovedPriceComparisonCard
                    productName={comparison.productName}
                    category={comparison.category}
                    brand={comparison.brand}
                    retailers={comparison.retailerPrices}
                    bestRetailerCode={comparison.priceAnalysis?.bestRetailer}
                    savingsAmount={comparison.priceAnalysis?.savingsAmount || 0}
                    savingsPercentage={comparison.priceAnalysis?.savingsPercentage || 0}
                    matchConfidence={comparison.matchConfidence}
                    matchDetails={comparison.matchDetails}
                    onCompare={() => console.log('Compare:', comparison.productName)}
                    onViewDetails={() => console.log('View details:', comparison.productName)}
                  />
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </motion.div>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <Paper sx={{ p: 6, textAlign: 'center' }}>
            <Typography variant="h5" gutterBottom>
              No price comparisons found
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Try adjusting your filters or check back later for new matches
            </Typography>
            <Button
              variant="contained"
              onClick={() => handleFilterChange('minConfidence', 0.3)}
              sx={{ textTransform: 'none' }}
            >
              Lower Confidence Threshold
            </Button>
          </Paper>
        </motion.div>
      )}
    </Container>
  );
};

export default ImprovedPriceComparisons;