import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  TextField,
  Checkbox,
  Button,
  Paper,
  Grid,
  Chip,
  InputAdornment,
  Collapse,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  CheckBox as CheckBoxIcon,
  CheckBoxOutlineBlank as CheckBoxOutlineBlankIcon,
} from '@mui/icons-material';

interface Category {
  code: string;
  name: string;
  name_th: string;
  url: string;
  estimated_products?: number;
}

interface CategorySelectorProps {
  categories: Category[];
  selectedCategories: string[];
  onCategoryChange: (categories: string[]) => void;
  retailerName: string;
}

export default function CategorySelector({
  categories,
  selectedCategories,
  onCategoryChange,
  retailerName,
}: CategorySelectorProps) {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredCategories = useMemo(() => {
    if (!searchTerm) return categories;
    
    const term = searchTerm.toLowerCase();
    return categories.filter(
      cat => 
        cat.name.toLowerCase().includes(term) ||
        cat.name_th.toLowerCase().includes(term) ||
        cat.code.toLowerCase().includes(term)
    );
  }, [categories, searchTerm]);

  const handleSelectAll = () => {
    onCategoryChange(filteredCategories.map(cat => cat.code));
  };

  const handleSelectNone = () => {
    onCategoryChange([]);
  };

  const handleToggleCategory = (categoryCode: string) => {
    if (selectedCategories.includes(categoryCode)) {
      onCategoryChange(selectedCategories.filter(code => code !== categoryCode));
    } else {
      onCategoryChange([...selectedCategories, categoryCode]);
    }
  };

  const totalProductsEstimate = useMemo(() => {
    return selectedCategories.reduce((total, code) => {
      const category = categories.find(cat => cat.code === code);
      return total + (category?.estimated_products || 0);
    }, 0);
  }, [selectedCategories, categories]);

  const estimatedTime = useMemo(() => {
    // Rough estimate: 500 products per hour
    const hours = totalProductsEstimate / 500;
    if (hours < 1) return `~${Math.round(hours * 60)} minutes`;
    return `~${Math.round(hours)} hours`;
  }, [totalProductsEstimate]);


  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Select Categories to Scrape
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Choose which product categories from {retailerName} you want to scrape
      </Typography>

      <Box sx={{ mt: 3, mb: 2 }}>
        <TextField
          fullWidth
          placeholder="Search categories..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />

        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Button
              size="small"
              onClick={handleSelectAll}
              startIcon={<CheckBoxIcon />}
              sx={{ mr: 1 }}
            >
              Select All
            </Button>
            <Button
              size="small"
              onClick={handleSelectNone}
              startIcon={<CheckBoxOutlineBlankIcon />}
            >
              Select None
            </Button>
          </Box>
          <Typography variant="body2" color="text.secondary">
            {selectedCategories.length} of {categories.length} selected
          </Typography>
        </Box>

        <Collapse in={selectedCategories.length > 0}>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Estimated:</strong> {totalProductsEstimate.toLocaleString()} products 
              • {estimatedTime} to complete
            </Typography>
          </Alert>
        </Collapse>

        <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto', p: 1 }}>
          <Grid container spacing={1}>
            {filteredCategories.map((category) => (
              <Grid item xs={12} sm={6} key={category.code}>
                <Paper
                  sx={{
                    p: 1.5,
                    cursor: 'pointer',
                    bgcolor: selectedCategories.includes(category.code) 
                      ? 'action.selected' 
                      : 'background.paper',
                    '&:hover': {
                      bgcolor: selectedCategories.includes(category.code)
                        ? 'action.selected'
                        : 'action.hover',
                    },
                    transition: 'background-color 0.2s',
                  }}
                  onClick={() => handleToggleCategory(category.code)}
                >
                  <Box display="flex" alignItems="center">
                    <Checkbox
                      checked={selectedCategories.includes(category.code)}
                      onChange={() => handleToggleCategory(category.code)}
                      onClick={(e) => e.stopPropagation()}
                      size="small"
                    />
                    <Box flex={1}>
                      <Typography variant="body2" fontWeight="medium">
                        {category.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {category.name_th}
                      </Typography>
                      {category.estimated_products && (
                        <Typography variant="caption" display="block" color="text.secondary">
                          ~{category.estimated_products.toLocaleString()} products
                        </Typography>
                      )}
                    </Box>
                    <Chip
                      label={category.code}
                      size="small"
                      variant="outlined"
                      sx={{ ml: 1 }}
                    />
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Paper>

        {filteredCategories.length === 0 && (
          <Box textAlign="center" py={4}>
            <Typography color="text.secondary">
              No categories found matching "{searchTerm}"
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
}