/**
 * Ultra-Strict Price Comparisons Page
 * Enhanced price comparison with maximum matching accuracy
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Skeleton,
  Chip,
  Stack,
  Divider,
  Paper,
  LinearProgress,
  Tooltip,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  CompareArrows as CompareIcon,
  Verified as VerifiedIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ultraStrictMatchingApi,
  UltraStrictMatchResponse,
  UltraStrictMatchRequest,
  UltraStrictConfig
} from '../services/ultraStrictMatchingApi';
import { priceComparisonApi } from '../services/api';
import UltraStrictPriceComparisonCard from '../components/UltraStrictPriceComparisonCard';
import UltraStrictMatchValidationIndicator from '../components/UltraStrictMatchValidationIndicator';

interface ProductSummary {
  id: string;
  name: string;
  brand: string;
  price: number;
  retailer_code: string;
  url: string;
  category: string;
}

export default function UltraStrictPriceComparisons() {
  // State management
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<ProductSummary | null>(null);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.6);
  const [maxResults, setMaxResults] = useState(10);
  const [showSettings, setShowSettings] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [excludedRetailers, setExcludedRetailers] = useState<string[]>([]);

  const queryClient = useQueryClient();

  // Fetch ultra-strict configuration
  const { data: config, isLoading: loadingConfig } = useQuery({
    queryKey: ['ultra-strict-config'],
    queryFn: () => ultraStrictMatchingApi.getConfig(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Search products for matching
  const { data: products, isLoading: loadingProducts } = useQuery({
    queryKey: ['products-search', searchTerm],
    queryFn: async () => {
      if (!searchTerm.trim()) return [];
      try {
        const response = await priceComparisonApi.getTopSavings(20);
        return response.data.products || [];
      } catch (error) {
        console.error('Error searching products:', error);
        return [];
      }
    },
    enabled: !!searchTerm.trim(),
  });

  // Find ultra-strict matches
  const { data: matchResults, isLoading: loadingMatches, error: matchError } = useQuery({
    queryKey: ['ultra-strict-matches', selectedProduct?.id, categoryFilter, confidenceThreshold, maxResults, excludedRetailers],
    queryFn: async () => {
      if (!selectedProduct) return null;
      
      const request: UltraStrictMatchRequest = {
        product_id: selectedProduct.id,
        max_results: maxResults,
        confidence_threshold: confidenceThreshold,
        category_filter: categoryFilter || undefined,
        retailer_exclusions: excludedRetailers.length > 0 ? excludedRetailers : undefined,
      };
      
      return await ultraStrictMatchingApi.findMatches(request);
    },
    enabled: !!selectedProduct,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  // Auto-refresh functionality
  useEffect(() => {
    if (!autoRefresh || !selectedProduct) return;
    
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ['ultra-strict-matches'] });
    }, 30000); // Refresh every 30 seconds
    
    return () => clearInterval(interval);
  }, [autoRefresh, selectedProduct, queryClient]);

  // Handlers
  const handleProductSelect = (product: ProductSummary) => {
    setSelectedProduct(product);
    setSearchTerm('');
  };

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['ultra-strict-matches'] });
  };

  const handleViewDetails = (productId: string) => {
    // Navigate to product details page
    window.open(`/products/${productId}`, '_blank');
  };

  const handleAddToCart = (productId: string) => {
    // Add to cart functionality
    console.log('Add to cart:', productId);
  };

  // Calculate summary statistics
  const getSummaryStats = () => {
    if (!matchResults) return null;
    
    const totalMatches = matchResults.matches.length;
    const exactMatches = matchResults.matches.filter(m => m.match_type === 'exact').length;
    const highMatches = matchResults.matches.filter(m => m.match_type === 'high').length;
    const avgConfidence = matchResults.matches.reduce((sum, m) => sum + m.confidence, 0) / totalMatches;
    const totalSavings = matchResults.matches.reduce((sum, m) => sum + (m.price_comparison?.savings || 0), 0);
    const betterDeals = matchResults.matches.filter(m => m.price_comparison?.is_better_deal).length;
    
    return {
      totalMatches,
      exactMatches,
      highMatches,
      avgConfidence,
      totalSavings,
      betterDeals,
      processingTime: matchResults.processing_time_ms,
    };
  };

  const summaryStats = getSummaryStats();

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 2 }}>
          🔍 Ultra-Strict Price Comparisons
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          Find the most accurate product matches with strict validation and maximum precision
        </Typography>
        
        {/* Configuration Info */}
        {config && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Ultra-Strict Mode:</strong> Using {config.version} with {config.features.join(', ')}
            </Typography>
          </Alert>
        )}
      </Box>

      {/* Search Section */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Search Products
          </Typography>
          
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Search products..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Enter product name, brand, or SKU"
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  label="Category"
                >
                  <MenuItem value="">All Categories</MenuItem>
                  <MenuItem value="air-conditioner">Air Conditioners</MenuItem>
                  <MenuItem value="refrigerator">Refrigerators</MenuItem>
                  <MenuItem value="washing-machine">Washing Machines</MenuItem>
                  <MenuItem value="television">Televisions</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<SettingsIcon />}
                onClick={() => setShowSettings(!showSettings)}
              >
                Settings
              </Button>
            </Grid>
          </Grid>

          {/* Search Results */}
          {loadingProducts && (
            <Box sx={{ mt: 2 }}>
              <Skeleton variant="rectangular" height={100} />
            </Box>
          )}
          
          {products && products.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Search Results ({products.length})
              </Typography>
              <Grid container spacing={1}>
                {products.map((product: ProductSummary) => (
                  <Grid item xs={12} key={product.id}>
                    <Card 
                      sx={{ 
                        cursor: 'pointer',
                        border: selectedProduct?.id === product.id ? '2px solid #1976d2' : '1px solid #e0e0e0',
                        '&:hover': { backgroundColor: '#f5f5f5' }
                      }}
                      onClick={() => handleProductSelect(product)}
                    >
                      <CardContent sx={{ py: 1 }}>
                        <Grid container spacing={2} alignItems="center">
                          <Grid item xs={12} md={8}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                              {product.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {product.brand} • {product.retailer_code}
                            </Typography>
                          </Grid>
                          <Grid item xs={12} md={4}>
                            <Typography variant="h6" sx={{ textAlign: 'right' }}>
                              ฿{product.price.toLocaleString()}
                            </Typography>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}

          {/* Settings Panel */}
          <Accordion expanded={showSettings} onChange={() => setShowSettings(!showSettings)}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>Ultra-Strict Matching Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Confidence Threshold: {(confidenceThreshold * 100).toFixed(0)}%
                  </Typography>
                  <Box sx={{ px: 2 }}>
                    <input
                      type="range"
                      min="0.1"
                      max="1.0"
                      step="0.1"
                      value={confidenceThreshold}
                      onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                      style={{ width: '100%' }}
                    />
                  </Box>
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    type="number"
                    label="Max Results"
                    value={maxResults}
                    onChange={(e) => setMaxResults(parseInt(e.target.value))}
                    inputProps={{ min: 1, max: 50 }}
                    fullWidth
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={autoRefresh}
                        onChange={(e) => setAutoRefresh(e.target.checked)}
                      />
                    }
                    label="Auto Refresh"
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </CardContent>
      </Card>

      {/* Selected Product & Summary */}
      {selectedProduct && (
        <Grid container spacing={4} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Selected Product
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                      {selectedProduct.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {selectedProduct.brand} • {selectedProduct.retailer_code}
                    </Typography>
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                    ฿{selectedProduct.price.toLocaleString()}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {summaryStats && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      Match Summary
                    </Typography>
                    <Button
                      size="small"
                      startIcon={<RefreshIcon />}
                      onClick={handleRefresh}
                      disabled={loadingMatches}
                    >
                      Refresh
                    </Button>
                  </Box>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Total Matches
                      </Typography>
                      <Typography variant="h6">
                        {summaryStats.totalMatches}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Exact Matches
                      </Typography>
                      <Typography variant="h6" sx={{ color: '#4CAF50' }}>
                        {summaryStats.exactMatches}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Avg Confidence
                      </Typography>
                      <Typography variant="h6">
                        {(summaryStats.avgConfidence * 100).toFixed(1)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Better Deals
                      </Typography>
                      <Typography variant="h6" sx={{ color: '#FF9800' }}>
                        {summaryStats.betterDeals}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}

      {/* Match Results */}
      {loadingMatches && (
        <Box sx={{ mb: 4 }}>
          <LinearProgress />
          <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
            Finding ultra-strict matches...
          </Typography>
        </Box>
      )}

      {matchError && (
        <Alert severity="error" sx={{ mb: 4 }}>
          Error finding matches: {String(matchError)}
        </Alert>
      )}

      {matchResults && matchResults.matches.length === 0 && (
        <Alert severity="info" sx={{ mb: 4 }}>
          No ultra-strict matches found for this product. Try reducing the confidence threshold or expanding the search criteria.
        </Alert>
      )}

      {matchResults && matchResults.matches.length > 0 && (
        <Box>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Ultra-Strict Matches ({matchResults.matches.length})
          </Typography>
          
          <Grid container spacing={2}>
            {matchResults.matches.map((result, index) => (
              <Grid item xs={12} key={`${result.matched_product.id}-${index}`}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <UltraStrictPriceComparisonCard
                    result={result}
                    queryProduct={selectedProduct!}
                    onViewDetails={handleViewDetails}
                    onAddToCart={handleAddToCart}
                    showValidationDetails={false}
                  />
                </motion.div>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Processing Info */}
      {matchResults && (
        <Paper sx={{ p: 2, mt: 4, backgroundColor: '#f9f9f9' }}>
          <Typography variant="body2" color="text.secondary">
            Processed {matchResults.total_candidates} candidates in {matchResults.processing_time_ms}ms 
            using {matchResults.matcher_config.type} matcher v{matchResults.matcher_config.version}
          </Typography>
        </Paper>
      )}
      </>
    </Container>
  );
}