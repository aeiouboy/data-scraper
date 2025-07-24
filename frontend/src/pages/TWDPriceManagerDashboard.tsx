import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Grid,
  Stack,
  Avatar,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Skeleton,
  Fade,
  Zoom,
  ToggleButton,
  ToggleButtonGroup,
  Badge,
  Divider,
} from '@mui/material';
import {
  TrendingDown as SavingsIcon,
  Store as StoreIcon,
  CompareArrows as CompareIcon,
  LocalOffer as OfferIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  ViewModule as GridViewIcon,
  ViewList as ListViewIcon,
  Analytics as AnalyticsIcon,
  Star as StarIcon,
  Speed as SpeedIcon,
  MonetizationOn as MoneyIcon,
  AttachMoney as DollarIcon,
  AccountBalance as BankIcon,
  Timeline as TimelineIcon,
  Notifications as NotificationsIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { priceComparisonApi } from '../services/api';
import { useRetailer } from '../contexts/RetailerContext';
import RetailerSelector from '../components/RetailerSelector';
import PriceTrackingDashboard from '../components/PriceTrackingDashboard';
import PriceComparisonCard from '../components/PriceComparisonCard';
import { NumberTicker, ShimmerButton, MagicCard } from '../components/ui';

// Custom Magic UI Components
const AnimatedGradientText = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <span 
    className={`animate-pulse bg-gradient-to-r from-[#FF6B35] via-[#1976D2] to-[#4CAF50] bg-clip-text text-transparent ${className}`}
    style={{
      background: 'linear-gradient(45deg, #FF6B35, #1976D2, #4CAF50)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
      animation: 'gradient 3s ease infinite',
    }}
  >
    {children}
  </span>
);

const SparklesText = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <span className={`relative ${className}`}>
    {children}
    <span className="absolute -top-1 -right-1 text-yellow-400 animate-pulse">✨</span>
  </span>
);

const retailerColors: Record<string, string> = {
  'HP': '#FF6B35',   // HomePro Orange
  'TWD': '#1976D2',  // Thai Watsadu Blue
  'GH': '#4CAF50',   // Global House Green
  'DH': '#FF9800',   // DoHome Orange
  'BT': '#9C27B0',   // Boonthavorn Purple
  'MH': '#607D8B',   // MegaHome Blue Grey
};

interface SavingsOpportunity {
  product_name: string;
  category: string;
  savings_amount: number;
  price_range: string;
  best_retailer: string;
  variance_percentage: number;
}

interface RetailerCompetitiveness {
  [category: string]: {
    [retailer: string]: {
      best_price_count: number;
      total_products: number;
      competitiveness_score: number;
    };
  };
}


export default function TWDPriceManagerDashboard() {
  const { selectedRetailers, multiRetailerMode } = useRetailer();
  const [categoryFilter, setCategoryFilter] = useState('');
  const [minSavings, setMinSavings] = useState(100);
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'analytics'>('grid');
  const [currentPage, setCurrentPage] = useState(0);
  const [minSavingsInput, setMinSavingsInput] = useState(100);
  const [showFilters, setShowFilters] = useState(false);
  const [matcherMode, setMatcherMode] = useState<'standard' | 'ultra-strict'>('standard');
  const itemsPerPage = 12;
  


  // Debounced update for minSavings
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setMinSavings(minSavingsInput);
      setCurrentPage(0);
    }, 500);
    
    return () => clearTimeout(timer);
  }, [minSavingsInput]);

  // Fetch detailed price comparisons using optimized endpoint
  const { data: detailedData, isLoading: loadingDetailed, refetch: refetchDetailed } = useQuery({
    queryKey: ['price-comparisons-optimized', minSavings, categoryFilter, currentPage, matcherMode, viewMode],
    queryFn: async () => {
      try {
        const limit = viewMode === 'grid' ? itemsPerPage : 50;
        const offset = currentPage * limit;
        
        const response = await priceComparisonApi.getDetailedComparisonsOptimized({
          limit,
          offset,
          minSavings: minSavings,
          category: categoryFilter || undefined,
        });
        
        if (!response.data) {
          throw new Error('No data received from API');
        }
        
        return response.data;
      } catch (error) {
        console.error('Error fetching detailed comparisons:', error);
        throw error;
      }
    },
    enabled: true, // Always enabled to show price comparisons
    staleTime: 30000,
    cacheTime: 300000,
    keepPreviousData: true,
    retry: 2,
  });

  // Fetch quick stats from API with better error handling
  const { data: quickStats, isLoading: loadingQuickStats, error: quickStatsError, refetch: refetchQuickStats } = useQuery({
    queryKey: ['twd-price-comparisons-quick-stats', categoryFilter],
    queryFn: async () => {
      try {
        const response = await priceComparisonApi.getQuickStats(categoryFilter || undefined);
        console.log('Quick stats response:', response.data);
        if (!response.data) {
          console.error('No data in response');
          return {
            totalSavingsAvailable: 0,
            productsWithSavings: 0,
            avgPriceVariance: 0,
            lastUpdated: new Date().toISOString()
          };
        }
        return response.data;
      } catch (error) {
        console.error('Error fetching quick stats:', error);
        return {
          totalSavingsAvailable: 0,
          productsWithSavings: 0,
          avgPriceVariance: 0,
          lastUpdated: new Date().toISOString()
        };
      }
    },
    enabled: true, // Always enabled to show statistics
    staleTime: 5000, // Very short cache for debugging
    retry: 1,
  });

  const comparisons = useMemo(() => detailedData?.comparisons || [], [detailedData]);
  
  // Extract values with fallback calculations
  const totalSavings = quickStats?.totalSavingsAvailable || 
    comparisons.reduce((sum: number, item: any) => sum + (item.priceAnalysis?.savingsAmount || 0), 0);
  const avgVariance = quickStats?.avgPriceVariance || 
    (comparisons.length > 0 
      ? comparisons.reduce((sum: number, item: any) => sum + (item.priceAnalysis?.savingsPercentage || 0), 0) / comparisons.length 
      : 0);
  const productsWithSavings = quickStats?.productsWithSavings || comparisons.length;
  
  console.log('Debug - quickStats:', quickStats);
  console.log('Debug - quickStatsError:', quickStatsError);
  console.log('Debug - loadingQuickStats:', loadingQuickStats);
  console.log('Debug - totalSavings:', totalSavings);
  console.log('Debug - avgVariance:', avgVariance);
  console.log('Debug - productsWithSavings:', productsWithSavings);
  console.log('Debug - comparisons.length:', comparisons.length);
  
  // Calculate TWD's competitive advantage
  const twdWins = comparisons.filter((item: any) => 
    item.priceAnalysis?.bestRetailer === 'TWD'
  ).length;
  const competitiveAdvantage = comparisons.length > 0 ? (twdWins / comparisons.length) * 100 : 0;

  // Refresh all matches
  const handleRefreshMatches = async () => {
    try {
      await priceComparisonApi.refreshMatches();
      refetchDetailed();
      refetchQuickStats();
    } catch (error) {
      console.error('Failed to refresh matches:', error);
    }
  };

  // Manual refresh for debugging
  const handleManualRefresh = () => {
    console.log('Manual refresh triggered');
    refetchQuickStats();
    refetchDetailed();
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Header with Magic UI */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" sx={{ mb: 2, fontWeight: 'bold' }}>
          <AnimatedGradientText>
            ⚡ TWD Price Intelligence Hub
          </AnimatedGradientText>
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>
          Real-time competitive analysis and pricing insights for Thai Watsadu
        </Typography>
        
        {/* Live Status Indicator */}
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mb: 3 }}>
          <Badge color="success" variant="dot">
            <Chip 
              label="Live Data" 
              color="success" 
              size="small" 
              icon={<SpeedIcon />}
            />
          </Badge>
          <Chip 
            label="Real-time Monitoring" 
            color="info" 
            size="small"
            icon={<NotificationsIcon />}
          />
          <Chip 
            label="6 Retailers Monitored" 
            color="info" 
            size="small"
            icon={<StoreIcon />}
          />
          <Button 
            variant="outlined" 
            size="small" 
            onClick={handleManualRefresh}
            startIcon={<RefreshIcon />}
          >
            Refresh Data
          </Button>
        </Box>
      </Box>

      {/* Key Metrics Dashboard */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%)',
            color: 'white',
            position: 'relative',
            overflow: 'hidden',
            height: 140,
            display: 'flex',
            alignItems: 'center',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
              transform: 'translateX(-100%)',
              animation: 'shimmer 2s infinite',
            },
            '@keyframes shimmer': {
              '0%': { transform: 'translateX(-100%)' },
              '100%': { transform: 'translateX(100%)' },
            }
          }}>
            <CardContent sx={{ width: '100%', py: 2 }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', width: 48, height: 48 }}>
                  <DollarIcon sx={{ fontSize: 24 }} />
                </Avatar>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', fontFamily: 'monospace', fontSize: '1.75rem', lineHeight: 1.2, mb: 0.5 }}>
                    {loadingQuickStats ? (
                      <Skeleton width={80} height={32} sx={{ bgcolor: 'rgba(255,255,255,0.2)' }} />
                    ) : (
                      <>฿<NumberTicker value={totalSavings} /></>
                    )}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9, fontSize: '0.875rem', lineHeight: 1.3 }}>
                    <SparklesText>Customer Savings Available</SparklesText>
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #2196F3 0%, #21CBF3 100%)',
            color: 'white',
            position: 'relative',
            overflow: 'hidden',
            height: 140,
            display: 'flex',
            alignItems: 'center'
          }}>
            <CardContent sx={{ width: '100%', py: 2 }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', width: 48, height: 48 }}>
                  <StarIcon sx={{ fontSize: 24 }} />
                </Avatar>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', fontFamily: 'monospace', fontSize: '1.75rem', lineHeight: 1.2, mb: 0.5 }}>
                    {loadingQuickStats ? (
                      <Skeleton width={60} height={32} sx={{ bgcolor: 'rgba(255,255,255,0.2)' }} />
                    ) : (
                      <><NumberTicker value={Math.round(competitiveAdvantage)} />%</>
                    )}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9, fontSize: '0.875rem', lineHeight: 1.3 }}>
                    TWD Market Leadership
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #FF9800 0%, #FFB74D 100%)',
            color: 'white',
            position: 'relative',
            overflow: 'hidden',
            height: 140,
            display: 'flex',
            alignItems: 'center'
          }}>
            <CardContent sx={{ width: '100%', py: 2 }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', width: 48, height: 48 }}>
                  <TimelineIcon sx={{ fontSize: 24 }} />
                </Avatar>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', fontFamily: 'monospace', fontSize: '1.75rem', lineHeight: 1.2, mb: 0.5 }}>
                    {loadingQuickStats ? (
                      <Skeleton width={60} height={32} sx={{ bgcolor: 'rgba(255,255,255,0.2)' }} />
                    ) : (
                      <><NumberTicker value={Math.round(avgVariance)} />%</>
                    )}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9, fontSize: '0.875rem', lineHeight: 1.3 }}>
                    Avg Market Variance
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #9C27B0 0%, #BA68C8 100%)',
            color: 'white',
            position: 'relative',
            overflow: 'hidden',
            height: 140,
            display: 'flex',
            alignItems: 'center'
          }}>
            <CardContent sx={{ width: '100%', py: 2 }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', width: 48, height: 48 }}>
                  <CompareIcon sx={{ fontSize: 24 }} />
                </Avatar>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', fontFamily: 'monospace', fontSize: '1.75rem', lineHeight: 1.2, mb: 0.5 }}>
                    {loadingQuickStats ? (
                      <Skeleton width={60} height={32} sx={{ bgcolor: 'rgba(255,255,255,0.2)' }} />
                    ) : (
                      <NumberTicker value={productsWithSavings} />
                    )}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9, fontSize: '0.875rem', lineHeight: 1.3 }}>
                    Products Monitored
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Matching Mode Controls */}
      <Paper sx={{ p: 2, mb: 3, border: '2px solid #1976D2', backgroundColor: '#f3f7ff' }}>
        <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between" flexWrap="wrap">
          <Box>
            <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold', mb: 1 }}>
              🎯 Matching Precision Mode
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Control product matching accuracy and validation strictness
            </Typography>
          </Box>
          <ToggleButtonGroup
            value={matcherMode}
            exclusive
            onChange={(event, newMode) => {
              if (newMode !== null) {
                setMatcherMode(newMode);
                setCurrentPage(0); // Reset pagination
              }
            }}
            aria-label="matching mode"
            sx={{
              '& .MuiToggleButton-root': {
                px: 3,
                py: 1,
                fontWeight: 'bold',
                borderRadius: 2,
                border: '2px solid #1976D2',
                '&.Mui-selected': {
                  backgroundColor: '#1976D2',
                  color: 'white',
                  '&:hover': {
                    backgroundColor: '#1565C0',
                  }
                }
              }
            }}
          >
            <ToggleButton value="standard">
              <SpeedIcon sx={{ mr: 1 }} />
              Standard Mode
            </ToggleButton>
            <ToggleButton value="ultra-strict">
              <StarIcon sx={{ mr: 1 }} />
              Ultra-Strict Mode
            </ToggleButton>
          </ToggleButtonGroup>
        </Stack>
      </Paper>

      {/* Ultra-Strict Mode Indicator */}
      {matcherMode === 'ultra-strict' && (
        <Alert 
          severity="info" 
          sx={{ 
            mb: 3, 
            border: '2px solid #2196F3',
            backgroundColor: '#e3f2fd',
            '& .MuiAlert-icon': {
              fontSize: '1.5rem'
            }
          }}
        >
          <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
            🎯 <strong>Ultra-Strict Mode Active:</strong> Maximum accuracy matching with strict model validation. 
            False positives are eliminated but fewer matches may be found.
          </Typography>
          <Typography variant="body2" sx={{ mt: 1, opacity: 0.8 }}>
            Perfect for critical pricing decisions requiring 100% confidence in product matches.
          </Typography>
        </Alert>
      )}




      {/* Retailer selector */}
      <RetailerSelector variant="full" showStats={true} showMultiMode={true} />
      
      {/* Price comparison content */}
      <Paper sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          💰 Detailed Price Comparisons
        </Typography>
        
        {loadingDetailed ? (
          <Box sx={{ p: 2 }}>
            <Grid container spacing={2}>
              {[...Array(6)].map((_, index) => (
                <Grid item xs={12} md={6} lg={4} key={index}>
                  <Skeleton variant="rectangular" height={350} sx={{ borderRadius: 1 }} />
                </Grid>
              ))}
            </Grid>
          </Box>
        ) : comparisons.length > 0 ? (
          <Box sx={{ p: 2 }}>
            <Grid container spacing={2}>
              {comparisons.map((comparison: any, index: number) => (
                <Grid item xs={12} md={6} lg={4} key={comparison.matchId || `comp-${index}`}>
                  <Box sx={{ height: '100%' }}>
                    <PriceComparisonCard
                      productName={comparison.productName}
                      category={comparison.category}
                      brand={comparison.brand}
                      retailers={comparison.retailerPrices}
                      bestRetailerCode={comparison.priceAnalysis?.bestRetailer}
                      savingsAmount={comparison.priceAnalysis?.savingsAmount || 0}
                      savingsPercentage={comparison.priceAnalysis?.savingsPercentage || 0}
                      matchConfidence={comparison.matchConfidence}
                      matcherMode={matcherMode}
                    />
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Box>
        ) : (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              No price comparisons available. Try enabling multi-retailer mode for cross-retailer analysis.
            </Typography>
          </Box>
        )}
      </Paper>

    </Box>
  );
}