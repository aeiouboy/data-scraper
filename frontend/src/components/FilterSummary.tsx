import React from 'react';
import {
  Box,
  Chip,
  Stack,
  Typography,
  Paper,
  Fade,
} from '@mui/material';
import {
  TrendingDown as SavingsIcon,
  Percent as PercentIcon,
  Category as CategoryIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';

interface FilterSummaryProps {
  filters: {
    minSavings: number;
    minSavingsPercent: number;
    category: string;
  };
  totalProducts: number;
  filteredProducts: number;
  onClearFilter: (filterKey: string) => void;
  onClearAll: () => void;
}

export default function FilterSummary({
  filters,
  totalProducts,
  filteredProducts,
  onClearFilter,
  onClearAll,
}: FilterSummaryProps) {
  const activeFilters = [
    filters.minSavings > 0 && {
      key: 'minSavings',
      label: `Min Savings: ฿${filters.minSavings.toLocaleString()}`,
      icon: <SavingsIcon fontSize="small" />,
    },
    filters.minSavingsPercent > 0 && {
      key: 'minSavingsPercent',
      label: `Min Savings: ${filters.minSavingsPercent}%`,
      icon: <PercentIcon fontSize="small" />,
    },
    filters.category && {
      key: 'category',
      label: `Category: ${filters.category}`,
      icon: <CategoryIcon fontSize="small" />,
    },
  ].filter(Boolean);

  if (activeFilters.length === 0) {
    return null;
  }

  const percentageFiltered = totalProducts > 0 
    ? Math.round((filteredProducts / totalProducts) * 100) 
    : 100;

  return (
    <Fade in={activeFilters.length > 0}>
      <Paper
        sx={{
          p: 1.5,
          mb: 2,
          bgcolor: 'primary.50',
          border: 1,
          borderColor: 'primary.200',
        }}
      >
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={2}>
            <Typography variant="body2" color="text.secondary">
              Active Filters:
            </Typography>
            
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {activeFilters.map((filter: any) => (
                <Chip
                  key={filter.key}
                  label={filter.label}
                  icon={filter.icon}
                  onDelete={() => onClearFilter(filter.key)}
                  size="small"
                  color="primary"
                  variant="filled"
                />
              ))}
            </Stack>
          </Stack>

          <Stack direction="row" alignItems="center" spacing={2}>
            <Typography variant="body2" color="text.secondary">
              Showing {filteredProducts} of {totalProducts} products ({percentageFiltered}%)
            </Typography>
            
            {activeFilters.length > 1 && (
              <Chip
                label="Clear All"
                onClick={onClearAll}
                size="small"
                variant="outlined"
                icon={<ClearIcon fontSize="small" />}
              />
            )}
          </Stack>
        </Stack>
      </Paper>
    </Fade>
  );
}