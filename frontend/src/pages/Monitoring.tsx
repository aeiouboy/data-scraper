import React, { useState } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  IconButton,
  Alert,
  useTheme,
  alpha,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Button,
  Snackbar,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Speed as SpeedIcon,
  Category as CategoryIcon,
  AutoMode as AutoModeIcon,
  ChangeCircle as ChangeCircleIcon,
  PlayArrow as PlayArrowIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { format } from 'date-fns';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';
import { scrapingApi, categoryApi } from '../services/api';
import { useCategoryMonitoring } from '../hooks/useCategoryMonitoring';
import CategoryDetailDialog from '../components/CategoryDetailDialog';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend
);

interface HealthMetrics {
  overall_health: 'healthy' | 'warning' | 'critical';
  success_rate_24h: number;
  success_rate_7d: number;
  avg_response_time: number;
  total_jobs_24h: number;
  failed_jobs_24h: number;
  active_jobs: number;
  queue_size: number;
  last_updated: string;
}

interface RetailerHealth {
  retailer_code: string;
  retailer_name: string;
  status: 'healthy' | 'warning' | 'critical' | 'offline';
  success_rate: number;
  avg_response_time: number;
  last_successful_scrape: string | null;
  error_count_24h: number;
  products_scraped_24h: number;
}

interface JobMetrics {
  hour: string;
  successful: number;
  failed: number;
  avg_duration: number;
}

interface CategoryHealthByRetailer {
  retailer_code: string;
  retailer_name: string;
  total_categories: number;
  avg_health_score: number;
  categories_with_issues: number;
  auto_discovered_percentage: number;
  last_category_update: string;
}

const retailerMapping: Record<string, string> = {
  'HP': 'HomePro',
  'TWD': 'Thai Watsadu',  
  'GH': 'Global House',
  'DH': 'DoHome',
  'BT': 'Boonthavorn',
  'MH': 'MegaHome',
};

export default function Monitoring() {
  const theme = useTheme();
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedRetailerCode, setSelectedRetailerCode] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });
  
  // Initialize category monitoring hook
  const {
    categoryChanges,
    aggregateStats,
    isLoadingHealth: isLoadingCategoryHealth,
    refreshAll: refreshCategoryData,
  } = useCategoryMonitoring();

  // Category monitoring mutation
  const runMonitoringMutation = useMutation({
    mutationFn: () => categoryApi.triggerMonitor(), // No retailer code means monitor all retailers
    onSuccess: () => {
      setSnackbar({
        open: true,
        message: 'Category monitoring started successfully',
        severity: 'success',
      });
      // Refresh data after a short delay
      setTimeout(() => {
        refreshCategoryData();
      }, 2000);
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to start category monitoring',
        severity: 'error',
      });
    },
  });

  // Fetch health metrics
  const { data: healthMetrics, refetch: refetchHealth } = useQuery<HealthMetrics>({
    queryKey: ['health-metrics'],
    queryFn: async () => {
      const response = await scrapingApi.getHealthMetrics();
      return response.data;
    },
    refetchInterval: autoRefresh ? 30000 : false, // Refresh every 30 seconds
  });

  // Fetch retailer health
  const { data: retailerHealth = [], isLoading: isLoadingRetailerHealth, isError: isRetailerHealthError } = useQuery<RetailerHealth[]>({
    queryKey: ['retailer-health'],
    queryFn: async () => {
      const response = await scrapingApi.getRetailerHealth();
      return response.data;
    },
    refetchInterval: autoRefresh ? 30000 : false,
  });

  // Fetch job metrics for charts
  const { data: jobMetrics = [] } = useQuery<JobMetrics[]>({
    queryKey: ['job-metrics'],
    queryFn: async () => {
      const response = await scrapingApi.getJobMetrics();
      return response.data;
    },
    refetchInterval: autoRefresh ? 60000 : false, // Refresh every minute
  });

  // Fetch category health by retailer
  const { data: categoryHealthByRetailer = [], isLoading: isCategoryHealthLoading } = useQuery<CategoryHealthByRetailer[]>({
    queryKey: ['category-health-by-retailer'],
    queryFn: async () => {
      try {
        // Get category stats which includes retailer information
        const response = await categoryApi.getStats();
        const stats = response.data;
        
        // Transform the stats into the expected format
        if (stats?.retailer_stats) {
          return Object.entries(stats.retailer_stats).map(([code, data]: [string, any]) => ({
            retailer_code: code,
            retailer_name: retailerMapping[code] || code,
            total_categories: data.total || 0,
            avg_health_score: data.active > 0 ? (data.active / data.total) * 100 : 0,
            categories_with_issues: data.inactive || 0,
            auto_discovered_percentage: data.auto_discovered > 0 ? (data.auto_discovered / data.total) * 100 : 0,
            last_category_update: new Date().toISOString(), // This would come from the API ideally
          }));
        }
        return [];
      } catch (error) {
        console.error('Error fetching category health by retailer:', error);
        return [];
      }
    },
    refetchInterval: autoRefresh ? 60000 : false,
  });

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return theme.palette.success.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'critical':
        return theme.palette.error.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon color="success" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'critical':
        return <ErrorIcon color="error" />;
      default:
        return <ScheduleIcon color="disabled" />;
    }
  };

  // Chart data
  const successRateChartData = {
    labels: jobMetrics.map(m => m.hour),
    datasets: [
      {
        label: 'Success Rate %',
        data: jobMetrics.map(m => 
          m.successful + m.failed > 0 
            ? (m.successful / (m.successful + m.failed)) * 100 
            : 0
        ),
        borderColor: theme.palette.success.main,
        backgroundColor: alpha(theme.palette.success.main, 0.1),
        tension: 0.4,
      },
    ],
  };

  const jobVolumeChartData = {
    labels: jobMetrics.map(m => m.hour),
    datasets: [
      {
        label: 'Successful Jobs',
        data: jobMetrics.map(m => m.successful),
        backgroundColor: theme.palette.success.main,
      },
      {
        label: 'Failed Jobs',
        data: jobMetrics.map(m => m.failed),
        backgroundColor: theme.palette.error.main,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const handleRetailerClick = (retailerCode: string) => {
    setSelectedRetailerCode(retailerCode);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setSelectedRetailerCode(null);
  };

  const handleRunDiscovery = async (categoryId: string) => {
    if (!selectedRetailerCode) return;
    
    try {
      await categoryApi.triggerDiscovery({
        retailer_code: selectedRetailerCode,
        max_depth: 3,
      });
      setSnackbar({
        open: true,
        message: 'Category discovery started successfully',
        severity: 'success',
      });
      // Refresh data after a short delay
      setTimeout(() => {
        refreshCategoryData();
      }, 2000);
    } catch (error: any) {
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to start category discovery',
        severity: 'error',
      });
    }
  };

  const handleRunVerification = async (categoryId: string) => {
    if (!selectedRetailerCode) return;
    
    try {
      await categoryApi.verifyCategory(categoryId);
      setSnackbar({
        open: true,
        message: 'Category verification started successfully',
        severity: 'success',
      });
      // Refresh data after a short delay
      setTimeout(() => {
        refreshCategoryData();
      }, 2000);
    } catch (error: any) {
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to start category verification',
        severity: 'error',
      });
    }
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" gutterBottom>
          Scraping Health Monitor
        </Typography>
        <Box>
          <Tooltip title="Refresh data">
            <IconButton onClick={() => {
              refetchHealth();
              refreshCategoryData();
            }}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Chip
            label={autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
            color={autoRefresh ? 'primary' : 'default'}
            onClick={() => setAutoRefresh(!autoRefresh)}
            sx={{ ml: 2 }}
          />
        </Box>
      </Box>

      {/* Overall Health Status */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    System Health
                  </Typography>
                  <Typography variant="h5">
                    {healthMetrics?.overall_health || 'Unknown'}
                  </Typography>
                </Box>
                {healthMetrics && getHealthIcon(healthMetrics.overall_health)}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    24h Success Rate
                  </Typography>
                  <Typography variant="h5">
                    {healthMetrics?.success_rate_24h?.toFixed(1) || '0.0'}%
                  </Typography>
                </Box>
                {healthMetrics && healthMetrics.success_rate_24h > 95 ? (
                  <TrendingUpIcon color="success" />
                ) : (
                  <TrendingDownIcon color="error" />
                )}
              </Box>
              <LinearProgress
                variant="determinate"
                value={healthMetrics?.success_rate_24h || 0}
                sx={{ mt: 1 }}
                color={
                  !healthMetrics ? 'inherit' :
                  healthMetrics.success_rate_24h > 95 
                    ? 'success' 
                    : healthMetrics.success_rate_24h > 85 
                    ? 'warning' 
                    : 'error'
                }
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Jobs
                  </Typography>
                  <Typography variant="h5">
                    {healthMetrics?.active_jobs || 0}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Queue: {healthMetrics?.queue_size || 0}
                  </Typography>
                </Box>
                <SpeedIcon color="primary" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Avg Response Time
                  </Typography>
                  <Typography variant="h5">
                    {healthMetrics?.avg_response_time?.toFixed(1) || '0.0'}s
                  </Typography>
                </Box>
                <ScheduleIcon color="action" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 300 }}>
            <Typography variant="h6" gutterBottom>
              Success Rate Trend (24h)
            </Typography>
            <Box sx={{ height: 240 }}>
              <Line data={successRateChartData} options={chartOptions} />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 300 }}>
            <Typography variant="h6" gutterBottom>
              Job Volume (24h)
            </Typography>
            <Box sx={{ height: 240 }}>
              <Bar data={jobVolumeChartData} options={chartOptions} />
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Retailer Health Table */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Retailer Health Status
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Retailer</TableCell>
                <TableCell align="center">Status</TableCell>
                <TableCell align="right">Success Rate</TableCell>
                <TableCell align="right">Avg Response</TableCell>
                <TableCell align="right">Products (24h)</TableCell>
                <TableCell align="right">Errors (24h)</TableCell>
                <TableCell>Last Success</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoadingRetailerHealth ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    Loading retailer health data...
                  </TableCell>
                </TableRow>
              ) : isRetailerHealthError ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Alert severity="error" sx={{ justifyContent: 'center' }}>
                      Failed to load retailer health data. Please check if the API server is running.
                    </Alert>
                  </TableCell>
                </TableRow>
              ) : retailerHealth.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="textSecondary">
                      No retailer data available. Run some scraping jobs to see health metrics.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                retailerHealth.map((retailer) => (
                <TableRow key={retailer.retailer_code}>
                  <TableCell>
                    <Typography variant="subtitle2">{retailer.retailer_name}</Typography>
                    <Typography variant="caption" color="textSecondary">
                      {retailer.retailer_code}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={retailer.status}
                      size="small"
                      sx={{
                        backgroundColor: alpha(getHealthColor(retailer.status), 0.1),
                        color: getHealthColor(retailer.status),
                      }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Typography
                      color={
                        retailer.success_rate > 95
                          ? 'success.main'
                          : retailer.success_rate > 85
                          ? 'warning.main'
                          : 'error.main'
                      }
                    >
                      {retailer.success_rate.toFixed(1)}%
                    </Typography>
                  </TableCell>
                  <TableCell align="right">{retailer.avg_response_time.toFixed(1)}s</TableCell>
                  <TableCell align="right">{retailer.products_scraped_24h.toLocaleString()}</TableCell>
                  <TableCell align="right">
                    <Typography color={retailer.error_count_24h > 0 ? 'error' : 'inherit'}>
                      {retailer.error_count_24h}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {retailer.last_successful_scrape ? (
                      <Typography variant="caption">
                        {format(new Date(retailer.last_successful_scrape), 'MMM d, HH:mm')}
                      </Typography>
                    ) : (
                      <Typography variant="caption" color="textSecondary">
                        Never
                      </Typography>
                    )}
                  </TableCell>
                </TableRow>
              ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Category Health Overview */}
      <Box sx={{ mt: 4, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Category Monitoring
        </Typography>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Categories
                  </Typography>
                  <Typography variant="h5">
                    {aggregateStats.totalCategories}
                  </Typography>
                </Box>
                <CategoryIcon color="primary" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Category Changes
                  </Typography>
                  <Typography variant="h5">
                    {categoryChanges?.length || 0}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Last 7 days
                  </Typography>
                </Box>
                <ChangeCircleIcon color="warning" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Auto-Discovered
                  </Typography>
                  <Typography variant="h5">
                    {categoryHealthByRetailer.length > 0
                      ? Math.round(
                          categoryHealthByRetailer.reduce((sum, r) => sum + r.auto_discovered_percentage, 0) /
                          categoryHealthByRetailer.length
                        )
                      : 0}%
                  </Typography>
                </Box>
                <AutoModeIcon color="success" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Categories with Issues
                  </Typography>
                  <Typography variant="h5">
                    {aggregateStats.categoriesWithIssues}
                  </Typography>
                  <Typography variant="caption" color="error">
                    {aggregateStats.highSeverityIssues} high severity
                  </Typography>
                </Box>
                <WarningIcon color="error" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Run Category Monitor button card */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
                <Typography color="textSecondary" gutterBottom align="center">
                  Run Category Monitor
                </Typography>
                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  startIcon={runMonitoringMutation.isPending ? <CircularProgress size={20} color="inherit" /> : <PlayArrowIcon />}
                  onClick={() => runMonitoringMutation.mutate()}
                  disabled={runMonitoringMutation.isPending}
                  fullWidth
                >
                  {runMonitoringMutation.isPending ? 'Running...' : 'Start Monitor'}
                </Button>
                <Typography variant="caption" color="textSecondary" align="center">
                  Scan all retailers for category changes
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Category Health by Retailer */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Category Health by Retailer
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Retailer</TableCell>
                <TableCell align="center">Total Categories</TableCell>
                <TableCell align="center">Avg Health Score</TableCell>
                <TableCell align="center">Categories with Issues</TableCell>
                <TableCell align="center">Auto-Discovered</TableCell>
                <TableCell>Last Category Update</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isCategoryHealthLoading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <CircularProgress size={20} />
                  </TableCell>
                </TableRow>
              ) : categoryHealthByRetailer && categoryHealthByRetailer.length > 0 ? (
                categoryHealthByRetailer.map((retailer) => (
                <TableRow key={retailer.retailer_code}>
                  <TableCell>
                    <Box
                      onClick={() => handleRetailerClick(retailer.retailer_code)}
                      sx={{
                        cursor: 'pointer',
                        '&:hover': {
                          '& .MuiTypography-subtitle2': {
                            color: theme.palette.primary.main,
                            textDecoration: 'underline',
                          },
                        },
                      }}
                    >
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <Box>
                          <Typography variant="subtitle2">{retailer.retailer_name}</Typography>
                          <Typography variant="caption" color="textSecondary">
                            {retailer.retailer_code}
                          </Typography>
                        </Box>
                        <OpenInNewIcon fontSize="small" sx={{ color: 'action.active' }} />
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell align="center">{retailer.total_categories}</TableCell>
                  <TableCell align="center">
                    <Box display="flex" alignItems="center" justifyContent="center">
                      <Typography
                        color={
                          retailer.avg_health_score > 80
                            ? 'success.main'
                            : retailer.avg_health_score > 60
                            ? 'warning.main'
                            : 'error.main'
                        }
                      >
                        {retailer.avg_health_score.toFixed(1)}%
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    <Typography color={retailer.categories_with_issues > 0 ? 'error' : 'inherit'}>
                      {retailer.categories_with_issues}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={`${retailer.auto_discovered_percentage.toFixed(0)}%`}
                      size="small"
                      color={retailer.auto_discovered_percentage > 75 ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell>
                    {retailer.last_category_update ? (
                      <Typography variant="caption">
                        {format(new Date(retailer.last_category_update), 'MMM d, HH:mm')}
                      </Typography>
                    ) : (
                      <Typography variant="caption" color="textSecondary">
                        Never
                      </Typography>
                    )}
                  </TableCell>
                </TableRow>
              ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography variant="body2" color="textSecondary">
                      No category health data available
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Recent Category Changes */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Recent Category Changes
        </Typography>
        {isLoadingCategoryHealth ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : categoryChanges && categoryChanges.length > 0 ? (
          <List>
            {categoryChanges.slice(0, 10).map((change, index) => (
              <React.Fragment key={change.id}>
                <ListItem>
                  <ListItemIcon>
                    {change.change_type === 'price_increase' ? (
                      <TrendingUpIcon color="error" />
                    ) : change.change_type === 'price_decrease' ? (
                      <TrendingDownIcon color="success" />
                    ) : change.change_type === 'new_products' ? (
                      <CheckCircleIcon color="primary" />
                    ) : (
                      <ErrorIcon color="warning" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Typography variant="subtitle2">
                          {change.category_name}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {format(new Date(change.change_date), 'MMM d, HH:mm')}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          {change.change_type.replace(/_/g, ' ').charAt(0).toUpperCase() + 
                           change.change_type.replace(/_/g, ' ').slice(1)}
                        </Typography>
                        {change.details.percentage_change && (
                          <Chip
                            label={`${change.details.percentage_change > 0 ? '+' : ''}${change.details.percentage_change.toFixed(1)}%`}
                            size="small"
                            color={change.details.percentage_change > 0 ? 'error' : 'success'}
                            sx={{ mt: 0.5 }}
                          />
                        )}
                        {change.details.product_count && (
                          <Typography variant="caption" color="textSecondary" sx={{ ml: 1 }}>
                            {change.details.product_count} products affected
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
                {index < categoryChanges.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        ) : (
          <Alert severity="info">
            No category changes detected in the selected time range
          </Alert>
        )}
      </Paper>

      {/* Last Updated */}
      {healthMetrics && (
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="caption" color="textSecondary">
            Last updated: {format(new Date(healthMetrics.last_updated), 'PPpp')}
          </Typography>
        </Box>
      )}

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Category Detail Dialog */}
      <CategoryDetailDialog
        open={dialogOpen}
        onClose={handleDialogClose}
        category={
          selectedRetailerCode && categoryHealthByRetailer.find(r => r.retailer_code === selectedRetailerCode)
            ? {
                id: selectedRetailerCode,
                name: categoryHealthByRetailer.find(r => r.retailer_code === selectedRetailerCode)!.retailer_name,
                path: categoryHealthByRetailer.find(r => r.retailer_code === selectedRetailerCode)!.retailer_name,
                parent_id: null,
                level: 0,
                is_active: true,
                product_count: categoryHealthByRetailer.find(r => r.retailer_code === selectedRetailerCode)!.total_categories,
                last_scraped: categoryHealthByRetailer.find(r => r.retailer_code === selectedRetailerCode)!.last_category_update,
                created_at: new Date().toISOString(),
                updated_at: categoryHealthByRetailer.find(r => r.retailer_code === selectedRetailerCode)!.last_category_update || new Date().toISOString(),
              }
            : null
        }
        onRunDiscovery={handleRunDiscovery}
        onRunVerification={handleRunVerification}
      />
    </Container>
  );
}