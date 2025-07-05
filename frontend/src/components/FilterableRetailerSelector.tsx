import React from 'react';
import {
  Autocomplete,
  TextField,
  Box,
  Avatar,
  Chip,
  Stack,
  Typography,
  Tooltip,
} from '@mui/material';
import {
  Store as StoreIcon,
  ViewModule as ViewModuleIcon,
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

interface FilterableRetailerSelectorProps {
  fullWidth?: boolean;
}

const FilterableRetailerSelector: React.FC<FilterableRetailerSelectorProps> = ({
  fullWidth = true
}) => {
  const {
    selectedRetailer,
    setSelectedRetailer,
    multiRetailerMode,
    setMultiRetailerMode,
    selectedRetailers = [],
    setSelectedRetailers,
    retailers = [],
    getActiveRetailers,
    getRetailerStats,
  } = useRetailer();

  const activeRetailers = getActiveRetailers() || [];
  
  const handleSingleRetailerChange = (_: any, newValue: any) => {
    if (newValue) {
      setSelectedRetailer(newValue.code);
    }
  };

  const handleMultiRetailerChange = (_: any, newValues: any[]) => {
    setSelectedRetailers(newValues.map(v => v.code));
  };

  const selectedSingleRetailer = retailers.find(r => r.code === selectedRetailer) || null;
  const selectedMultipleRetailers = selectedRetailers ? retailers.filter(r => selectedRetailers.includes(r.code)) : [];

  const renderOption = (props: any, option: any) => {
    const stats = getRetailerStats(option.code);
    
    return (
      <Box component="li" {...props}>
        <Stack direction="row" spacing={2} alignItems="center" width="100%">
          <Avatar
            sx={{
              bgcolor: retailerColors[option.code],
              width: 32,
              height: 32,
            }}
          >
            {retailerLogos[option.code]}
          </Avatar>
          <Box flex={1}>
            <Typography variant="body2" fontWeight="medium">
              {option.name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {option.market_position} • {stats?.actual_products?.toLocaleString() || 0} products
            </Typography>
          </Box>
        </Stack>
      </Box>
    );
  };

  const renderInput = (params: any) => (
    <TextField
      {...params}
      placeholder={multiRetailerMode ? "Select retailers..." : "Select a retailer..."}
      InputProps={{
        ...params.InputProps,
        startAdornment: (
          <>
            <StoreIcon sx={{ color: 'action.active', mr: 1 }} />
            {params.InputProps.startAdornment}
          </>
        ),
        endAdornment: (
          <>
            {params.InputProps.endAdornment}
            <Tooltip title={multiRetailerMode ? "Single retailer mode" : "Multi-retailer mode"}>
              <ViewModuleIcon
                sx={{
                  color: multiRetailerMode ? 'primary.main' : 'action.disabled',
                  cursor: 'pointer',
                  ml: 1,
                  '&:hover': {
                    color: 'primary.main',
                  },
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  setMultiRetailerMode(!multiRetailerMode);
                  if (!multiRetailerMode) {
                    // Entering multi-mode: select current retailer
                    if (selectedRetailer) {
                      setSelectedRetailers([selectedRetailer]);
                    } else {
                      setSelectedRetailers([]);
                    }
                  } else {
                    // Exiting multi-mode: select first retailer
                    if (selectedRetailers && selectedRetailers.length > 0) {
                      setSelectedRetailer(selectedRetailers[0]);
                    } else {
                      setSelectedRetailer('HP'); // Default to HomePro
                    }
                  }
                }}
              />
            </Tooltip>
          </>
        ),
      }}
      fullWidth={fullWidth}
    />
  );

  const renderTags = (value: any[], getTagProps: any) => {
    return value.map((option, index) => {
      const stats = getRetailerStats(option.code);
      return (
        <Chip
          {...getTagProps({ index })}
          key={option.code}
          avatar={
            <Avatar sx={{ bgcolor: retailerColors[option.code] }}>
              {retailerLogos[option.code]}
            </Avatar>
          }
          label={`${option.name} (${stats?.actual_products?.toLocaleString() || 0})`}
          size="small"
          sx={{
            bgcolor: `${retailerColors[option.code]}15`,
            '& .MuiChip-deleteIcon': {
              color: retailerColors[option.code],
            },
          }}
        />
      );
    });
  };

  if (multiRetailerMode) {
    return (
      <Autocomplete
        multiple
        options={activeRetailers}
        getOptionLabel={(option) => option.name}
        value={selectedMultipleRetailers}
        onChange={handleMultiRetailerChange}
        renderOption={renderOption}
        renderInput={renderInput}
        renderTags={renderTags}
        fullWidth={fullWidth}
        size="small"
        isOptionEqualToValue={(option, value) => option.code === value.code}
        ChipProps={{
          size: 'small',
        }}
      />
    );
  }

  return (
    <Autocomplete
      options={activeRetailers}
      getOptionLabel={(option) => option.name}
      value={selectedSingleRetailer}
      onChange={handleSingleRetailerChange}
      renderOption={renderOption}
      renderInput={renderInput}
      fullWidth={fullWidth}
      size="small"
      isOptionEqualToValue={(option, value) => option?.code === value?.code}
    />
  );
};

export default FilterableRetailerSelector;