import React, { useState } from 'react';
import {
  Box,
  Paper,
  Stack,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Button,
  IconButton,
  Collapse,
  Typography,
  Slider,
  Grid,
  Divider,
  Badge,
} from '@mui/material';
import {
  FilterList as FilterIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  TrendingDown as SavingsIcon,
  Percent as PercentIcon,
  Category as CategoryIcon,
} from '@mui/icons-material';

interface PriceComparisonFiltersProps {
  minSavings: number;
  minSavingsPercent: number;
  minConfidence: number;
  category: string;
  categories: Array<{ category: string; productCount: number }>;
  onMinSavingsChange: (value: number) => void;
  onMinSavingsPercentChange: (value: number) => void;
  onMinConfidenceChange: (value: number) => void;
  onCategoryChange: (value: string) => void;
  onClearFilters: () => void;
}

export default function PriceComparisonFilters({
  minSavings,
  minSavingsPercent,
  minConfidence,
  category,
  categories,
  onMinSavingsChange,
  onMinSavingsPercentChange,
  onMinConfidenceChange,
  onCategoryChange,
  onClearFilters,
}: PriceComparisonFiltersProps) {
  const [expanded, setExpanded] = useState(false);
  const [savingsRange, setSavingsRange] = useState<number[]>([0, 10000]);
  const [percentRange, setPercentRange] = useState<number[]>([0, 50]);
  const [confidenceRange, setConfidenceRange] = useState<number[]>([0.5, 1]);

  // Count active filters
  const activeFilterCount = [
    minSavings > 0,
    minSavingsPercent > 0,
    minConfidence > 0.5,
    category !== '',
  ].filter(Boolean).length;

  const handleSavingsRangeChange = (_: any, newValue: number | number[]) => {
    setSavingsRange(newValue as number[]);
  };

  const handleSavingsRangeCommit = () => {
    onMinSavingsChange(savingsRange[0]);
  };

  const handlePercentRangeChange = (_: any, newValue: number | number[]) => {
    setPercentRange(newValue as number[]);
  };

  const handlePercentRangeCommit = () => {
    onMinSavingsPercentChange(percentRange[0]);
  };

  const handleClearAll = () => {
    setSavingsRange([0, 10000]);
    setPercentRange([0, 50]);
    setConfidenceRange([0.5, 1]);
    onClearFilters();
  };

  // Quick filter presets
  const applyPreset = (preset: { savings?: number; percent?: number; categoryVal?: string }) => {
    if (preset.savings !== undefined) {
      onMinSavingsChange(preset.savings);
      setSavingsRange([preset.savings, 10000]);
    }
    if (preset.percent !== undefined) {
      onMinSavingsPercentChange(preset.percent);
      setPercentRange([preset.percent, 50]);
    }
    if (preset.categoryVal !== undefined) {
      onCategoryChange(preset.categoryVal);
    }
  };

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Stack spacing={2}>
        {/* Header */}
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={1}>
            <FilterIcon color="action" />
            <Typography variant="h6">Filters</Typography>
            {activeFilterCount > 0 && (
              <Badge badgeContent={activeFilterCount} color="primary">
                <Box />
              </Badge>
            )}
          </Stack>
          
          <Stack direction="row" spacing={1}>
            {activeFilterCount > 0 && (
              <Button
                size="small"
                startIcon={<ClearIcon />}
                onClick={handleClearAll}
              >
                Clear All
              </Button>
            )}
            
            <IconButton
              size="small"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? <CollapseIcon /> : <ExpandIcon />}
            </IconButton>
          </Stack>
        </Stack>

        {/* Quick Presets */}
        <Stack direction="row" spacing={1} flexWrap="wrap">
          <Chip
            label="Best Deals (20%+ off)"
            onClick={() => applyPreset({ percent: 20 })}
            size="small"
            variant="outlined"
            clickable
          />
          <Chip
            label="Big Savings (฿1000+)"
            onClick={() => applyPreset({ savings: 1000 })}
            size="small"
            variant="outlined"
            clickable
          />
          <Chip
            label="Small Savings"
            onClick={() => applyPreset({ savings: 100, percent: 5 })}
            size="small"
            variant="outlined"
            clickable
          />
        </Stack>

        {/* Active Filters Display */}
        {activeFilterCount > 0 && (
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {minSavings > 0 && (
              <Chip
                label={`Min: ฿${minSavings.toLocaleString()}`}
                onDelete={() => {
                  onMinSavingsChange(0);
                  setSavingsRange([0, 10000]);
                }}
                size="small"
                color="primary"
              />
            )}
            {minSavingsPercent > 0 && (
              <Chip
                label={`Min: ${minSavingsPercent}%`}
                onDelete={() => {
                  onMinSavingsPercentChange(0);
                  setPercentRange([0, 50]);
                }}
                size="small"
                color="primary"
              />
            )}
            {minConfidence > 0.5 && (
              <Chip
                label={`Confidence: ${(minConfidence * 100).toFixed(0)}%`}
                onDelete={() => {
                  onMinConfidenceChange(0.5);
                  setConfidenceRange([0.5, 1]);
                }}
                size="small"
                color="primary"
              />
            )}
            {category && (
              <Chip
                label={category}
                onDelete={() => onCategoryChange('')}
                size="small"
                color="primary"
              />
            )}
          </Stack>
        )}

        <Divider />

        {/* Basic Filters */}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              label="Minimum Savings (฿)"
              type="number"
              value={minSavings}
              onChange={(e) => {
                const val = Number(e.target.value);
                onMinSavingsChange(val);
                setSavingsRange([val, 10000]);
              }}
              size="small"
              fullWidth
              InputProps={{
                startAdornment: <SavingsIcon sx={{ mr: 1, color: 'action.active' }} />,
              }}
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              label="Minimum Savings %"
              type="number"
              value={minSavingsPercent}
              onChange={(e) => {
                const val = Number(e.target.value);
                onMinSavingsPercentChange(val);
                setPercentRange([val, 50]);
              }}
              size="small"
              fullWidth
              InputProps={{
                startAdornment: <PercentIcon sx={{ mr: 1, color: 'action.active' }} />,
              }}
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <FormControl size="small" fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={category}
                onChange={(e) => onCategoryChange(e.target.value)}
                label="Category"
                startAdornment={<CategoryIcon sx={{ ml: 1, mr: -0.5, color: 'action.active' }} />}
              >
                <MenuItem value="">All Categories</MenuItem>
                {categories.map((cat) => (
                  <MenuItem key={cat.category} value={cat.category}>
                    <Stack direction="row" justifyContent="space-between" width="100%">
                      <span>{cat.category}</span>
                      <Typography variant="caption" color="text.secondary">
                        ({cat.productCount})
                      </Typography>
                    </Stack>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {/* Advanced Filters - Collapsible */}
        <Collapse in={expanded}>
          <Stack spacing={3} sx={{ mt: 2 }}>
            <Divider />
            
            {/* Savings Amount Slider */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Minimum Savings Amount
              </Typography>
              <Box sx={{ px: 2 }}>
                <Slider
                  value={savingsRange}
                  onChange={handleSavingsRangeChange}
                  onChangeCommitted={handleSavingsRangeCommit}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `฿${value.toLocaleString()}`}
                  min={0}
                  max={10000}
                  step={100}
                  marks={[
                    { value: 0, label: '฿0' },
                    { value: 2500, label: '฿2.5k' },
                    { value: 5000, label: '฿5k' },
                    { value: 7500, label: '฿7.5k' },
                    { value: 10000, label: '฿10k+' },
                  ]}
                />
              </Box>
            </Box>

            {/* Savings Percentage Slider */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Minimum Savings Percentage
              </Typography>
              <Box sx={{ px: 2 }}>
                <Slider
                  value={percentRange}
                  onChange={handlePercentRangeChange}
                  onChangeCommitted={handlePercentRangeCommit}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${value}%`}
                  min={0}
                  max={50}
                  step={5}
                  marks={[
                    { value: 0, label: '0%' },
                    { value: 10, label: '10%' },
                    { value: 20, label: '20%' },
                    { value: 30, label: '30%' },
                    { value: 40, label: '40%' },
                    { value: 50, label: '50%+' },
                  ]}
                />
              </Box>
            </Box>

            {/* Match Confidence Slider */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Minimum Match Confidence
              </Typography>
              <Box sx={{ px: 2 }}>
                <Slider
                  value={confidenceRange}
                  onChange={(_, newValue) => setConfidenceRange(newValue as number[])}
                  onChangeCommitted={() => onMinConfidenceChange(confidenceRange[0])}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
                  min={0.5}
                  max={1}
                  step={0.05}
                  marks={[
                    { value: 0.5, label: '50%' },
                    { value: 0.6, label: '60%' },
                    { value: 0.7, label: '70%' },
                    { value: 0.8, label: '80%' },
                    { value: 0.9, label: '90%' },
                    { value: 1, label: '100%' },
                  ]}
                />
              </Box>
            </Box>

            {/* Category Breakdown */}
            {categories.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Categories with Savings
                </Typography>
                <Grid container spacing={1}>
                  {categories.slice(0, 6).map((cat) => (
                    <Grid item xs={6} sm={4} md={2} key={cat.category}>
                      <Paper
                        sx={{
                          p: 1,
                          textAlign: 'center',
                          cursor: 'pointer',
                          bgcolor: category === cat.category ? 'primary.light' : 'background.paper',
                          color: category === cat.category ? 'primary.contrastText' : 'text.primary',
                          '&:hover': {
                            bgcolor: category === cat.category ? 'primary.main' : 'action.hover',
                          },
                        }}
                        onClick={() => onCategoryChange(cat.category === category ? '' : cat.category)}
                      >
                        <Typography variant="caption" display="block">
                          {cat.category}
                        </Typography>
                        <Typography variant="h6">
                          {cat.productCount}
                        </Typography>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            )}
          </Stack>
        </Collapse>
      </Stack>
    </Paper>
  );
}