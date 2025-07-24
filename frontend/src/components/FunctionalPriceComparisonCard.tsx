import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Stack,
  Box,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Launch as LaunchIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Star as StarIcon,
} from '@mui/icons-material';

interface RetailerPrice {
  retailer_code: string;
  retailer_name: string;
  price: number;
  currency: string;
  product_url?: string;
  last_updated?: string;
  stock_status?: string;
  discount_percentage?: number;
  is_promotion?: boolean;
  shipping_cost?: number;
}

interface FunctionalPriceComparisonCardProps {
  productName: string;
  category: string;
  brand: string;
  retailers: RetailerPrice[];
  matchDetails?: {
    match_confidence?: number;
    match_type?: string;
    rejection_reasons?: string[];
    warnings?: string[];
    matched_fields?: string[];
  };
}

const retailerConfig: Record<string, {
  name: string;
  logo: string;
  color: string;
  baseUrl: string;
}> = {
  HP: {
    name: 'HomePro',
    logo: '🏠',
    color: '#ff6b35',
    baseUrl: 'https://www.homepro.co.th',
  },
  TWD: {
    name: 'Thai Watsadu',
    logo: '🔨',
    color: '#2196f3',
    baseUrl: 'https://www.thaiwatsadu.com',
  },
  GH: {
    name: 'Global House',
    logo: '🏡',
    color: '#4caf50',
    baseUrl: 'https://www.globalhouse.co.th',
  },
  BT: {
    name: 'Boonthavorn',
    logo: '🏺',
    color: '#9c27b0',
    baseUrl: 'https://www.boonthavorn.com',
  },
  MH: {
    name: 'MegaHome',
    logo: '🏗️',
    color: '#ff9800',
    baseUrl: 'https://www.megahome.co.th',
  },
  DH: {
    name: 'DoHome',
    logo: '🛠️',
    color: '#607d8b',
    baseUrl: 'https://www.dohome.co.th',
  },
};

const FunctionalPriceComparisonCard: React.FC<FunctionalPriceComparisonCardProps> = ({
  productName,
  category,
  brand,
  retailers,
  matchDetails,
}) => {
  const sortedRetailers = [...retailers].sort((a, b) => a.price - b.price);
  const lowestPrice = sortedRetailers[0]?.price || 0;
  const highestPrice = sortedRetailers[sortedRetailers.length - 1]?.price || 0;
  const averagePrice = retailers.reduce((sum, r) => sum + r.price, 0) / retailers.length;
  const potentialSavings = highestPrice - lowestPrice;
  const savingsPercentage = highestPrice > 0 ? ((potentialSavings / highestPrice) * 100) : 0;


  const getMatchConfidenceText = (confidence?: number) => {
    if (!confidence) return 'Unknown';
    if (confidence >= 0.9) return 'Excellent Match';
    if (confidence >= 0.7) return 'Good Match';
    if (confidence >= 0.5) return 'Fair Match';
    return 'Poor Match';
  };

  const formatPrice = (price: number, currency: string = 'THB') => {
    return new Intl.NumberFormat('th-TH', {
      style: 'currency',
      currency: currency,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const getRetailerConfig = (retailerCode: string) => {
    return retailerConfig[retailerCode] || {
      name: retailerCode,
      logo: '🏪',
      color: '#757575',
      baseUrl: '',
    };
  };

  const getPriceRanking = (price: number) => {
    const rank = sortedRetailers.findIndex(r => r.price === price) + 1;
    return rank;
  };

  const getPriceVarianceFromAverage = (price: number) => {
    const variance = ((price - averagePrice) / averagePrice) * 100;
    return variance;
  };

  return (
    <Card 
      elevation={1} 
      sx={{ 
        mb: 3,
        border: '1px solid #e0e0e0',
        borderRadius: 2,
      }}
    >
      <CardContent sx={{ p: 3 }}>
        {/* Header Section */}
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: '#1a1a1a' }}>
              {productName}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center" mb={1}>
              <Chip 
                label={brand} 
                size="small" 
                sx={{ 
                  backgroundColor: '#f5f5f5',
                  fontWeight: 500,
                  border: '1px solid #e0e0e0',
                }}
              />
              <Chip 
                label={category} 
                size="small" 
                variant="outlined"
                sx={{ fontSize: '0.75rem' }}
              />
            </Stack>
          </Box>
          
          {/* Match Quality */}
          {matchDetails && matchDetails.match_confidence && (
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="body2" sx={{ color: '#666' }}>
                {getMatchConfidenceText(matchDetails.match_confidence)}
              </Typography>
              <Typography variant="caption" sx={{ color: '#666' }}>
                {(matchDetails.match_confidence * 100).toFixed(0)}% match
              </Typography>
            </Box>
          )}
        </Stack>

        {/* Price Summary */}
        <Box sx={{ mb: 3, p: 2, backgroundColor: '#f8f9fa', borderRadius: 1 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" sx={{ color: '#666' }}>
              Price Range ({retailers.length} retailers)
            </Typography>
            {savingsPercentage > 0 && (
              <Typography variant="body2" sx={{ color: '#4caf50', fontWeight: 600 }}>
                Save up to {savingsPercentage.toFixed(1)}%
              </Typography>
            )}
          </Stack>
          <Typography variant="h5" sx={{ fontWeight: 700, color: '#1a1a1a' }}>
            {formatPrice(lowestPrice)} - {formatPrice(highestPrice)}
          </Typography>
        </Box>

        {/* Detailed Price Table */}
        <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
          <Table size="small">
            <TableHead>
              <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                <TableCell sx={{ fontWeight: 600 }}>Retailer</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Price</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600 }}>Rank</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600 }}>vs Avg</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600 }}>Stock</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600 }}>Website</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedRetailers.map((retailer, index) => {
                const config = getRetailerConfig(retailer.retailer_code);
                const rank = getPriceRanking(retailer.price);
                const variance = getPriceVarianceFromAverage(retailer.price);
                const isLowest = index === 0;
                
                return (
                  <TableRow 
                    key={retailer.retailer_code}
                    sx={{ 
                      backgroundColor: isLowest ? '#e8f5e8' : 'inherit',
                    }}
                  >
                    <TableCell>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <span style={{ fontSize: '16px' }}>{config.logo}</span>
                        <Stack>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {config.name}
                          </Typography>
                          <Typography variant="caption" sx={{ color: '#666' }}>
                            {retailer.retailer_code}
                          </Typography>
                        </Stack>
                      </Stack>
                    </TableCell>
                    
                    <TableCell align="right">
                      <Stack alignItems="flex-end" spacing={0.5}>
                        <Typography 
                          variant="body1" 
                          sx={{ 
                            fontWeight: isLowest ? 700 : 500,
                            color: isLowest ? '#4caf50' : '#1a1a1a',
                          }}
                        >
                          {formatPrice(retailer.price)}
                        </Typography>
                        {retailer.shipping_cost && (
                          <Typography variant="caption" sx={{ color: '#666' }}>
                            +{formatPrice(retailer.shipping_cost)} shipping
                          </Typography>
                        )}
                      </Stack>
                    </TableCell>
                    
                    <TableCell align="center">
                      <Stack direction="row" alignItems="center" justifyContent="center" spacing={0.5}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          #{rank}
                        </Typography>
                        {isLowest && <StarIcon sx={{ color: '#4caf50', fontSize: 16 }} />}
                      </Stack>
                    </TableCell>
                    
                    <TableCell align="center">
                      <Stack direction="row" alignItems="center" justifyContent="center" spacing={0.5}>
                        {variance > 0 ? (
                          <TrendingUpIcon sx={{ color: '#f44336', fontSize: 16 }} />
                        ) : (
                          <TrendingDownIcon sx={{ color: '#4caf50', fontSize: 16 }} />
                        )}
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: variance > 0 ? '#f44336' : '#4caf50',
                            fontWeight: 500,
                          }}
                        >
                          {variance > 0 ? '+' : ''}{variance.toFixed(1)}%
                        </Typography>
                      </Stack>
                    </TableCell>
                    
                    <TableCell align="center">
                      <Chip
                        label={retailer.stock_status || 'In Stock'}
                        size="small"
                        color={retailer.stock_status === 'In Stock' ? 'success' : 'warning'}
                        variant="outlined"
                        sx={{ fontSize: '0.7rem' }}
                      />
                    </TableCell>
                    
                    <TableCell align="center">
                      {retailer.product_url && (
                        <Tooltip title={`Visit ${config.name}`}>
                          <IconButton
                            size="small"
                            onClick={() => window.open(retailer.product_url, '_blank')}
                            sx={{ color: config.color }}
                          >
                            <LaunchIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Matching Notes */}
        {matchDetails?.warnings && matchDetails.warnings.length > 0 && (
          <Box sx={{ mb: 2, p: 2, backgroundColor: '#fff3cd', borderRadius: 1, border: '1px solid #ffeaa7' }}>
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#856404', mb: 1 }}>
              Matching Notes:
            </Typography>
            {matchDetails.warnings.map((warning, index) => (
              <Typography key={index} variant="body2" sx={{ color: '#856404', fontSize: '0.875rem' }}>
                • {warning}
              </Typography>
            ))}
          </Box>
        )}

        {matchDetails?.rejection_reasons && matchDetails.rejection_reasons.length > 0 && (
          <Box sx={{ mb: 2, p: 2, backgroundColor: '#f8d7da', borderRadius: 1, border: '1px solid #f5c6cb' }}>
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#721c24', mb: 1 }}>
              Matching Issues:
            </Typography>
            {matchDetails.rejection_reasons.map((reason, index) => (
              <Typography key={index} variant="body2" sx={{ color: '#721c24', fontSize: '0.875rem' }}>
                • {reason}
              </Typography>
            ))}
          </Box>
        )}

      </CardContent>
    </Card>
  );
};

export default FunctionalPriceComparisonCard;