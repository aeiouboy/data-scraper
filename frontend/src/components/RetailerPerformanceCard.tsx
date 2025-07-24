import React, { memo } from 'react';
import {
  Card,
  CardContent,
  Avatar,
  Typography,
  Stack,
  Box,
  Divider,
  Grid,
  Chip,
  Fade,
  LinearProgress,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  InfoOutlined as InfoIcon,
  CheckCircle as HealthyIcon,
  Warning as WarningIcon,
  Error as CriticalIcon,
} from '@mui/icons-material';

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

interface RetailerPerformanceCardProps {
  retailer: RetailerStats;
  index: number;
  retailerColor: string;
  onCardClick?: (retailerCode: string) => void;
  showComparison?: boolean;
  comparisonMetrics?: {
    productsChange?: number;
    priceChange?: number;
    coverageChange?: number;
  };
}

const RetailerPerformanceCard: React.FC<RetailerPerformanceCardProps> = memo(({
  retailer,
  index,
  retailerColor,
  onCardClick,
  showComparison = false,
  comparisonMetrics,
}) => {
  const stockRate = retailer.actual_products > 0 
    ? (retailer.in_stock_products / retailer.actual_products) * 100 
    : 0;

  const pricingRate = retailer.actual_products > 0 
    ? (retailer.priced_products / retailer.actual_products) * 100 
    : 0;

  const totalMonitoringProducts = 
    retailer.ultra_critical_count + 
    retailer.high_value_count + 
    retailer.standard_count + 
    retailer.low_priority_count;

  const getHealthStatus = () => {
    if (stockRate >= 90 && pricingRate >= 90) return 'healthy';
    if (stockRate >= 70 && pricingRate >= 70) return 'warning';
    return 'critical';
  };

  const healthStatus = getHealthStatus();
  const healthIcon = {
    healthy: <HealthyIcon color="success" />,
    warning: <WarningIcon color="warning" />,
    critical: <CriticalIcon color="error" />,
  }[healthStatus];

  const getMarketPosition = () => {
    if (retailer.market_position) return retailer.market_position;
    
    // Infer market position from data
    if (retailer.actual_products > 50000) return 'Market Leader';
    if (retailer.actual_products > 20000) return 'Major Retailer';
    if (retailer.actual_products > 5000) return 'Growing Retailer';
    return 'Emerging Retailer';
  };

  const formatLastScraped = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
      
      if (diffHours < 1) return 'Updated recently';
      if (diffHours < 24) return `${diffHours}h ago`;
      return `${Math.floor(diffHours / 24)}d ago`;
    } catch {
      return 'Unknown';
    }
  };

  const getTrendIcon = (change?: number) => {
    if (!change) return null;
    return change > 0 ? 
      <TrendingUpIcon color="success" fontSize="small" /> : 
      <TrendingDownIcon color="error" fontSize="small" />;
  };

  const formatPercentageChange = (change?: number) => {
    if (!change) return '';
    return `${change > 0 ? '+' : ''}${change.toFixed(1)}%`;
  };

  return (
    <Fade in timeout={300 + index * 100}>
      <Card 
        variant="outlined" 
        sx={{ 
          height: '100%',
          cursor: onCardClick ? 'pointer' : 'default',
          transition: 'all 0.2s ease-in-out',
          '&:hover': onCardClick ? {
            transform: 'translateY(-2px)',
            boxShadow: 2,
            borderColor: retailerColor,
          } : {},
          borderLeft: `4px solid ${retailerColor}`,
        }}
        onClick={() => onCardClick?.(retailer.code)}
      >
        <CardContent>
          {/* Header */}
          <Stack direction="row" alignItems="center" spacing={2} mb={2}>
            <Avatar
              sx={{
                bgcolor: retailerColor,
                width: 48,
                height: 48,
                fontWeight: 'bold',
              }}
            >
              {retailer.code}
            </Avatar>
            <Box flex={1}>
              <Stack direction="row" alignItems="center" spacing={1}>
                <Typography variant="h6" fontWeight="bold">
                  {retailer.name}
                </Typography>
                <Tooltip title={`System Health: ${healthStatus}`}>
                  {healthIcon}
                </Tooltip>
              </Stack>
              <Typography variant="caption" color="text.secondary">
                {getMarketPosition()}
              </Typography>
            </Box>
            <Tooltip title="Additional information">
              <IconButton size="small">
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>

          <Divider sx={{ mb: 2 }} />

          {/* Key Metrics */}
          <Grid container spacing={2} mb={2}>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">
                Total Products
              </Typography>
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <Typography variant="h6" fontWeight="bold">
                  {retailer.actual_products.toLocaleString()}
                </Typography>
                {showComparison && getTrendIcon(comparisonMetrics?.productsChange)}
              </Stack>
              {showComparison && comparisonMetrics?.productsChange && (
                <Typography variant="caption" color={comparisonMetrics.productsChange > 0 ? 'success.main' : 'error.main'}>
                  {formatPercentageChange(comparisonMetrics.productsChange)}
                </Typography>
              )}
            </Grid>
            
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">
                In Stock
              </Typography>
              <Typography variant="h6" fontWeight="bold" color="success.main">
                {retailer.in_stock_products.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {stockRate.toFixed(1)}% rate
              </Typography>
            </Grid>
            
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">
                Avg Price
              </Typography>
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <Typography variant="h6" fontWeight="bold">
                  ฿{retailer.avg_price?.toFixed(0) || '0'}
                </Typography>
                {showComparison && getTrendIcon(comparisonMetrics?.priceChange)}
              </Stack>
              {showComparison && comparisonMetrics?.priceChange && (
                <Typography variant="caption" color={comparisonMetrics.priceChange > 0 ? 'error.main' : 'success.main'}>
                  {formatPercentageChange(comparisonMetrics.priceChange)}
                </Typography>
              )}
            </Grid>
            
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">
                Coverage
              </Typography>
              <Stack direction="row" alignItems="center" spacing={0.5}>
                <Typography variant="h6" fontWeight="bold">
                  {retailer.category_coverage_percentage?.toFixed(1) || '0'}%
                </Typography>
                {showComparison && getTrendIcon(comparisonMetrics?.coverageChange)}
              </Stack>
              {showComparison && comparisonMetrics?.coverageChange && (
                <Typography variant="caption" color={comparisonMetrics.coverageChange > 0 ? 'success.main' : 'error.main'}>
                  {formatPercentageChange(comparisonMetrics.coverageChange)}
                </Typography>
              )}
            </Grid>
          </Grid>

          {/* Health Indicators */}
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Data Quality
            </Typography>
            <Stack spacing={1}>
              <Box>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="caption">Stock Rate</Typography>
                  <Typography variant="caption">{stockRate.toFixed(1)}%</Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={stockRate}
                  sx={{
                    height: 4,
                    borderRadius: 2,
                    '& .MuiLinearProgress-bar': {
                      bgcolor: stockRate >= 90 ? 'success.main' : stockRate >= 70 ? 'warning.main' : 'error.main',
                    },
                  }}
                />
              </Box>
              <Box>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="caption">Pricing Rate</Typography>
                  <Typography variant="caption">{pricingRate.toFixed(1)}%</Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={pricingRate}
                  sx={{
                    height: 4,
                    borderRadius: 2,
                    '& .MuiLinearProgress-bar': {
                      bgcolor: pricingRate >= 90 ? 'success.main' : pricingRate >= 70 ? 'warning.main' : 'error.main',
                    },
                  }}
                />
              </Box>
            </Stack>
          </Box>

          {/* Monitoring Tiers */}
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Monitoring Distribution ({totalMonitoringProducts.toLocaleString()})
            </Typography>
            <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
              <Chip
                label={`Ultra: ${retailer.ultra_critical_count}`}
                size="small"
                color="error"
                variant="outlined"
              />
              <Chip
                label={`High: ${retailer.high_value_count}`}
                size="small"
                color="warning"
                variant="outlined"
              />
              <Chip
                label={`Std: ${retailer.standard_count}`}
                size="small"
                color="info"
                variant="outlined"
              />
              <Chip
                label={`Low: ${retailer.low_priority_count}`}
                size="small"
                color="default"
                variant="outlined"
              />
            </Stack>
          </Box>

          {/* Last Updated */}
          <Box>
            <Typography variant="caption" color="text.secondary">
              Last updated: {formatLastScraped(retailer.last_scraped_at)}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Fade>
  );
});

RetailerPerformanceCard.displayName = 'RetailerPerformanceCard';

export default RetailerPerformanceCard;