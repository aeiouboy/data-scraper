import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Stack,
  Avatar,
  LinearProgress,
  Tooltip,
  IconButton,
  Divider,
} from '@mui/material';
import {
  TrendingDown as SavingsIcon,
  Store as StoreIcon,
  Info as InfoIcon,
  OpenInNew as OpenIcon,
} from '@mui/icons-material';

interface RetailerPrice {
  retailerCode: string;
  retailerName: string;
  price: number;
  url?: string;
  inStock: boolean;
}

interface PriceComparisonCardProps {
  productName: string;
  category: string;
  brand?: string;
  image?: string;
  retailers: RetailerPrice[];
  bestRetailerCode: string;
  savingsAmount: number;
  savingsPercentage: number;
  matchConfidence?: number;
}

const retailerColors: Record<string, string> = {
  'HP': '#FF6B35',
  'TWD': '#1976D2',
  'GH': '#4CAF50',
  'DH': '#FF9800',
  'BT': '#9C27B0',
  'MH': '#607D8B',
};

const PriceComparisonCard = React.memo(({
  productName,
  category,
  brand,
  image,
  retailers,
  bestRetailerCode,
  savingsAmount,
  savingsPercentage,
  matchConfidence = 0.85,
}: PriceComparisonCardProps) => {
  const minPrice = Math.min(...retailers.map(r => r.price));
  const maxPrice = Math.max(...retailers.map(r => r.price));
  const priceRange = maxPrice - minPrice;

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flex: 1 }}>
        {/* Product Header */}
        <Stack spacing={2}>
          <Box>
            <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
              <Box flex={1}>
                <Typography variant="h6" gutterBottom>
                  {productName}
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  {brand && (
                    <Chip label={brand} size="small" variant="outlined" />
                  )}
                  <Chip label={category} size="small" />
                  {matchConfidence && (
                    <Tooltip title={`Match confidence: ${(matchConfidence * 100).toFixed(0)}%`}>
                      <Chip 
                        label={`${(matchConfidence * 100).toFixed(0)}% match`}
                        size="small"
                        color={matchConfidence > 0.8 ? 'success' : 'warning'}
                      />
                    </Tooltip>
                  )}
                </Stack>
              </Box>
              {image && (
                <Box
                  component="img"
                  src={image}
                  alt={productName}
                  sx={{
                    width: 80,
                    height: 80,
                    objectFit: 'cover',
                    borderRadius: 1,
                    ml: 2,
                  }}
                />
              )}
            </Stack>
          </Box>

          {/* Savings Highlight */}
          <Box
            sx={{
              background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
              borderRadius: 2,
              p: 2,
              color: 'white',
            }}
          >
            <Stack direction="row" alignItems="center" spacing={2}>
              <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
                <SavingsIcon />
              </Avatar>
              <Box>
                <Typography variant="h5" fontWeight="bold">
                  Save ฿{savingsAmount.toLocaleString()}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  {savingsPercentage.toFixed(1)}% savings potential
                </Typography>
              </Box>
            </Stack>
          </Box>

          <Divider />

          {/* Price Comparison */}
          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Price Comparison Across Retailers
            </Typography>
            
            <Stack spacing={1.5}>
              {retailers
                .sort((a, b) => a.price - b.price)
                .map((retailer, index) => {
                  const isBestPrice = retailer.retailerCode === bestRetailerCode;
                  const pricePosition = ((retailer.price - minPrice) / priceRange) * 100;
                  
                  return (
                    <Box key={`${retailer.retailerCode}-${index}`}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={0.5}>
                        <Stack direction="row" alignItems="center" spacing={1}>
                          <Avatar
                            sx={{
                              width: 28,
                              height: 28,
                              bgcolor: retailerColors[retailer.retailerCode],
                              fontSize: 12,
                            }}
                          >
                            {retailer.retailerCode}
                          </Avatar>
                          <Typography variant="body2" fontWeight={isBestPrice ? 'bold' : 'normal'}>
                            {retailer.retailerName}
                          </Typography>
                          {isBestPrice && (
                            <Chip
                              label="BEST PRICE"
                              size="small"
                              color="success"
                              sx={{ height: 20, fontSize: 10 }}
                            />
                          )}
                        </Stack>
                        <Stack direction="row" alignItems="center" spacing={1}>
                          <Typography
                            variant="body1"
                            fontWeight="bold"
                            color={isBestPrice ? 'success.main' : 'text.primary'}
                          >
                            ฿{retailer.price.toLocaleString()}
                          </Typography>
                          {retailer.url && (
                            <Tooltip title="View product">
                              <IconButton
                                size="small"
                                href={retailer.url}
                                target="_blank"
                                sx={{ p: 0.5 }}
                              >
                                <OpenIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Stack>
                      </Stack>
                      
                      {/* Price Bar Visualization */}
                      <Box sx={{ position: 'relative', height: 8, bgcolor: 'grey.200', borderRadius: 1 }}>
                        <Box
                          sx={{
                            position: 'absolute',
                            left: 0,
                            top: 0,
                            height: '100%',
                            width: `${priceRange > 0 ? pricePosition : 100}%`,
                            bgcolor: isBestPrice ? 'success.main' : retailerColors[retailer.retailerCode],
                            borderRadius: 1,
                            transition: 'width 0.3s ease',
                          }}
                        />
                      </Box>
                      
                      {!retailer.inStock && (
                        <Typography variant="caption" color="error" sx={{ mt: 0.5 }}>
                          Out of stock
                        </Typography>
                      )}
                    </Box>
                  );
                })}
            </Stack>
          </Box>

          {/* Price Range Summary */}
          <Box sx={{ bgcolor: 'grey.50', borderRadius: 1, p: 1.5 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Typography variant="caption" color="text.secondary">
                Price Range
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                ฿{minPrice.toLocaleString()} - ฿{maxPrice.toLocaleString()}
              </Typography>
            </Stack>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
});

PriceComparisonCard.displayName = 'PriceComparisonCard';

export default PriceComparisonCard;