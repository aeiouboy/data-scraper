import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Inventory as ProductIcon,
  TrendingUp as TrendingIcon,
  CloudDownload as ScrapingIcon,
  AttachMoney as PriceIcon,
} from '@mui/icons-material';
import { analyticsApi } from '../services/api';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color }) => (
  <Card>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom>
            {title}
          </Typography>
          <Typography variant="h4">
            {value}
          </Typography>
        </Box>
        <Box
          sx={{
            backgroundColor: color,
            borderRadius: '50%',
            width: 56,
            height: 56,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
          }}
        >
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics', 'dashboard'],
    queryFn: async () => {
      const response = await analyticsApi.getDashboard();
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load dashboard data. Please try again later.
      </Alert>
    );
  }

  const stats = data?.product_stats || {};

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Stat Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Products"
            value={stats.total_products || 0}
            icon={<ProductIcon />}
            color="#3f51b5"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Average Price"
            value={`฿${stats.avg_price?.toFixed(2) || 0}`}
            icon={<PriceIcon />}
            color="#4caf50"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Products on Sale"
            value={stats.products_on_sale || 0}
            icon={<TrendingIcon />}
            color="#ff9800"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Brands"
            value={stats.total_brands || 0}
            icon={<ScrapingIcon />}
            color="#f44336"
          />
        </Grid>

        {/* Charts Section */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Daily Scraping Activity
            </Typography>
            <Box height={300} display="flex" alignItems="center" justifyContent="center">
              <Typography color="textSecondary">
                Chart will be implemented here
              </Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Top Brands
            </Typography>
            <Box>
              {data?.brand_distribution?.slice(0, 5).map((brand: any, index: number) => (
                <Box key={index} display="flex" justifyContent="space-between" py={1}>
                  <Typography>{brand.brand}</Typography>
                  <Typography color="textSecondary">{brand.count}</Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Price Distribution */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Price Distribution
            </Typography>
            <Box>
              {Object.entries(data?.price_distribution || {}).map(([range, count]) => (
                <Box key={range} display="flex" justifyContent="space-between" py={1}>
                  <Typography>฿{range}</Typography>
                  <Typography color="textSecondary">{count as number}</Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Scraping Jobs
            </Typography>
            <Box>
              {data?.daily_stats?.slice(0, 5).map((stat: any, index: number) => (
                <Box key={index} display="flex" justifyContent="space-between" py={1}>
                  <Typography>{stat.date}</Typography>
                  <Typography color={stat.avg_success_rate > 80 ? 'success.main' : 'error.main'}>
                    {stat.avg_success_rate?.toFixed(1)}% success
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}