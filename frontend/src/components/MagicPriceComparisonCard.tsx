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
  Star,
  StarBorder,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

// Magic UI Components (inline implementations for demo)
const ShimmerButton = React.forwardRef<
  HTMLButtonElement,
  React.ComponentPropsWithoutRef<"button"> & {
    shimmerColor?: string;
    shimmerSize?: string;
    borderRadius?: string;
    shimmerDuration?: string;
    background?: string;
    className?: string;
    children?: React.ReactNode;
  }
>(
  (
    {
      shimmerColor = "#ffffff",
      shimmerSize = "0.05em",
      shimmerDuration = "3s",
      borderRadius = "100px",
      background = "rgba(0, 0, 0, 1)",
      className,
      children,
      ...props
    },
    ref,
  ) => {
    return (
      <button
        style={
          {
            "--spread": "90deg",
            "--shimmer-color": shimmerColor,
            "--radius": borderRadius,
            "--speed": shimmerDuration,
            "--cut": shimmerSize,
            "--bg": background,
            background: background,
            borderRadius: borderRadius,
          } as React.CSSProperties
        }
        className={`group relative z-0 flex cursor-pointer items-center justify-center overflow-hidden whitespace-nowrap border border-white/10 px-6 py-3 text-white transform-gpu transition-transform duration-300 ease-in-out active:translate-y-px ${className}`}
        ref={ref}
        {...props}
      >
        {/* Shimmer effect */}
        <div className="absolute inset-0 overflow-visible -z-30 blur-[2px]">
          <div className="absolute inset-0 h-full animate-pulse">
            <div 
              className="absolute -inset-full w-auto rotate-0"
              style={{
                background: `conic-gradient(from calc(270deg - 45deg), transparent 0, ${shimmerColor} 90deg, transparent 90deg)`,
                animation: `spin 3s linear infinite`,
              }}
            />
          </div>
        </div>
        {children}
        
        {/* Highlight overlay */}
        <div className="absolute inset-0 rounded-2xl px-4 py-1.5 text-sm font-medium shadow-[inset_0_-8px_10px_#ffffff1f] transform-gpu transition-all duration-300 ease-in-out group-hover:shadow-[inset_0_-6px_10px_#ffffff3f] group-active:shadow-[inset_0_-10px_10px_#ffffff3f]" />
        
        {/* Backdrop */}
        <div 
          className="absolute -z-20"
          style={{
            background: background,
            borderRadius: borderRadius,
            inset: shimmerSize,
          }}
        />
      </button>
    );
  },
);

const NumberTicker: React.FC<{
  value: number;
  className?: string;
  prefix?: string;
  suffix?: string;
}> = ({ value, className, prefix = "", suffix = "" }) => {
  const [displayValue, setDisplayValue] = React.useState(0);
  
  React.useEffect(() => {
    const duration = 1000; // 1 second
    const steps = 60;
    const increment = value / steps;
    let current = 0;
    let step = 0;
    
    const timer = setInterval(() => {
      if (step < steps) {
        current += increment;
        setDisplayValue(Math.floor(current));
        step++;
      } else {
        setDisplayValue(value);
        clearInterval(timer);
      }
    }, duration / steps);
    
    return () => clearInterval(timer);
  }, [value]);

  return (
    <span className={className}>
      {prefix}{displayValue.toLocaleString()}{suffix}
    </span>
  );
};

const AnimatedShinyText: React.FC<{
  children: React.ReactNode;
  className?: string;
  shimmerWidth?: number;
}> = ({ children, className, shimmerWidth = 100 }) => {
  return (
    <span
      style={{
        "--shiny-width": `${shimmerWidth}px`,
        background: "linear-gradient(to right, transparent, rgba(255,255,255,0.8) 50%, transparent)",
        backgroundSize: "var(--shiny-width) 100%",
        backgroundRepeat: "no-repeat",
        backgroundPosition: "0 0",
        animation: "shimmer 2s infinite",
        backgroundClip: "text",
        WebkitBackgroundClip: "text",
        color: "transparent",
      } as React.CSSProperties}
      className={className}
    >
      {children}
    </span>
  );
};

const SparklesText: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className }) => {
  return (
    <span className={`relative inline-block ${className}`}>
      {/* Sparkle effects */}
      <span className="absolute -top-1 -right-1 text-yellow-400 animate-pulse">✨</span>
      <span className="absolute -bottom-1 -left-1 text-blue-400 animate-pulse" style={{ animationDelay: '0.5s' }}>⭐</span>
      <span className="absolute top-0 left-1/2 text-purple-400 animate-pulse" style={{ animationDelay: '1s' }}>✨</span>
      <strong>{children}</strong>
    </span>
  );
};

interface RetailerPrice {
  retailer_code: string;
  retailer_name: string;
  price: number;
  url?: string;
  in_stock?: boolean;
  last_updated?: string;
}

interface MagicPriceComparisonCardProps {
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

// Enhanced retailer information with premium colors
const retailerInfo: Record<string, { name: string; color: string; gradient: string }> = {
  'HP': { 
    name: 'HomePro', 
    color: '#FF6B35',
    gradient: 'linear-gradient(135deg, #FF6B35 0%, #FF8A65 100%)'
  },
  'TWD': { 
    name: 'Thai Watsadu', 
    color: '#1976D2',
    gradient: 'linear-gradient(135deg, #1976D2 0%, #42A5F5 100%)'
  },
  'GH': { 
    name: 'Global House', 
    color: '#4CAF50',
    gradient: 'linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%)'
  },
  'DH': { 
    name: 'DoHome', 
    color: '#FF9800',
    gradient: 'linear-gradient(135deg, #FF9800 0%, #FFB74D 100%)'
  },
  'BT': { 
    name: 'Boonthavorn', 
    color: '#9C27B0',
    gradient: 'linear-gradient(135deg, #9C27B0 0%, #BA68C8 100%)'
  },
  'MH': { 
    name: 'MegaHome', 
    color: '#E91E63',
    gradient: 'linear-gradient(135deg, #E91E63 0%, #F06292 100%)'
  },
};

const MagicPriceComparisonCard: React.FC<MagicPriceComparisonCardProps> = ({
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
  const [favorited, setFavorited] = useState(false);
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

  // Determine if this is a high savings deal
  const isHighSavings = savingsPercentage > 30;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      whileHover={{ scale: 1.02, y: -5 }}
      onHoverStart={() => setHovering(true)}
      onHoverEnd={() => setHovering(false)}
    >
      <Card
        sx={{
          position: 'relative',
          overflow: 'visible',
          background: hovering
            ? `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${alpha(confidenceColor, 0.05)} 100%)`
            : theme.palette.background.paper,
          borderRadius: 4,
          boxShadow: hovering ? theme.shadows[12] : theme.shadows[4],
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          border: `2px solid ${hovering ? confidenceColor : 'transparent'}`,
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `linear-gradient(135deg, ${confidenceColor}15 0%, transparent 50%, ${confidenceColor}15 100%)`,
            borderRadius: 4,
            opacity: hovering ? 1 : 0,
            transition: 'opacity 0.4s ease',
          },
        }}
      >
        {/* Premium Confidence Badge */}
        <Box
          sx={{
            position: 'absolute',
            top: -15,
            right: 20,
            zIndex: 10,
          }}
        >
          <motion.div
            animate={{ 
              rotate: hovering ? [0, 360] : 0,
              scale: hovering ? [1, 1.1, 1] : 1,
            }}
            transition={{ 
              duration: hovering ? 0.8 : 0.4,
              ease: "easeInOut"
            }}
          >
            <Avatar
              sx={{
                background: `linear-gradient(135deg, ${confidenceColor} 0%, ${alpha(confidenceColor, 0.8)} 100%)`,
                width: 70,
                height: 70,
                boxShadow: `0 8px 32px ${alpha(confidenceColor, 0.3)}`,
                border: `3px solid ${theme.palette.background.paper}`,
              }}
            >
              <Stack alignItems="center" spacing={0}>
                <NumberTicker 
                  value={Math.round(matchConfidence * 100)} 
                  suffix="%" 
                  className="text-sm font-bold text-white"
                />
                <CheckCircle sx={{ fontSize: 16, color: 'white' }} />
              </Stack>
            </Avatar>
          </motion.div>
        </Box>

        {/* Favorite Button */}
        <IconButton
          onClick={() => setFavorited(!favorited)}
          sx={{
            position: 'absolute',
            top: 10,
            right: 10,
            zIndex: 5,
            color: favorited ? '#FFD700' : theme.palette.text.secondary,
            transition: 'all 0.3s ease',
            '&:hover': {
              transform: 'scale(1.2)',
              color: '#FFD700',
            },
          }}
        >
          {favorited ? <Star /> : <StarBorder />}
        </IconButton>

        <CardContent sx={{ pt: 3, pb: 2 }}>
          {/* Product Header with Enhanced Typography */}
          <Grid container spacing={3} alignItems="flex-start">
            <Grid item xs={12} md={7}>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Typography
                  variant="h6"
                  gutterBottom
                  sx={{
                    fontWeight: 700,
                    fontSize: '1.1rem',
                    lineHeight: 1.3,
                    background: `linear-gradient(135deg, ${theme.palette.text.primary} 0%, ${confidenceColor} 100%)`,
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    color: 'transparent',
                    mb: 2,
                  }}
                >
                  {productName}
                </Typography>
              </motion.div>
              
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }} flexWrap="wrap">
                <Chip
                  label={brand}
                  size="small"
                  icon={<Verified />}
                  sx={{ 
                    fontWeight: 600,
                    background: `linear-gradient(135deg, ${confidenceColor}20 0%, ${confidenceColor}10 100%)`,
                    color: confidenceColor,
                    border: `1px solid ${confidenceColor}30`,
                  }}
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
                      background: `linear-gradient(135deg, ${alpha(confidenceColor, 0.2)} 0%, ${alpha(confidenceColor, 0.1)} 100%)`,
                      color: confidenceColor,
                      fontWeight: 700,
                      fontSize: '0.75rem',
                      borderRadius: 2,
                    }}
                  />
                </Tooltip>
              </Stack>
            </Grid>

            <Grid item xs={12} md={5}>
              {/* Premium Animated Savings Display */}
              <motion.div
                animate={{
                  scale: hovering ? [1, 1.05, 1] : 1,
                  rotateY: hovering ? [0, 5, 0] : 0,
                }}
                transition={{
                  duration: 0.6,
                  repeat: hovering ? Infinity : 0,
                  repeatDelay: 2,
                }}
              >
                <Box
                  sx={{
                    background: isHighSavings 
                      ? `linear-gradient(135deg, #FF6B35 0%, #FF8E53 50%, #FFB74D 100%)`
                      : `linear-gradient(135deg, ${theme.palette.success.main} 0%, ${theme.palette.success.dark} 100%)`,
                    borderRadius: 3,
                    p: 2.5,
                    color: 'white',
                    textAlign: 'center',
                    boxShadow: `0 8px 32px ${alpha(theme.palette.success.main, 0.3)}`,
                    position: 'relative',
                    overflow: 'hidden',
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: '-100%',
                      width: '100%',
                      height: '100%',
                      background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
                      animation: hovering ? 'shimmer 2s infinite' : 'none',
                    },
                  }}
                >
                  {isHighSavings ? (
                    <SparklesText className="text-2xl font-bold text-white">
                      ฿<NumberTicker value={savingsAmount} />
                    </SparklesText>
                  ) : (
                    <Typography variant="h4" sx={{ fontWeight: 'bold', fontSize: '1.8rem' }}>
                      ฿<NumberTicker value={savingsAmount} />
                    </Typography>
                  )}
                  
                  <Stack direction="row" alignItems="center" justifyContent="center" spacing={0.5} sx={{ mt: 1 }}>
                    <TrendingDown sx={{ fontSize: '1.2rem' }} />
                    {isHighSavings ? (
                      <AnimatedShinyText className="text-base font-semibold">
                        Save {savingsPercentage.toFixed(1)}%
                      </AnimatedShinyText>
                    ) : (
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        Save {savingsPercentage.toFixed(1)}%
                      </Typography>
                    )}
                  </Stack>
                  
                  {isHighSavings && (
                    <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.9 }}>
                      🔥 Hot Deal!
                    </Typography>
                  )}
                </Box>
              </motion.div>
            </Grid>
          </Grid>

          {/* Enhanced Price Range Visualization */}
          <Box sx={{ my: 3 }}>
            <Stack direction="row" justifyContent="space-between" sx={{ mb: 1.5 }}>
              <Typography variant="body2" color="text.secondary" fontWeight={600}>
                Price Range Analysis
              </Typography>
              <Typography variant="body2" fontWeight="bold" sx={{ 
                background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                color: 'transparent',
              }}>
                ฿{lowestPrice.toLocaleString()} - ฿{highestPrice.toLocaleString()}
              </Typography>
            </Stack>
            
            <Box sx={{ position: 'relative', height: 50 }}>
              <LinearProgress
                variant="determinate"
                value={100}
                sx={{
                  height: 10,
                  borderRadius: 5,
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 5,
                    background: `linear-gradient(90deg, 
                      ${theme.palette.success.main} 0%, 
                      ${theme.palette.warning.main} 50%, 
                      ${theme.palette.error.main} 100%)`,
                  },
                }}
              />
              
              {/* Enhanced Retailer Price Points */}
              {sortedRetailers.map((retailer, index) => {
                const position = ((retailer.price - lowestPrice) / (highestPrice - lowestPrice)) * 100;
                const retailerBrand = retailerInfo[retailer.retailer_code];
                
                return (
                  <Tooltip
                    key={`${retailer.retailer_code}-${index}-${retailer.price}`}
                    title={
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          {retailerBrand?.name || retailer.retailer_code}
                        </Typography>
                        <Typography variant="body2">
                          ฿{retailer.price.toLocaleString()}
                        </Typography>
                        {retailer.retailer_code === bestRetailerCode && (
                          <Typography variant="caption" sx={{ color: theme.palette.success.light }}>
                            🏆 Best Price
                          </Typography>
                        )}
                      </Box>
                    }
                  >
                    <motion.div
                      whileHover={{ scale: 1.3, y: -5 }}
                      transition={{ type: "spring", stiffness: 300 }}
                    >
                      <Avatar
                        sx={{
                          position: 'absolute',
                          top: -8,
                          left: `${position}%`,
                          transform: 'translateX(-50%)',
                          width: 36,
                          height: 36,
                          background: retailerBrand?.gradient || '#666',
                          fontSize: 11,
                          fontWeight: 'bold',
                          cursor: 'pointer',
                          border: retailer.retailer_code === bestRetailerCode 
                            ? `3px solid ${theme.palette.success.main}`
                            : `2px solid ${theme.palette.background.paper}`,
                          boxShadow: retailer.retailer_code === bestRetailerCode
                            ? `0 4px 20px ${alpha(theme.palette.success.main, 0.4)}`
                            : theme.shadows[3],
                        }}
                      >
                        {retailer.retailer_code}
                      </Avatar>
                    </motion.div>
                  </Tooltip>
                );
              })}
            </Box>
          </Box>

          {/* Premium Retailer Grid */}
          <Grid container spacing={2} sx={{ mb: 2 }}>
            {sortedRetailers.slice(0, expanded ? undefined : 3).map((retailer, index) => {
              const retailerBrand = retailerInfo[retailer.retailer_code];
              const isBestPrice = retailer.retailer_code === bestRetailerCode;
              
              return (
                <Grid item xs={12} sm={6} md={4} key={`retailer-${retailer.retailer_code}-${index}-${retailer.price}`}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    whileHover={{ scale: 1.02, y: -2 }}
                  >
                    <Box
                      sx={{
                        p: 2,
                        borderRadius: 3,
                        background: isBestPrice
                          ? `linear-gradient(135deg, ${alpha(theme.palette.success.main, 0.15)} 0%, ${alpha(theme.palette.success.main, 0.05)} 100%)`
                          : `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${alpha(retailerBrand?.color || '#666', 0.05)} 100%)`,
                        border: isBestPrice
                          ? `2px solid ${theme.palette.success.main}`
                          : `1px solid ${alpha(retailerBrand?.color || theme.palette.divider, 0.3)}`,
                        position: 'relative',
                        overflow: 'hidden',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          boxShadow: `0 8px 32px ${alpha(retailerBrand?.color || theme.palette.primary.main, 0.2)}`,
                        },
                      }}
                    >
                      {isBestPrice && (
                        <motion.div
                          initial={{ scale: 0, rotate: -180 }}
                          animate={{ scale: 1, rotate: 0 }}
                          transition={{ delay: 0.3, type: "spring" }}
                        >
                          <Chip
                            label="🏆 BEST PRICE"
                            size="small"
                            sx={{
                              position: 'absolute',
                              top: 8,
                              right: 8,
                              fontSize: '0.7rem',
                              height: 24,
                              background: `linear-gradient(135deg, ${theme.palette.success.main} 0%, ${theme.palette.success.dark} 100%)`,
                              color: 'white',
                              fontWeight: 'bold',
                              boxShadow: `0 4px 12px ${alpha(theme.palette.success.main, 0.4)}`,
                            }}
                          />
                        </motion.div>
                      )}
                      
                      <Stack direction="row" alignItems="center" spacing={1.5}>
                        <Avatar
                          sx={{
                            background: retailerBrand?.gradient || '#666',
                            width: 42,
                            height: 42,
                            fontSize: 12,
                            fontWeight: 'bold',
                            boxShadow: theme.shadows[3],
                          }}
                        >
                          {retailer.retailer_code}
                        </Avatar>
                        
                        <Box flex={1}>
                          <Typography variant="caption" color="text.secondary" fontWeight={500}>
                            {retailerBrand?.name || retailer.retailer_code}
                          </Typography>
                          <Typography variant="h6" fontWeight="bold" sx={{
                            background: isBestPrice 
                              ? `linear-gradient(135deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`
                              : `linear-gradient(135deg, ${theme.palette.text.primary}, ${retailerBrand?.color || theme.palette.text.primary})`,
                            backgroundClip: 'text',
                            WebkitBackgroundClip: 'text',
                            color: 'transparent',
                          }}>
                            ฿<NumberTicker value={retailer.price} />
                          </Typography>
                          
                          {retailer.in_stock !== false && (
                            <Typography variant="caption" sx={{ color: theme.palette.success.main, fontWeight: 500 }}>
                              ✓ In Stock
                            </Typography>
                          )}
                        </Box>
                      </Stack>
                    </Box>
                  </motion.div>
                </Grid>
              );
            })}
          </Grid>

          {/* Show More/Less Button */}
          {retailers.length > 3 && (
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <Button
                size="small"
                onClick={() => setExpanded(!expanded)}
                endIcon={expanded ? <ExpandLess /> : <ExpandMore />}
                sx={{ 
                  textTransform: 'none',
                  borderRadius: 2,
                  fontWeight: 600,
                }}
              >
                {expanded ? 'Show Less' : `Show ${retailers.length - 3} More Retailers`}
              </Button>
            </Box>
          )}

          {/* Enhanced Match Details */}
          <Collapse in={expanded && !!matchDetails}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 700, color: theme.palette.primary.main }}>
              🔍 Match Quality Analysis
            </Typography>
            
            {/* Show rejection reasons if any */}
            {matchDetails?.rejection_reasons && matchDetails.rejection_reasons.length > 0 && (
              <Box sx={{ mb: 2, p: 2, borderRadius: 2, bgcolor: alpha(theme.palette.error.main, 0.1) }}>
                <Typography variant="body2" color="error" fontWeight="bold" sx={{ mb: 1 }}>
                  ❌ Match Rejected:
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
              <Box sx={{ mb: 2, p: 2, borderRadius: 2, bgcolor: alpha(theme.palette.warning.main, 0.1) }}>
                <Typography variant="body2" color="warning.main" fontWeight="bold" sx={{ mb: 1 }}>
                  ⚠️ Warnings:
                </Typography>
                {matchDetails.warnings.map((warning, index) => (
                  <Typography key={`warning-${index}-${warning}`} variant="body2" color="warning.main" sx={{ ml: 1 }}>
                    • {warning}
                  </Typography>
                ))}
              </Box>
            )}

            {/* Enhanced Score breakdown */}
            <Grid container spacing={2}>
              {matchDetails &&
                Object.entries(matchDetails)
                  .filter(([key]) => key.endsWith('_score'))
                  .map(([key, value]) => {
                    const numValue = typeof value === 'number' ? value : 0;
                    return (
                      <Grid item xs={6} sm={3} key={key}>
                        <Box sx={{ textAlign: 'center', p: 1.5, borderRadius: 2, bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                          <Typography variant="caption" color="text.secondary" fontWeight={600}>
                            {key.replace('_score', '').toUpperCase()}
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={numValue * 100}
                            sx={{
                              height: 8,
                              borderRadius: 4,
                              my: 1,
                              bgcolor: alpha(theme.palette.primary.main, 0.1),
                              '& .MuiLinearProgress-bar': {
                                borderRadius: 4,
                                background: numValue > 0.8
                                  ? `linear-gradient(135deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`
                                  : numValue > 0.5
                                  ? `linear-gradient(135deg, ${theme.palette.warning.main}, ${theme.palette.warning.dark})`
                                  : `linear-gradient(135deg, ${theme.palette.error.main}, ${theme.palette.error.dark})`,
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

          {/* Premium Action Buttons */}
          <Stack direction="row" spacing={2} justifyContent="center">
            <ShimmerButton
              onClick={onCompare}
              background="linear-gradient(135deg, #1976D2 0%, #42A5F5 100%)"
              shimmerColor="#ffffff"
              className="px-6 py-2 rounded-xl font-semibold"
            >
              <CompareArrows sx={{ mr: 1, fontSize: '1.1rem' }} />
              Compare All
            </ShimmerButton>
            
            <Button
              variant="outlined"
              startIcon={<InfoOutlined />}
              onClick={onViewDetails}
              sx={{
                textTransform: 'none',
                fontWeight: 600,
                px: 3,
                py: 1,
                borderRadius: 3,
                borderWidth: 2,
                '&:hover': {
                  borderWidth: 2,
                  transform: 'translateY(-2px)',
                  boxShadow: theme.shadows[8],
                },
              }}
            >
              View Details
            </Button>
            
            <Tooltip title="Add to shopping list">
              <IconButton 
                color="primary" 
                sx={{
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                  '&:hover': {
                    bgcolor: alpha(theme.palette.primary.main, 0.2),
                    transform: 'scale(1.1)',
                  },
                }}
              >
                <ShoppingCart />
              </IconButton>
            </Tooltip>
          </Stack>
        </CardContent>
      </Card>
      
      {/* Custom CSS for animations */}
      <style>{`
        @keyframes shimmer {
          0% { background-position: -100% 0; }
          100% { background-position: 100% 0; }
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </motion.div>
  );
};

export default MagicPriceComparisonCard;