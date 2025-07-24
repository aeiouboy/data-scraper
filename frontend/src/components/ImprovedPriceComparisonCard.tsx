import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Button,
  Grid,
  Avatar,
  IconButton,
  Tooltip,
  Collapse,
  LinearProgress,
  Stack,
  Divider,
  useTheme,
  alpha,
} from '@mui/material';
import {
  TrendingDown,
  CheckCircle,
  InfoOutlined,
  ExpandMore,
  ExpandLess,
  CompareArrows,
  Verified,
  ShoppingCart,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

interface RetailerPrice {
  retailer_code: string;
  retailer_name: string;
  price: number;
  url?: string;
  in_stock?: boolean;
  last_updated?: string;
}

interface ImprovedPriceComparisonCardProps {
  productName: string;
  productImage?: string;
  category: string;
  brand: string;
  retailers: RetailerPrice[];
  bestRetailerCode: string;
  savingsAmount: number;
  savingsPercentage: number;
  matchConfidence: number;
  matchDetails?: {
    sku_score: number;
    brand_score: number;
    name_score: number;
    spec_score: number;
    match_confidence?: number;
    match_type?: string;
    rejection_reasons?: string[];
    warnings?: string[];
    matched_fields?: string[];
  };
  onCompare?: () => void;
  onViewDetails?: () => void;
}

// Enhanced retailer information
const retailerInfo: Record<string, { name: string; color: string; logo?: string }> = {
  'HP': { name: 'HomePro', color: '#FF6B35' },
  'TWD': { name: 'Thai Watsadu', color: '#1976D2' },
  'GH': { name: 'Global House', color: '#4CAF50' },
  'DH': { name: 'DoHome', color: '#FF9800' },
  'BT': { name: 'Boonthavorn', color: '#9C27B0' },
  'MH': { name: 'MegaHome', color: '#E91E63' },
};

const ImprovedPriceComparisonCard: React.FC<ImprovedPriceComparisonCardProps> = ({
  productName,
  productImage,
  category,
  brand,
  retailers,
  bestRetailerCode,
  savingsAmount,
  savingsPercentage,
  matchConfidence,
  matchDetails,
  onCompare,
  onViewDetails,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [hovering, setHovering] = useState(false);
  const theme = useTheme();

  // Get confidence color and label
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.85) return theme.palette.success.main;
    if (confidence >= 0.65) return theme.palette.info.main;
    if (confidence >= 0.45) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.85) return 'Excellent Match';
    if (confidence >= 0.65) return 'Good Match';
    if (confidence >= 0.45) return 'Fair Match';
    return 'Low Match';
  };

  const confidenceColor = getConfidenceColor(matchConfidence);

  // Sort retailers by price
  const sortedRetailers = [...retailers].sort((a, b) => a.price - b.price);
  const lowestPrice = sortedRetailers[0]?.price || 0;
  const highestPrice = sortedRetailers[sortedRetailers.length - 1]?.price || 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.02 }}
      onHoverStart={() => setHovering(true)}
      onHoverEnd={() => setHovering(false)}
    >
      <Card
        sx={{
          position: 'relative',
          overflow: 'visible',
          border: `2px solid ${hovering ? confidenceColor : 'transparent'}`,
          boxShadow: hovering ? theme.shadows[8] : theme.shadows[2],
          transition: 'all 0.3s ease-in-out',
          background: hovering
            ? `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${alpha(
                confidenceColor,
                0.05
              )} 100%)`
            : theme.palette.background.paper,
        }}
      >
        {/* Confidence Badge */}
        <Box
          sx={{
            position: 'absolute',
            top: -10,
            right: 20,
            zIndex: 1,
          }}
        >
          <motion.div
            animate={{ rotate: hovering ? 360 : 0 }}
            transition={{ duration: 0.5 }}
          >
            <Avatar
              sx={{
                bgcolor: confidenceColor,
                width: 60,
                height: 60,
                boxShadow: theme.shadows[4],
              }}
            >
              <Stack alignItems="center" spacing={0}>
                <Typography variant="caption" sx={{ fontSize: '10px', fontWeight: 'bold' }}>
                  {(matchConfidence * 100).toFixed(0)}%
                </Typography>
                <CheckCircle sx={{ fontSize: 20 }} />
              </Stack>
            </Avatar>
          </motion.div>
        </Box>

        <CardContent sx={{ pb: 1 }}>
          {/* Product Header */}
          <Grid container spacing={2} alignItems="flex-start">
            <Grid item xs={12} md={8}>
              <Typography
                variant="h6"
                gutterBottom
                sx={{
                  fontWeight: 600,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                }}
              >
                {productName}
              </Typography>
              
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
                <Chip
                  label={brand}
                  size="small"
                  icon={<Verified />}
                  sx={{ fontWeight: 500 }}
                />
                <Chip
                  label={category}
                  size="small"
                  variant="outlined"
                  sx={{ fontWeight: 500 }}
                />
                <Tooltip title={getConfidenceLabel(matchConfidence)}>
                  <Chip
                    label={getConfidenceLabel(matchConfidence)}
                    size="small"
                    sx={{
                      bgcolor: alpha(confidenceColor, 0.15),
                      color: confidenceColor,
                      fontWeight: 600,
                    }}
                  />
                </Tooltip>
              </Stack>
            </Grid>

            <Grid item xs={12} md={4}>
              {/* Animated Savings Display */}
              <motion.div
                animate={{
                  scale: hovering ? [1, 1.1, 1] : 1,
                }}
                transition={{
                  duration: 0.5,
                  repeat: hovering ? Infinity : 0,
                  repeatDelay: 1,
                }}
              >
                <Box
                  sx={{
                    background: `linear-gradient(135deg, ${theme.palette.success.main} 0%, ${theme.palette.success.dark} 100%)`,
                    borderRadius: 2,
                    p: 2,
                    color: 'white',
                    textAlign: 'center',
                    boxShadow: theme.shadows[4],
                  }}
                >
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    ฿{savingsAmount.toLocaleString()}
                  </Typography>
                  <Stack direction="row" alignItems="center" justifyContent="center" spacing={0.5}>
                    <TrendingDown />
                    <Typography variant="subtitle2">
                      Save {savingsPercentage.toFixed(1)}%
                    </Typography>
                  </Stack>
                </Box>
              </motion.div>
            </Grid>
          </Grid>

          {/* Price Range Visualization */}
          <Box sx={{ my: 3 }}>
            <Stack direction="row" justifyContent="space-between" sx={{ mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Price Range
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                ฿{lowestPrice.toLocaleString()} - ฿{highestPrice.toLocaleString()}
              </Typography>
            </Stack>
            <Box sx={{ position: 'relative', height: 40 }}>
              <LinearProgress
                variant="determinate"
                value={100}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 4,
                    background: `linear-gradient(90deg, ${theme.palette.success.main} 0%, ${theme.palette.error.main} 100%)`,
                  },
                }}
              />
              {/* Retailer Price Points */}
              {sortedRetailers.map((retailer, index) => {
                const position =
                  ((retailer.price - lowestPrice) / (highestPrice - lowestPrice)) * 100;
                return (
                  <Tooltip
                    key={`${retailer.retailer_code}-${index}-${retailer.price}`}
                    title={`${retailerInfo[retailer.retailer_code]?.name || retailer.retailer_code}: ฿${retailer.price.toLocaleString()}`}
                  >
                    <Avatar
                      sx={{
                        position: 'absolute',
                        top: -4,
                        left: `${position}%`,
                        transform: 'translateX(-50%)',
                        width: 32,
                        height: 32,
                        bgcolor: retailerInfo[retailer.retailer_code]?.color || '#666',
                        fontSize: 12,
                        fontWeight: 'bold',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        '&:hover': {
                          transform: 'translateX(-50%) scale(1.2)',
                          zIndex: 10,
                        },
                      }}
                    >
                      {retailer.retailer_code}
                    </Avatar>
                  </Tooltip>
                );
              })}
            </Box>
          </Box>

          {/* Retailer Prices Grid */}
          <Grid container spacing={2} sx={{ mb: 2 }}>
            {sortedRetailers.slice(0, expanded ? undefined : 3).map((retailer, index) => (
              <Grid item xs={12} sm={6} md={4} key={`retailer-${retailer.retailer_code}-${index}-${retailer.price}`}>
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      border: `1px solid ${
                        retailer.retailer_code === bestRetailerCode
                          ? theme.palette.success.main
                          : theme.palette.divider
                      }`,
                      bgcolor:
                        retailer.retailer_code === bestRetailerCode
                          ? alpha(theme.palette.success.main, 0.1)
                          : 'background.paper',
                      position: 'relative',
                      overflow: 'hidden',
                    }}
                  >
                    {retailer.retailer_code === bestRetailerCode && (
                      <Chip
                        label="BEST PRICE"
                        size="small"
                        color="success"
                        sx={{
                          position: 'absolute',
                          top: 4,
                          right: 4,
                          fontSize: '10px',
                          height: 20,
                        }}
                      />
                    )}
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <Avatar
                        sx={{
                          bgcolor: retailerInfo[retailer.retailer_code]?.color || '#666',
                          width: 36,
                          height: 36,
                        }}
                      >
                        {retailer.retailer_code}
                      </Avatar>
                      <Box flex={1}>
                        <Typography variant="caption" color="text.secondary">
                          {retailerInfo[retailer.retailer_code]?.name || retailer.retailer_code}
                        </Typography>
                        <Typography variant="h6" fontWeight="bold">
                          ฿{retailer.price.toLocaleString()}
                        </Typography>
                      </Box>
                    </Stack>
                  </Box>
                </motion.div>
              </Grid>
            ))}
          </Grid>

          {/* Show More/Less Button */}
          {retailers.length > 3 && (
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <Button
                size="small"
                onClick={() => setExpanded(!expanded)}
                endIcon={expanded ? <ExpandLess /> : <ExpandMore />}
                sx={{ textTransform: 'none' }}
              >
                {expanded ? 'Show Less' : `Show ${retailers.length - 3} More Retailers`}
              </Button>
            </Box>
          )}

          {/* Match Details (Collapsible) */}
          <Collapse in={expanded && !!matchDetails}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
              Match Quality Details
            </Typography>
            
            {/* Show rejection reasons if any */}
            {matchDetails?.rejection_reasons && matchDetails.rejection_reasons.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="error" fontWeight="bold">
                  Match Rejected:
                </Typography>
                {matchDetails.rejection_reasons.map((reason, index) => (
                  <Typography key={`rejection-${index}-${reason}`} variant="body2" color="error" sx={{ ml: 1 }}>
                    • {reason}
                  </Typography>
                ))}
              </Box>
            )}

            {/* Show warnings if any */}
            {matchDetails?.warnings && matchDetails.warnings.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="warning.main" fontWeight="bold">
                  Warnings:
                </Typography>
                {matchDetails.warnings.map((warning, index) => (
                  <Typography key={`warning-${index}-${warning}`} variant="body2" color="warning.main" sx={{ ml: 1 }}>
                    • {warning}
                  </Typography>
                ))}
              </Box>
            )}

            {/* Show matched fields */}
            {matchDetails?.matched_fields && matchDetails.matched_fields.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Matched Fields:
                </Typography>
                <Stack direction="row" spacing={0.5} flexWrap="wrap">
                  {matchDetails.matched_fields.map((field) => (
                    <Chip
                      key={field}
                      label={field}
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  ))}
                </Stack>
              </Box>
            )}

            {/* Score breakdown */}
            <Grid container spacing={1}>
              {matchDetails &&
                Object.entries(matchDetails)
                  .filter(([key]) => key.endsWith('_score'))
                  .map(([key, value]) => {
                    const numValue = typeof value === 'number' ? value : 0;
                    return (
                      <Grid item xs={6} sm={3} key={key}>
                        <Box sx={{ textAlign: 'center', p: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            {key.replace('_score', '').toUpperCase()}
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={numValue * 100}
                            sx={{
                              height: 6,
                              borderRadius: 3,
                              my: 0.5,
                              bgcolor: alpha(theme.palette.primary.main, 0.1),
                              '& .MuiLinearProgress-bar': {
                                borderRadius: 3,
                                bgcolor:
                                  numValue > 0.8
                                    ? theme.palette.success.main
                                    : numValue > 0.5
                                    ? theme.palette.warning.main
                                    : theme.palette.error.main,
                              },
                            }}
                          />
                          <Typography variant="body2" fontWeight="bold">
                            {(numValue * 100).toFixed(0)}%
                          </Typography>
                        </Box>
                      </Grid>
                    );
                  })}
            </Grid>
          </Collapse>

          <Divider sx={{ my: 2 }} />

          {/* Action Buttons */}
          <Stack direction="row" spacing={2} justifyContent="center">
            <Button
              variant="contained"
              color="primary"
              startIcon={<CompareArrows />}
              onClick={onCompare}
              sx={{
                textTransform: 'none',
                fontWeight: 600,
                px: 3,
              }}
            >
              Compare All
            </Button>
            <Button
              variant="outlined"
              startIcon={<InfoOutlined />}
              onClick={onViewDetails}
              sx={{
                textTransform: 'none',
                fontWeight: 600,
                px: 3,
              }}
            >
              View Details
            </Button>
            <Tooltip title="Add to shopping list">
              <IconButton color="primary">
                <ShoppingCart />
              </IconButton>
            </Tooltip>
          </Stack>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default ImprovedPriceComparisonCard;