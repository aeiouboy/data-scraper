import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Button,
  Grid,
  Alert,
  Tooltip,
  Badge,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Switch,
  FormControlLabel,
  Slider,
  TextField
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Settings,
  Refresh,
  CheckCircle,
  Speed,
  Psychology,
  Language,
  Analytics
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  optimizedMatchingApi,
  matchingUtils,
  type OptimizedMatchResult,
} from '../services/optimizedMatchingApi';

interface OptimizedPriceComparisonProps {
  productId: string;
  showConfiguration?: boolean;
  autoRefresh?: boolean;
  minConfidence?: number;
}

export const OptimizedPriceComparison: React.FC<OptimizedPriceComparisonProps> = ({
  productId,
  showConfiguration = false,
  autoRefresh = false,
  minConfidence = 0.3
}) => {
  const [configOpen, setConfigOpen] = useState(false);
  const [useOptimized, setUseOptimized] = useState(true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(minConfidence);
  const [maxResults, setMaxResults] = useState(10);
  const queryClient = useQueryClient();

  // Fetch matching suggestions using optimized algorithm
  const {
    data: suggestions,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['optimized-suggestions', productId, confidenceThreshold, maxResults],
    queryFn: () => optimizedMatchingApi.getSuggestions(productId, maxResults, confidenceThreshold),
    enabled: !!productId && useOptimized,
    refetchInterval: autoRefresh ? 30000 : false, // Refresh every 30 seconds if enabled
  });

  // Fetch service statistics
  const { data: statistics } = useQuery({
    queryKey: ['optimized-statistics'],
    queryFn: () => optimizedMatchingApi.getStatistics(),
    refetchInterval: 60000, // Refresh every minute
  });

  // Clear cache mutation
  const clearCacheMutation = useMutation({
    mutationFn: () => optimizedMatchingApi.clearCache(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['optimized-suggestions'] });
    },
  });

  const matchingData = suggestions?.data;
  const stats = statistics?.data;

  const handleRefresh = () => {
    refetch();
  };

  const handleClearCache = () => {
    clearCacheMutation.mutate();
  };

  const renderConfidenceChip = (match: OptimizedMatchResult) => {
    const color = matchingUtils.getConfidenceColor(match.confidence);
    const label = matchingUtils.getConfidenceLabel(match.confidence);
    const icon = matchingUtils.getActionIcon(match.action_required);

    return (
      <Tooltip title={`${(match.confidence * 100).toFixed(1)}% confidence - ${match.action_required.replace('_', ' ')}`}>
        <Chip
          label={`${icon} ${label}`}
          style={{ backgroundColor: color, color: 'white' }}
          size="small"
        />
      </Tooltip>
    );
  };

  const renderMatchDetails = (match: OptimizedMatchResult) => {
    const savings = matchingData?.product?.price && match.candidate_price
      ? matchingUtils.calculateSavings(matchingData.product.price, match.candidate_price)
      : 0;

    return (
      <Card sx={{ mb: 2, border: `2px solid ${matchingUtils.getConfidenceColor(match.confidence)}` }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box flex={1}>
              <Typography variant="h6" component="div" gutterBottom>
                {match.candidate_name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {match.candidate_brand} • {match.candidate_retailer}
              </Typography>
            </Box>
            <Box textAlign="right">
              {renderConfidenceChip(match)}
              {match.candidate_price && (
                <Typography variant="h6" color="primary" sx={{ mt: 1 }}>
                  {matchingUtils.formatCurrency(match.candidate_price)}
                </Typography>
              )}
              {savings > 0 && (
                <Chip
                  label={`Save ${savings.toFixed(1)}%`}
                  color="success"
                  size="small"
                  icon={<TrendingDown />}
                />
              )}
            </Box>
          </Box>

          {/* Match Quality Indicators */}
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Match Quality:
            </Typography>
            <Grid container spacing={1}>
              {Object.entries(match.details).map(([key, value]) => {
                const numValue = typeof value === 'number' ? value : 0;
                return (
                  <Grid item xs={6} sm={4} md={2} key={key}>
                    <Box textAlign="center">
                      <Typography variant="caption" display="block">
                        {key.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={numValue * 100}
                        color={numValue > 0.8 ? 'success' : numValue > 0.5 ? 'warning' : 'error'}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="caption">
                        {(numValue * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                  </Grid>
                );
              })}
            </Grid>
          </Box>

          {/* Matched Fields */}
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Matched Fields:
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {match.matched_fields.map((field) => (
                <Chip key={field} label={field} size="small" variant="outlined" />
              ))}
            </Box>
          </Box>

          {/* Tier Information */}
          <Box display="flex" alignItems="center" gap={1}>
            <Chip
              label={`Tier: ${match.details.tier}`}
              size="small"
              color="info"
            />
            <Chip
              label={matchingUtils.formatMatchType(match.match_type)}
              size="small"
              variant="outlined"
            />
          </Box>

          {/* Warnings */}
          {match.warnings.length > 0 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              <Typography variant="body2">
                {match.warnings.join(', ')}
              </Typography>
            </Alert>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderSummary = () => {
    if (!matchingData?.summary) return null;

    const { summary } = matchingData;

    return (
      <Card sx={{ mb: 3, bgcolor: 'primary.main', color: 'white' }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Match Summary
            </Typography>
            <Badge badgeContent={summary.total_matches} color="secondary">
              <CheckCircle />
            </Badge>
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Typography variant="body2" gutterBottom>
                Best Match
              </Typography>
              <Typography variant="h6">
                {(summary.best_confidence * 100).toFixed(1)}%
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="body2" gutterBottom>
                Quality
              </Typography>
              <Typography variant="h6">
                {summary.match_quality}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="body2" gutterBottom>
                High Confidence
              </Typography>
              <Typography variant="h6">
                {summary.confidence_distribution.high}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="body2" gutterBottom>
                Cache Hit
              </Typography>
              <Typography variant="h6">
                {matchingData.metadata.cache_hit ? '✅' : '❌'}
              </Typography>
            </Grid>
          </Grid>

          <Typography variant="body2" sx={{ mt: 2, fontStyle: 'italic' }}>
            💡 {summary.recommendation}
          </Typography>
        </CardContent>
      </Card>
    );
  };

  const renderOptimizationFeatures = () => (
    <Card sx={{ mb: 3, bgcolor: 'success.light', color: 'white' }}>
      <CardContent>
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <Psychology />
          <Typography variant="h6">
            Optimized Matching Features
          </Typography>
        </Box>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Box display="flex" alignItems="center" gap={1}>
              <Speed fontSize="small" />
              <Typography variant="body2">
                Progressive Matching
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box display="flex" alignItems="center" gap={1}>
              <Language fontSize="small" />
              <Typography variant="body2">
                Thai-English Support
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box display="flex" alignItems="center" gap={1}>
              <Analytics fontSize="small" />
              <Typography variant="body2">
                Multiple Algorithms
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box display="flex" alignItems="center" gap={1}>
              <TrendingUp fontSize="small" />
              <Typography variant="body2">
                50% Better Accuracy
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {stats?.statistics && (
          <Typography variant="body2" sx={{ mt: 1 }}>
            Enhanced with {stats.statistics.matcher_info.enhanced_brands} brand variations • 
            Cache: {stats.statistics.cache_size} items • 
            {stats.statistics.matcher_info.progressive_tiers.length} matching tiers
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  const renderConfiguration = () => (
    <Dialog open={configOpen} onClose={() => setConfigOpen(false)} maxWidth="sm" fullWidth>
      <DialogTitle>Matching Configuration</DialogTitle>
      <DialogContent>
        <Box py={2}>
          <FormControlLabel
            control={
              <Switch
                checked={useOptimized}
                onChange={(e) => setUseOptimized(e.target.checked)}
              />
            }
            label="Use Optimized Matching Algorithm"
          />

          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {matchingUtils.getImprovementMessage(useOptimized)}
          </Typography>

          <Typography gutterBottom>
            Confidence Threshold: {(confidenceThreshold * 100).toFixed(0)}%
          </Typography>
          <Slider
            value={confidenceThreshold}
            onChange={(_, value) => setConfidenceThreshold(value as number)}
            min={0.1}
            max={0.9}
            step={0.05}
            marks
            valueLabelDisplay="auto"
            valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
          />

          <TextField
            label="Maximum Results"
            type="number"
            value={maxResults}
            onChange={(e) => setMaxResults(parseInt(e.target.value) || 10)}
            fullWidth
            margin="normal"
            inputProps={{ min: 1, max: 50 }}
          />

          {stats?.statistics && (
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                Current configuration: {stats.statistics.configuration.batch_size} batch size, 
                {stats.statistics.configuration.max_workers} workers, 
                {stats.statistics.configuration.cache_duration}s cache duration
              </Typography>
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setConfigOpen(false)}>Cancel</Button>
        <Button variant="contained" onClick={() => setConfigOpen(false)}>
          Apply
        </Button>
      </DialogActions>
    </Dialog>
  );

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <LinearProgress sx={{ flex: 1 }} />
            <Typography variant="body2">
              Finding optimized matches...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" onClick={handleRefresh}>
          Retry
        </Button>
      }>
        Failed to load matching suggestions: {error && typeof error === 'object' && 'message' in error ? String(error.message) : 'Unknown error'}
      </Alert>
    );
  }

  if (!matchingData?.suggestions?.length) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">
            No matches found with current confidence threshold ({(confidenceThreshold * 100).toFixed(0)}%).
            Try lowering the threshold or check product data quality.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      {/* Header with controls */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          🚀 Optimized Price Comparison
        </Typography>
        <Box display="flex" gap={1}>
          <Tooltip title="Refresh matches">
            <IconButton onClick={handleRefresh} disabled={isLoading}>
              <Refresh />
            </IconButton>
          </Tooltip>
          <Tooltip title="Clear cache">
            <IconButton onClick={handleClearCache} disabled={clearCacheMutation.isPending}>
              <Speed />
            </IconButton>
          </Tooltip>
          {showConfiguration && (
            <Tooltip title="Configure matching">
              <IconButton onClick={() => setConfigOpen(true)}>
                <Settings />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      {/* Optimization features banner */}
      {renderOptimizationFeatures()}

      {/* Summary */}
      {renderSummary()}

      {/* Product matches */}
      <Typography variant="h6" gutterBottom>
        Found {matchingData.suggestions.length} matches
      </Typography>

      {matchingData.suggestions.map((match, index) => (
        <Box key={match.candidate_id || index}>
          {renderMatchDetails(match)}
        </Box>
      ))}

      {/* Configuration dialog */}
      {renderConfiguration()}

      {/* Footer with metadata */}
      <Card sx={{ mt: 3, bgcolor: 'grey.50' }}>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            Processed {matchingData.metadata.total_candidates} candidates • 
            Found {matchingData.metadata.total_matches} potential matches • 
            Filtered to {matchingData.metadata.filtered_matches} results • 
            {matchingData.metadata.cache_hit ? 'From cache' : 'Fresh results'}
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default OptimizedPriceComparison;