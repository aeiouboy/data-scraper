/**
 * Ultra-Strict Price Comparison Card
 * Enhanced price comparison with ultra-strict matching validation
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Grid,
  Button,
  Chip,
  Avatar,
  IconButton,
  Collapse,
  Divider,
  Alert,
  Tooltip,
  LinearProgress
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Launch as LaunchIcon,
  Verified as VerifiedIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  TrendingDown as TrendingDownIcon,
  ShoppingCart as ShoppingCartIcon,
  Info as InfoIcon,
  Star as StarIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import {
  UltraStrictMatchResult,
  ultraStrictMatchingApi
} from '../services/ultraStrictMatchingApi';
import UltraStrictMatchValidationIndicator from './UltraStrictMatchValidationIndicator';

interface UltraStrictPriceComparisonCardProps {
  result: UltraStrictMatchResult;
  queryProduct: {
    id: string;
    name: string;
    brand: string;
    price: number;
    retailer_code: string;
    url: string;
  };
  onViewDetails?: (productId: string) => void;
  onAddToCart?: (productId: string) => void;
  showValidationDetails?: boolean;
  compact?: boolean;
}

const UltraStrictPriceComparisonCard: React.FC<UltraStrictPriceComparisonCardProps> = ({
  result,
  queryProduct,
  onViewDetails,
  onAddToCart,
  showValidationDetails = false,
  compact = false
}) => {
  const [expanded, setExpanded] = useState(showValidationDetails);
  const [showFullDescription, setShowFullDescription] = useState(false);

  const { matched_product, confidence, match_type, price_comparison, ultra_strict_details } = result;
  const matchQuality = ultraStrictMatchingApi.calculateMatchQuality(result);
  const confidenceColor = ultraStrictMatchingApi.getConfidenceColor(confidence, match_type);
  const validationIcon = ultraStrictMatchingApi.getValidationIcon(ultra_strict_details);

  // Get retailer info
  const getRetailerInfo = (retailerCode: string) => {
    const retailers: Record<string, { name: string; color: string; logo?: string }> = {
      'HP': { name: 'HomePro', color: '#FF6B35' },
      'TWD': { name: 'Thai Watsadu', color: '#1976D2' },
      'GH': { name: 'Global House', color: '#4CAF50' },
      'BT': { name: 'Boonthavorn', color: '#9C27B0' },
      'MH': { name: 'Mega Home', color: '#FF9800' },
      'DH': { name: 'DoHome', color: '#795548' }
    };
    return retailers[retailerCode] || { name: retailerCode, color: '#9E9E9E' };
  };

  const queryRetailer = getRetailerInfo(queryProduct.retailer_code);
  const matchedRetailer = getRetailerInfo(matched_product.retailer_code);

  // Calculate savings
  const savings = price_comparison ? price_comparison.savings : 0;
  const isBetterDeal = price_comparison ? price_comparison.is_better_deal : false;

  // Determine overall recommendation
  const getRecommendation = () => {
    if (match_type === 'none' || result.rejection_reasons.length > 0) {
      return { text: 'Not Recommended', color: '#F44336', icon: <ErrorIcon /> };
    }
    if (match_type === 'exact' && isBetterDeal) {
      return { text: 'Highly Recommended', color: '#4CAF50', icon: <VerifiedIcon /> };
    }
    if (match_type === 'high' && savings > 1000) {
      return { text: 'Recommended', color: '#2196F3', icon: <StarIcon /> };
    }
    if (match_type === 'medium' && isBetterDeal) {
      return { text: 'Consider', color: '#FF9800', icon: <InfoIcon /> };
    }
    return { text: 'Review Required', color: '#FF5722', icon: <WarningIcon /> };
  };

  const recommendation = getRecommendation();

  if (compact) {
    return (
      <Card sx={{ mb: 1, border: `2px solid ${confidenceColor}20` }}>
        <CardContent sx={{ py: 1 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Avatar
                  sx={{
                    bgcolor: matchedRetailer.color,
                    width: 32,
                    height: 32,
                    fontSize: '0.8rem'
                  }}
                >
                  {matched_product.retailer_code}
                </Avatar>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    {matched_product.name.length > 50 
                      ? `${matched_product.name.substring(0, 50)}...` 
                      : matched_product.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {matched_product.brand} • {matched_product.sku}
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" sx={{ color: confidenceColor }}>
                  ฿{matched_product.price.toLocaleString()}
                </Typography>
                {savings > 0 && (
                  <Typography variant="body2" sx={{ color: '#4CAF50' }}>
                    Save ฿{savings.toLocaleString()}
                  </Typography>
                )}
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Chip
                  label={`${(confidence * 100).toFixed(1)}%`}
                  size="small"
                  sx={{
                    backgroundColor: `${confidenceColor}20`,
                    color: confidenceColor,
                    fontWeight: 'bold'
                  }}
                />
                <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                  {validationIcon} {match_type.toUpperCase()}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card 
        sx={{ 
          mb: 2, 
          border: `2px solid ${confidenceColor}20`,
          boxShadow: `0 4px 12px ${confidenceColor}20`,
          overflow: 'visible'
        }}
      >
        <CardContent>
          {/* Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar
                sx={{
                  bgcolor: matchedRetailer.color,
                  width: 48,
                  height: 48,
                  fontSize: '1.2rem'
                }}
              >
                {matched_product.retailer_code}
              </Avatar>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  {matchedRetailer.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {matched_product.brand} • {matched_product.sku}
                </Typography>
              </Box>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Chip
                label={recommendation.text}
                icon={recommendation.icon}
                sx={{
                  backgroundColor: `${recommendation.color}20`,
                  color: recommendation.color,
                  fontWeight: 'bold',
                  mb: 1
                }}
              />
              <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary' }}>
                Match Quality: {matchQuality.toFixed(1)}/100
              </Typography>
            </Box>
          </Box>

          {/* Product Name */}
          <Typography 
            variant="body1" 
            sx={{ 
              mb: 2, 
              fontWeight: 'medium',
              cursor: 'pointer',
              '&:hover': { color: 'primary.main' }
            }}
            onClick={() => setShowFullDescription(!showFullDescription)}
          >
            {showFullDescription || matched_product.name.length <= 100
              ? matched_product.name
              : `${matched_product.name.substring(0, 100)}...`}
            {matched_product.name.length > 100 && (
              <IconButton size="small" sx={{ ml: 1 }}>
                <ExpandMoreIcon
                  sx={{
                    transform: showFullDescription ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.3s'
                  }}
                />
              </IconButton>
            )}
          </Typography>

          {/* Price Comparison */}
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={6}>
              <Box sx={{ p: 2, backgroundColor: '#f5f5f5', borderRadius: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  {queryRetailer.name} (Your Query)
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 'bold', color: queryRetailer.color }}>
                  ฿{queryProduct.price.toLocaleString()}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ p: 2, backgroundColor: isBetterDeal ? '#E8F5E8' : '#FFF3E0', borderRadius: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  {matchedRetailer.name} (Match Found)
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 'bold', color: matchedRetailer.color }}>
                  ฿{matched_product.price.toLocaleString()}
                </Typography>
                {savings > 0 && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                    <TrendingDownIcon sx={{ color: '#4CAF50', fontSize: 18 }} />
                    <Typography variant="body2" sx={{ color: '#4CAF50', fontWeight: 'bold' }}>
                      Save ฿{savings.toLocaleString()}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Grid>
          </Grid>

          {/* Confidence Indicator */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                Match Confidence
              </Typography>
              <Typography variant="body2" sx={{ color: confidenceColor, fontWeight: 'bold' }}>
                {validationIcon} {(confidence * 100).toFixed(1)}% ({match_type.toUpperCase()})
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={confidence * 100}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: '#f5f5f5',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: confidenceColor,
                  borderRadius: 4,
                }
              }}
            />
          </Box>

          {/* Quick Validation Summary */}
          <Grid container spacing={1} sx={{ mb: 2 }}>
            <Grid item xs={4}>
              <Box sx={{ textAlign: 'center', p: 1, borderRadius: 1, backgroundColor: '#f9f9f9' }}>
                <Typography variant="caption" color="text.secondary">
                  Model
                </Typography>
                <Typography variant="body2" sx={{ 
                  color: ultra_strict_details.model_exact_match ? '#4CAF50' : '#FF5722',
                  fontWeight: 'bold'
                }}>
                  {ultra_strict_details.model_exact_match ? '✅ Match' : '❌ Different'}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={4}>
              <Box sx={{ textAlign: 'center', p: 1, borderRadius: 1, backgroundColor: '#f9f9f9' }}>
                <Typography variant="caption" color="text.secondary">
                  Brand
                </Typography>
                <Typography variant="body2" sx={{ 
                  color: ultra_strict_details.brand_exact_match ? '#4CAF50' : '#FF5722',
                  fontWeight: 'bold'
                }}>
                  {ultra_strict_details.brand_exact_match ? '✅ Match' : '❌ Different'}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={4}>
              <Box sx={{ textAlign: 'center', p: 1, borderRadius: 1, backgroundColor: '#f9f9f9' }}>
                <Typography variant="caption" color="text.secondary">
                  Specs
                </Typography>
                <Typography variant="body2" sx={{ 
                  color: ultra_strict_details.specification_validation ? '#4CAF50' : '#FF5722',
                  fontWeight: 'bold'
                }}>
                  {ultra_strict_details.specification_validation ? '✅ Valid' : '❌ Invalid'}
                </Typography>
              </Box>
            </Grid>
          </Grid>

          {/* Warnings and Rejections */}
          {(result.warnings.length > 0 || result.rejection_reasons.length > 0) && (
            <Box sx={{ mb: 2 }}>
              {result.warnings.length > 0 && (
                <Alert severity="warning" sx={{ mb: 1 }}>
                  <Typography variant="body2">
                    {result.warnings.join(', ')}
                  </Typography>
                </Alert>
              )}
              {result.rejection_reasons.length > 0 && (
                <Alert severity="error">
                  <Typography variant="body2">
                    {ultraStrictMatchingApi.formatRejectionReasons(result.rejection_reasons)}
                  </Typography>
                </Alert>
              )}
            </Box>
          )}

          {/* Expandable Validation Details */}
          <Collapse in={expanded}>
            <Divider sx={{ mb: 2 }} />
            <UltraStrictMatchValidationIndicator
              result={result}
              showDetails={true}
              compact={false}
            />
          </Collapse>
        </CardContent>

        <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              size="small"
              onClick={() => setExpanded(!expanded)}
              startIcon={<InfoIcon />}
            >
              {expanded ? 'Hide' : 'Show'} Details
            </Button>
            <Tooltip title="View product page">
              <IconButton
                size="small"
                onClick={() => window.open(matched_product.url, '_blank')}
              >
                <LaunchIcon />
              </IconButton>
            </Tooltip>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {onViewDetails && (
              <Button
                variant="outlined"
                size="small"
                onClick={() => onViewDetails(matched_product.id)}
              >
                View Details
              </Button>
            )}
            {onAddToCart && isBetterDeal && (
              <Button
                variant="contained"
                size="small"
                startIcon={<ShoppingCartIcon />}
                onClick={() => onAddToCart(matched_product.id)}
                sx={{ backgroundColor: matchedRetailer.color }}
              >
                Add to Cart
              </Button>
            )}
          </Box>
        </CardActions>
      </Card>
    </motion.div>
  );
};

export default UltraStrictPriceComparisonCard;