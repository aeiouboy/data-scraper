import React, { useState } from 'react';
import {
  Box,
  Button,
  ButtonGroup,
  Chip,
  FormControlLabel,
  IconButton,
  Paper,
  Stack,
  Switch,
  Tooltip,
  Typography,
  Avatar,
  Badge,
  Grow,
  Zoom,
  Fade,
} from '@mui/material';
import {
  Store as StoreIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as RadioButtonUncheckedIcon,
  ViewModule as ViewModuleIcon,
  ViewList as ViewListIcon,
  TrendingUp as TrendingUpIcon,
  Inventory as InventoryIcon,
} from '@mui/icons-material';
import { useRetailer } from '../contexts/RetailerContext';

const retailerColors: Record<string, string> = {
  'HP': '#FF6B35',   // HomePro Orange
  'TWD': '#1976D2',  // Thai Watsadu Blue
  'GH': '#4CAF50',   // Global House Green
  'DH': '#FF9800',   // DoHome Orange
  'BT': '#9C27B0',   // Boonthavorn Purple
  'MH': '#607D8B',   // MegaHome Blue Grey
};

const retailerLogos: Record<string, string> = {
  'HP': '🏠',   // HomePro
  'TWD': '🔨',  // Thai Watsadu
  'GH': '🏡',   // Global House
  'DH': '🛠️',   // DoHome
  'BT': '🏺',   // Boonthavorn
  'MH': '🏗️',   // MegaHome
};

interface RetailerSelectorProps {
  variant?: 'compact' | 'full' | 'badge';
  showStats?: boolean;
  showMultiMode?: boolean;
}

const RetailerSelector: React.FC<RetailerSelectorProps> = ({
  variant = 'full',
  showStats = true,
  showMultiMode = true,
}) => {
  const {
    selectedRetailer,
    setSelectedRetailer,
    multiRetailerMode,
    setMultiRetailerMode,
    selectedRetailers,
    setSelectedRetailers,
    retailers,
    getActiveRetailers,
    getRetailerStats,
  } = useRetailer();

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const activeRetailers = getActiveRetailers();

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    // For badge variant - could implement menu later
    console.log('Menu open clicked', event);
  };

  const handleRetailerSelect = (retailerCode: string) => {
    if (multiRetailerMode) {
      // Toggle retailer in multi-mode
      if (selectedRetailers.includes(retailerCode)) {
        setSelectedRetailers(selectedRetailers.filter(code => code !== retailerCode));
      } else {
        setSelectedRetailers([...selectedRetailers, retailerCode]);
      }
    } else {
      // Single retailer selection
      setSelectedRetailer(retailerCode);
    }
  };

  const handleMultiModeToggle = () => {
    setMultiRetailerMode(!multiRetailerMode);
    if (!multiRetailerMode) {
      // Entering multi-mode: select all active retailers
      setSelectedRetailers(activeRetailers.map(r => r.code));
    } else {
      // Exiting multi-mode: keep only first selected or default to HomePro
      const firstSelected = selectedRetailers[0] || 'HP';
      setSelectedRetailer(firstSelected);
    }
  };


  const selectedRetailerData = selectedRetailer ? 
    retailers.find(r => r.code === selectedRetailer) : null;

  // Compact Badge Variant
  if (variant === 'badge') {
    return (
      <Tooltip title={`Current: ${selectedRetailerData?.name || 'All Retailers'}`}>
        <Badge
          badgeContent={multiRetailerMode ? selectedRetailers.length : 1}
          color="primary"
          onClick={handleMenuOpen}
          sx={{ cursor: 'pointer' }}
        >
          <Avatar 
            sx={{ 
              bgcolor: multiRetailerMode ? '#666' : retailerColors[selectedRetailer || 'HP'],
              width: 32,
              height: 32,
            }}
          >
            {multiRetailerMode ? <ViewModuleIcon /> : retailerLogos[selectedRetailer || 'HP']}
          </Avatar>
        </Badge>
      </Tooltip>
    );
  }

  // Compact Variant
  if (variant === 'compact') {
    return (
      <Box>
        <ButtonGroup variant="outlined" size="small">
          <Button
            onClick={handleMenuOpen}
            endIcon={<ExpandMoreIcon />}
            startIcon={<StoreIcon />}
            sx={{
              borderColor: multiRetailerMode ? '#666' : retailerColors[selectedRetailer || 'HP'],
              color: multiRetailerMode ? '#666' : retailerColors[selectedRetailer || 'HP'],
            }}
          >
            {multiRetailerMode ? `${selectedRetailers.length} Retailers` : selectedRetailerData?.name}
          </Button>
          {showMultiMode && (
            <Tooltip title="Toggle Multi-Retailer Mode">
              <Button
                onClick={handleMultiModeToggle}
                sx={{
                  borderColor: multiRetailerMode ? '#666' : retailerColors[selectedRetailer || 'HP'],
                  bgcolor: multiRetailerMode ? 'action.selected' : 'transparent',
                }}
              >
                <ViewModuleIcon />
              </Button>
            </Tooltip>
          )}
        </ButtonGroup>
      </Box>
    );
  }

  // Full Variant
  return (
    <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <StoreIcon color="primary" />
          Retailer Selection
        </Typography>
        
        <Stack direction="row" spacing={1} alignItems="center">
          {showMultiMode && (
            <FormControlLabel
              control={
                <Switch
                  checked={multiRetailerMode}
                  onChange={handleMultiModeToggle}
                  size="small"
                />
              }
              label="Multi-Retailer"
              sx={{ mr: 2 }}
            />
          )}
          
          <Tooltip title={`View Mode: ${viewMode}`}>
            <IconButton
              size="small"
              onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
            >
              {viewMode === 'grid' ? <ViewListIcon /> : <ViewModuleIcon />}
            </IconButton>
          </Tooltip>
        </Stack>
      </Stack>

      {/* Retailer Selection */}
      {viewMode === 'grid' ? (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
          {activeRetailers.map((retailer, index) => {
            const isSelected = multiRetailerMode ? 
              selectedRetailers.includes(retailer.code) : 
              selectedRetailer === retailer.code;
            const stats = getRetailerStats(retailer.code);

            return (
              <Grow in timeout={300 + index * 100} key={retailer.code}>
                <Paper
                  elevation={isSelected ? 4 : 1}
                  onClick={() => handleRetailerSelect(retailer.code)}
                  sx={{
                    p: 2,
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    border: isSelected ? 
                      `2px solid ${retailerColors[retailer.code]}` : 
                      '2px solid transparent',
                    bgcolor: isSelected ? 
                      `${retailerColors[retailer.code]}10` : 
                      'background.paper',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: 4,
                    },
                  }}
                >
                  <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Avatar
                        sx={{
                          bgcolor: retailerColors[retailer.code],
                          width: 32,
                          height: 32,
                        }}
                      >
                        {retailerLogos[retailer.code]}
                      </Avatar>
                      <Typography variant="subtitle2" fontWeight="bold">
                        {retailer.name}
                      </Typography>
                    </Box>
                    
                    <Zoom in={isSelected}>
                      <CheckCircleIcon 
                        color="primary" 
                        sx={{ 
                          color: retailerColors[retailer.code],
                          display: isSelected ? 'block' : 'none',
                        }} 
                      />
                    </Zoom>
                  </Stack>

                  <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                    {retailer.market_position}
                  </Typography>

                  {showStats && stats && (
                    <Stack direction="row" spacing={1} flexWrap="wrap">
                      <Chip
                        icon={<InventoryIcon />}
                        label={`${stats.actual_products.toLocaleString()} products`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        icon={<TrendingUpIcon />}
                        label={`฿${stats.avg_price?.toFixed(0) || 0} avg`}
                        size="small"
                        variant="outlined"
                      />
                    </Stack>
                  )}
                </Paper>
              </Grow>
            );
          })}
        </Box>
      ) : (
        <Stack spacing={1}>
          {activeRetailers.map((retailer, index) => {
            const isSelected = multiRetailerMode ? 
              selectedRetailers.includes(retailer.code) : 
              selectedRetailer === retailer.code;
            const stats = getRetailerStats(retailer.code);

            return (
              <Fade in timeout={200 + index * 50} key={retailer.code}>
                <Paper
                  elevation={isSelected ? 2 : 0}
                  onClick={() => handleRetailerSelect(retailer.code)}
                  sx={{
                    p: 1.5,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    border: isSelected ? 
                      `1px solid ${retailerColors[retailer.code]}` : 
                      '1px solid transparent',
                    bgcolor: isSelected ? 
                      `${retailerColors[retailer.code]}08` : 
                      'transparent',
                    '&:hover': {
                      bgcolor: `${retailerColors[retailer.code]}05`,
                    },
                  }}
                >
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Avatar
                        sx={{
                          bgcolor: retailerColors[retailer.code],
                          width: 24,
                          height: 24,
                        }}
                      >
                        {retailerLogos[retailer.code]}
                      </Avatar>
                      
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {retailer.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {retailer.market_position}
                        </Typography>
                      </Box>
                    </Box>

                    <Stack direction="row" spacing={1} alignItems="center">
                      {showStats && stats && (
                        <>
                          <Typography variant="caption" color="text.secondary">
                            {stats.actual_products.toLocaleString()} products
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ฿{stats.avg_price?.toFixed(0) || 0} avg
                          </Typography>
                        </>
                      )}
                      
                      {isSelected ? (
                        <CheckCircleIcon 
                          sx={{ color: retailerColors[retailer.code], fontSize: 20 }} 
                        />
                      ) : (
                        <RadioButtonUncheckedIcon 
                          sx={{ color: 'text.disabled', fontSize: 20 }} 
                        />
                      )}
                    </Stack>
                  </Stack>
                </Paper>
              </Fade>
            );
          })}
        </Stack>
      )}

      {/* Selected Summary */}
      {multiRetailerMode && selectedRetailers.length > 0 && (
        <Box mt={2} p={1.5} bgcolor="action.hover" borderRadius={1}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Selected Retailers ({selectedRetailers.length}):
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {selectedRetailers.map(code => {
              const retailer = retailers.find(r => r.code === code);
              const stats = getRetailerStats(code);
              return retailer && (
                <Chip
                  key={code}
                  avatar={
                    <Avatar sx={{ bgcolor: retailerColors[code] }}>
                      {retailerLogos[code]}
                    </Avatar>
                  }
                  label={`${retailer.name} (${stats?.actual_products?.toLocaleString() || 0})`}
                  onDelete={() => handleRetailerSelect(code)}
                  size="small"
                  sx={{
                    bgcolor: `${retailerColors[code]}15`,
                    '& .MuiChip-deleteIcon': {
                      color: retailerColors[code],
                    },
                  }}
                />
              );
            })}
          </Stack>
        </Box>
      )}
    </Paper>
  );
};

export default RetailerSelector;