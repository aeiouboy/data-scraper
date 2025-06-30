import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Typography,
  Box,
  Chip,
  Avatar,
  Grow,
} from '@mui/material';
import {
  Store as StoreIcon,
  Construction as ConstructionIcon,
  Home as HomeIcon,
  Kitchen as KitchenIcon,
  Build as BuildIcon,
  Warehouse as WarehouseIcon,
} from '@mui/icons-material';

interface Retailer {
  code: string;
  name: string;
  market_position: string;
  estimated_products: number;
  focus_categories: string[];
  is_active: boolean;
}

interface RetailerSelectorProps {
  retailers: Retailer[];
  selectedRetailer: string | null;
  onSelectRetailer: (retailerCode: string) => void;
}

const retailerIcons: Record<string, React.ReactElement> = {
  HP: <HomeIcon />,
  TWD: <ConstructionIcon />,
  GH: <StoreIcon />,
  DH: <BuildIcon />,
  BT: <KitchenIcon />,
  MH: <WarehouseIcon />,
};

const retailerColors: Record<string, string> = {
  HP: '#1976d2',
  TWD: '#f57c00',
  GH: '#388e3c',
  DH: '#d32f2f',
  BT: '#7b1fa2',
  MH: '#455a64',
};

export default function RetailerSelector({
  retailers,
  selectedRetailer,
  onSelectRetailer,
}: RetailerSelectorProps) {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Select a Retailer to Scrape
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Choose which retailer's website you want to scrape products from
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 1 }}>
        {retailers.map((retailer, index) => (
          <Grid item xs={12} sm={6} md={4} key={retailer.code}>
            <Grow in timeout={200 + index * 100}>
              <Card
                sx={{
                  height: '100%',
                  position: 'relative',
                  border: selectedRetailer === retailer.code ? 2 : 1,
                  borderColor: selectedRetailer === retailer.code 
                    ? retailerColors[retailer.code] 
                    : 'divider',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
              >
                <CardActionArea
                  onClick={() => onSelectRetailer(retailer.code)}
                  disabled={!retailer.is_active}
                  sx={{ height: '100%' }}
                >
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                      <Avatar
                        sx={{
                          bgcolor: retailerColors[retailer.code],
                          width: 56,
                          height: 56,
                          mr: 2,
                        }}
                      >
                        {retailerIcons[retailer.code] || <StoreIcon />}
                      </Avatar>
                      <Box>
                        <Typography variant="h6" component="h3">
                          {retailer.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {retailer.market_position}
                        </Typography>
                      </Box>
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" mb={2}>
                      ~{retailer.estimated_products.toLocaleString()} products
                    </Typography>
                    
                    <Box>
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        Specializes in:
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={0.5} mt={0.5}>
                        {retailer.focus_categories.map((category) => (
                          <Chip
                            key={category}
                            label={category}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem' }}
                          />
                        ))}
                      </Box>
                    </Box>
                    
                    {selectedRetailer === retailer.code && (
                      <Box
                        sx={{
                          position: 'absolute',
                          top: 8,
                          right: 8,
                          width: 24,
                          height: 24,
                          borderRadius: '50%',
                          bgcolor: retailerColors[retailer.code],
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <Typography
                          variant="caption"
                          sx={{ color: 'white', fontWeight: 'bold' }}
                        >
                          ✓
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grow>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}