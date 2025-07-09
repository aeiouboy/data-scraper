import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  Stack,
  Avatar,
  Button,
  Tab,
  Tabs,
  Chip,
  Alert,
  LinearProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  TrendingDown as SavingsIcon,
  AutoFixHigh as MatchIcon,
  CheckCircle as ConfirmIcon,
  Cancel as RejectIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Analytics as AnalyticsIcon,
  CompareArrows as CompareIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from 'recharts';
import { matchingApi, productApi, priceComparisonApi } from '../services/api';
import { useRetailer } from '../contexts/RetailerContext';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`price-tracking-tabpanel-${index}`}
      aria-labelledby={`price-tracking-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

interface MatchSuggestion {
  product: {
    id: string;
    name: string;
    brand?: string;
    retailer: string;
    price?: number;
    url: string;
  };
  match_confidence: number;
  match_details: {
    name_similarity: number;
    sku_match: boolean;
    brand_match: number;
    spec_match: number;
  };
}

export default function PriceTrackingDashboard() {
  const queryClient = useQueryClient();
  const { selectedRetailers, multiRetailerMode } = useRetailer();
  const [activeTab, setActiveTab] = useState(0);
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [matchDialogOpen, setMatchDialogOpen] = useState(false);
  const [testMatchDialog, setTestMatchDialog] = useState(false);
  const [testMatchData, setTestMatchData] = useState({
    product1_name: '',
    product2_name: '',
    brand1: '',
    brand2: '',
  });

  // Fetch matching analytics
  const { data: analyticsData, isLoading: loadingAnalytics, refetch: refetchAnalytics } = useQuery({
    queryKey: ['matching-analytics'],
    queryFn: async () => {
      try {
        const response = await matchingApi.getAnalytics();
        return response.data;
      } catch (error) {
        console.error('Analytics error:', error);
        return null;
      }
    },
    enabled: multiRetailerMode,
  });

  // Process new products mutation
  const processProductsMutation = useMutation({
    mutationFn: async (params: { retailer_codes?: string[]; limit?: number }) => {
      return await matchingApi.processNewProducts(params);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matching-analytics'] });
    },
  });

  // Test match mutation
  const testMatchMutation = useMutation({
    mutationFn: async (data: typeof testMatchData) => {
      return await matchingApi.testMatch(data);
    },
  });

  // Confirm match mutation
  const confirmMatchMutation = useMutation({
    mutationFn: async (data: {
      product1_id: string;
      product2_id: string;
      is_match: boolean;
      confidence_override?: number;
    }) => {
      return await matchingApi.confirmMatch(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['match-suggestions'] });
      setMatchDialogOpen(false);
    },
  });

  // Get match suggestions for selected product
  const { data: matchSuggestions, isLoading: loadingSuggestions } = useQuery({
    queryKey: ['match-suggestions', selectedProduct?.id],
    queryFn: async () => {
      if (!selectedProduct?.id) return null;
      const response = await matchingApi.getMatchSuggestions(selectedProduct.id, 0.5);
      return response.data;
    },
    enabled: !!selectedProduct?.id && matchDialogOpen,
  });

  const handleProcessNewProducts = () => {
    processProductsMutation.mutate({
      retailer_codes: selectedRetailers,
      limit: 100,
    });
  };

  const handleTestMatch = () => {
    testMatchMutation.mutate(testMatchData);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'success';
    if (confidence >= 0.7) return 'warning';
    return 'error';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.9) return 'EXACT MATCH';
    if (confidence >= 0.7) return 'LIKELY MATCH';
    if (confidence >= 0.5) return 'POSSIBLE MATCH';
    return 'NO MATCH';
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        🎯 Price Tracking Dashboard
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <MatchIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {analyticsData?.match_statistics?.total_products_matched || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Products Matched
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
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <SavingsIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {analyticsData?.match_statistics?.average_price_variance?.toFixed(1) || 0}%
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
                  <TimelineIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {analyticsData?.manual_review_stats?.accuracy_rate?.toFixed(0) || 0}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Match Accuracy
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
                  <AnalyticsIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">
                    {Object.keys(analyticsData?.match_statistics?.retailer_coverage || {}).length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Retailers Covered
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Action Buttons */}
      <Stack direction="row" spacing={2} mb={3}>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={handleProcessNewProducts}
          disabled={processProductsMutation.isPending}
        >
          Process New Products
        </Button>
        <Button
          variant="outlined"
          startIcon={<SearchIcon />}
          onClick={() => setTestMatchDialog(true)}
        >
          Test Product Match
        </Button>
        <Button
          variant="outlined"
          startIcon={<AnalyticsIcon />}
          onClick={() => refetchAnalytics()}
        >
          Refresh Analytics
        </Button>
      </Stack>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
          <Tab label="Match Overview" />
          <Tab label="Price Trends" />
          <Tab label="Savings Opportunities" />
          <Tab label="Manual Review" />
        </Tabs>

        <TabPanel value={activeTab} index={0}>
          {/* Match Overview */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Confidence Distribution
                </Typography>
                {analyticsData?.confidence_distribution && (
                  <Box>
                    <Stack spacing={2}>
                      <Box>
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                          <Typography variant="body2">High Confidence (80%+)</Typography>
                          <Chip
                            label={analyticsData.confidence_distribution.high_confidence}
                            color="success"
                            size="small"
                          />
                        </Stack>
                        <LinearProgress
                          variant="determinate"
                          value={(analyticsData.confidence_distribution.high_confidence / 
                            (analyticsData.manual_review_stats?.total_reviews || 1)) * 100}
                          sx={{ mt: 1, height: 8, borderRadius: 1 }}
                          color="success"
                        />
                      </Box>
                      <Box>
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                          <Typography variant="body2">Medium Confidence (50-80%)</Typography>
                          <Chip
                            label={analyticsData.confidence_distribution.medium_confidence}
                            color="warning"
                            size="small"
                          />
                        </Stack>
                        <LinearProgress
                          variant="determinate"
                          value={(analyticsData.confidence_distribution.medium_confidence / 
                            (analyticsData.manual_review_stats?.total_reviews || 1)) * 100}
                          sx={{ mt: 1, height: 8, borderRadius: 1 }}
                          color="warning"
                        />
                      </Box>
                      <Box>
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                          <Typography variant="body2">Low Confidence (&lt;50%)</Typography>
                          <Chip
                            label={analyticsData.confidence_distribution.low_confidence}
                            color="error"
                            size="small"
                          />
                        </Stack>
                        <LinearProgress
                          variant="determinate"
                          value={(analyticsData.confidence_distribution.low_confidence / 
                            (analyticsData.manual_review_stats?.total_reviews || 1)) * 100}
                          sx={{ mt: 1, height: 8, borderRadius: 1 }}
                          color="error"
                        />
                      </Box>
                    </Stack>
                  </Box>
                )}
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Manual Review Stats
                </Typography>
                {analyticsData?.manual_review_stats && (
                  <Stack spacing={2}>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography variant="body2">Total Reviews</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {analyticsData.manual_review_stats.total_reviews}
                      </Typography>
                    </Stack>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography variant="body2">Confirmed Matches</Typography>
                      <Typography variant="body2" color="success.main" fontWeight="bold">
                        {analyticsData.manual_review_stats.confirmed_matches}
                      </Typography>
                    </Stack>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography variant="body2">Rejected Matches</Typography>
                      <Typography variant="body2" color="error.main" fontWeight="bold">
                        {analyticsData.manual_review_stats.rejected_matches}
                      </Typography>
                    </Stack>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography variant="body2">Accuracy Rate</Typography>
                      <Typography variant="body2" color="primary.main" fontWeight="bold">
                        {analyticsData.manual_review_stats.accuracy_rate?.toFixed(1)}%
                      </Typography>
                    </Stack>
                  </Stack>
                )}
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {/* Price Trends */}
          <Alert severity="info" sx={{ mb: 2 }}>
            Price trend visualization will show historical price data for matched products across retailers.
          </Alert>
          
          {analyticsData?.top_savings_opportunities && analyticsData.top_savings_opportunities.length > 0 && (
            <Box sx={{ height: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={analyticsData.top_savings_opportunities.slice(0, 10)}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="product_name" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <RechartsTooltip />
                  <Area
                    type="monotone"
                    dataKey="savings_amount"
                    stroke="#8884d8"
                    fill="#8884d8"
                    name="Savings Amount (฿)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          {/* Savings Opportunities */}
          {analyticsData?.top_savings_opportunities && (
            <Grid container spacing={2}>
              {analyticsData.top_savings_opportunities.slice(0, 6).map((opp: any, index: number) => (
                <Grid item xs={12} md={6} key={index}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                        {opp.product_name}
                      </Typography>
                      <Stack spacing={1}>
                        <Stack direction="row" justifyContent="space-between">
                          <Typography variant="body2" color="text.secondary">Category</Typography>
                          <Chip label={opp.category} size="small" />
                        </Stack>
                        <Stack direction="row" justifyContent="space-between">
                          <Typography variant="body2" color="text.secondary">Price Range</Typography>
                          <Typography variant="body2">{opp.price_range}</Typography>
                        </Stack>
                        <Stack direction="row" justifyContent="space-between">
                          <Typography variant="body2" color="text.secondary">Savings</Typography>
                          <Typography variant="body2" color="success.main" fontWeight="bold">
                            ฿{opp.savings_amount.toFixed(2)}
                          </Typography>
                        </Stack>
                        <Stack direction="row" justifyContent="space-between">
                          <Typography variant="body2" color="text.secondary">Best Retailer</Typography>
                          <Chip
                            label={opp.best_retailer}
                            size="small"
                            color="primary"
                          />
                        </Stack>
                        <Stack direction="row" justifyContent="space-between">
                          <Typography variant="body2" color="text.secondary">Price Variance</Typography>
                          <Typography
                            variant="body2"
                            color={opp.variance_percentage > 20 ? 'error.main' : 'warning.main'}
                            fontWeight="bold"
                          >
                            {opp.variance_percentage.toFixed(1)}%
                          </Typography>
                        </Stack>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          {/* Manual Review */}
          <Alert severity="info" sx={{ mb: 2 }}>
            Select a product from your catalog to review and confirm matches with products from other retailers.
          </Alert>
          
          <Button
            variant="outlined"
            onClick={() => {
              // In a real implementation, this would open a product selector
              setSelectedProduct({ id: 'sample-product-id', name: 'Sample Product' });
              setMatchDialogOpen(true);
            }}
          >
            Select Product for Review
          </Button>
        </TabPanel>
      </Paper>

      {/* Test Match Dialog */}
      <Dialog open={testMatchDialog} onClose={() => setTestMatchDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Test Product Matching</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 2 }}>
            <TextField
              label="Product 1 Name"
              fullWidth
              value={testMatchData.product1_name}
              onChange={(e) => setTestMatchData({ ...testMatchData, product1_name: e.target.value })}
              placeholder="e.g., MITSUBISHI แอร์ติดผนัง รุ่น MSY-KP13VF 12000BTU"
            />
            <TextField
              label="Product 1 Brand (Optional)"
              fullWidth
              value={testMatchData.brand1}
              onChange={(e) => setTestMatchData({ ...testMatchData, brand1: e.target.value })}
              placeholder="e.g., MITSUBISHI"
            />
            <TextField
              label="Product 2 Name"
              fullWidth
              value={testMatchData.product2_name}
              onChange={(e) => setTestMatchData({ ...testMatchData, product2_name: e.target.value })}
              placeholder="e.g., มิตซูบิชิ เครื่องปรับอากาศ MSY-KP13VF 12,000 บีทียู"
            />
            <TextField
              label="Product 2 Brand (Optional)"
              fullWidth
              value={testMatchData.brand2}
              onChange={(e) => setTestMatchData({ ...testMatchData, brand2: e.target.value })}
              placeholder="e.g., มิตซูบิชิ"
            />
            
            {testMatchMutation.data && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Stack spacing={2}>
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Chip
                      label={getConfidenceLabel(testMatchMutation.data.data.confidence_score)}
                      color={getConfidenceColor(testMatchMutation.data.data.confidence_score)}
                    />
                    <Typography variant="h6">
                      {(testMatchMutation.data.data.confidence_score * 100).toFixed(1)}% Confidence
                    </Typography>
                  </Stack>
                  
                  <Typography variant="body2">
                    {testMatchMutation.data.data.recommendation}
                  </Typography>
                  
                  <Stack spacing={1}>
                    <Typography variant="body2">
                      Name Similarity: {(testMatchMutation.data.data.details.name_similarity * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2">
                      Brand Match: {testMatchMutation.data.data.details.brand_match > 0.8 ? '✅' : '❌'}
                    </Typography>
                    <Typography variant="body2">
                      SKU Match: {testMatchMutation.data.data.details.sku_match === 1 ? '✅' : '❌'}
                    </Typography>
                    <Typography variant="body2">
                      Spec Match: {(testMatchMutation.data.data.details.spec_match * 100).toFixed(1)}%
                    </Typography>
                  </Stack>
                  
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Normalized Text 1: {testMatchMutation.data.data.details.normalized_name1}
                    </Typography>
                    <br />
                    <Typography variant="caption" color="text.secondary">
                      Normalized Text 2: {testMatchMutation.data.data.details.normalized_name2}
                    </Typography>
                  </Box>
                </Stack>
              </Paper>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestMatchDialog(false)}>Close</Button>
          <Button
            onClick={handleTestMatch}
            variant="contained"
            disabled={!testMatchData.product1_name || !testMatchData.product2_name || testMatchMutation.isPending}
          >
            Test Match
          </Button>
        </DialogActions>
      </Dialog>

      {/* Match Review Dialog */}
      <Dialog open={matchDialogOpen} onClose={() => setMatchDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          Review Product Matches: {selectedProduct?.name}
        </DialogTitle>
        <DialogContent>
          {loadingSuggestions ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : matchSuggestions?.suggestions ? (
            <Stack spacing={2} sx={{ mt: 2 }}>
              {matchSuggestions.suggestions.map((suggestion: MatchSuggestion, index: number) => (
                <Card key={index} variant="outlined">
                  <CardContent>
                    <Grid container spacing={2} alignItems="center">
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {suggestion.product.name}
                        </Typography>
                        <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                          <Chip label={suggestion.product.retailer} size="small" />
                          {suggestion.product.brand && (
                            <Chip label={suggestion.product.brand} size="small" variant="outlined" />
                          )}
                        </Stack>
                        {suggestion.product.price && (
                          <Typography variant="body2" sx={{ mt: 1 }}>
                            Price: ฿{suggestion.product.price.toFixed(2)}
                          </Typography>
                        )}
                      </Grid>
                      <Grid item xs={12} md={4}>
                        <Stack spacing={1}>
                          <Chip
                            label={`${(suggestion.match_confidence * 100).toFixed(1)}% Match`}
                            color={getConfidenceColor(suggestion.match_confidence)}
                          />
                          <Typography variant="caption" color="text.secondary">
                            Name: {(suggestion.match_details.name_similarity * 100).toFixed(0)}% |
                            Brand: {suggestion.match_details.brand_match > 0.8 ? '✅' : '❌'} |
                            SKU: {suggestion.match_details.sku_match ? '✅' : '❌'} |
                            Spec: {(suggestion.match_details.spec_match * 100).toFixed(0)}%
                          </Typography>
                        </Stack>
                      </Grid>
                      <Grid item xs={12} md={2}>
                        <Stack direction="row" spacing={1}>
                          <Tooltip title="Confirm Match">
                            <IconButton
                              color="success"
                              onClick={() => {
                                confirmMatchMutation.mutate({
                                  product1_id: selectedProduct.id,
                                  product2_id: suggestion.product.id,
                                  is_match: true,
                                  confidence_override: suggestion.match_confidence,
                                });
                              }}
                            >
                              <ConfirmIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Reject Match">
                            <IconButton
                              color="error"
                              onClick={() => {
                                confirmMatchMutation.mutate({
                                  product1_id: selectedProduct.id,
                                  product2_id: suggestion.product.id,
                                  is_match: false,
                                });
                              }}
                            >
                              <RejectIcon />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              ))}
            </Stack>
          ) : (
            <Alert severity="info">No match suggestions found for this product.</Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMatchDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Process Status */}
      {processProductsMutation.isPending && (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Stack direction="row" alignItems="center" spacing={2}>
            <CircularProgress size={20} />
            <Typography>Processing new products for matching...</Typography>
          </Stack>
        </Alert>
      )}
      
      {processProductsMutation.isSuccess && (
        <Alert severity="success" sx={{ mt: 2 }}>
          Successfully queued products for matching. Check back in a few moments for results.
        </Alert>
      )}
    </Box>
  );
}