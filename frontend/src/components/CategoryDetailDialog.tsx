import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Chip,
  IconButton,
  Divider,
  Stack,
  Alert,
  CircularProgress,
  Paper,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Tooltip,
} from '@mui/material';
import { TreeView, TreeItem } from '@mui/lab';
import {
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Update as UpdateIcon,
  Search as SearchIcon,
  VerifiedUser as VerifiedUserIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Category as CategoryIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';

// TypeScript interfaces
interface Category {
  id: string;
  name: string;
  path: string;
  parent_id: string | null;
  level: number;
  is_active: boolean;
  product_count: number;
  last_scraped: string | null;
  created_at: string;
  updated_at: string;
  children?: Category[];
}

interface HealthMetrics {
  status: 'healthy' | 'warning' | 'error';
  lastScrapedHours: number | null;
  productGrowthRate: number;
  activeProductPercentage: number;
  issues: string[];
}

interface RecentChange {
  id: string;
  type: 'added' | 'removed' | 'updated';
  description: string;
  timestamp: string;
  details?: Record<string, any>;
}

interface CategoryDetailDialogProps {
  open: boolean;
  onClose: () => void;
  category: Category | null;
  onRunDiscovery: (categoryId: string) => Promise<void>;
  onRunVerification: (categoryId: string) => Promise<void>;
}

const CategoryDetailDialog: React.FC<CategoryDetailDialogProps> = ({
  open,
  onClose,
  category,
  onRunDiscovery,
  onRunVerification,
}) => {
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [healthMetrics, setHealthMetrics] = useState<HealthMetrics | null>(null);
  const [recentChanges, setRecentChanges] = useState<RecentChange[]>([]);
  const [expandedNodes, setExpandedNodes] = useState<string[]>([]);

  useEffect(() => {
    if (category) {
      // Load health metrics and recent changes
      loadCategoryDetails();
    }
  }, [category]);

  const loadCategoryDetails = async () => {
    setLoading(true);
    try {
      // Simulate API calls - replace with actual API endpoints
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Mock health metrics
      setHealthMetrics({
        status: category?.product_count === 0 ? 'warning' : 'healthy',
        lastScrapedHours: category?.last_scraped 
          ? Math.floor((Date.now() - new Date(category.last_scraped).getTime()) / (1000 * 60 * 60))
          : null,
        productGrowthRate: 5.2,
        activeProductPercentage: 85.5,
        issues: category?.product_count === 0 ? ['No products found in this category'] : [],
      });

      // Mock recent changes
      setRecentChanges([
        {
          id: '1',
          type: 'added',
          description: '15 new products discovered',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: '2',
          type: 'updated',
          description: 'Category metadata refreshed',
          timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        },
      ]);
    } catch (error) {
      console.error('Failed to load category details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunDiscovery = async () => {
    if (!category) return;
    
    setActionLoading('discovery');
    try {
      await onRunDiscovery(category.id);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRunVerification = async () => {
    if (!category) return;
    
    setActionLoading('verification');
    try {
      await onRunVerification(category.id);
    } finally {
      setActionLoading(null);
    }
  };

  const handleNodeToggle = (event: React.SyntheticEvent, nodeIds: string[]) => {
    setExpandedNodes(nodeIds);
  };

  const renderCategoryTree = (cat: Category): JSX.Element => {
    const hasChildren = cat.children && cat.children.length > 0;
    
    return (
      <TreeItem
        key={cat.id}
        nodeId={cat.id}
        label={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 0.5 }}>
            <Typography variant="body2">{cat.name}</Typography>
            <Chip 
              label={cat.product_count} 
              size="small" 
              color={cat.product_count > 0 ? 'primary' : 'default'}
            />
            {!cat.is_active && (
              <Chip label="Inactive" size="small" color="error" />
            )}
          </Box>
        }
      >
        {hasChildren && cat.children!.map(child => renderCategoryTree(child))}
      </TreeItem>
    );
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon color="success" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return null;
    }
  };

  const getChangeIcon = (type: string) => {
    switch (type) {
      case 'added':
        return <TrendingUpIcon color="success" />;
      case 'removed':
        return <TrendingDownIcon color="error" />;
      case 'updated':
        return <UpdateIcon color="primary" />;
      default:
        return null;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffHours < 48) return 'Yesterday';
    return date.toLocaleDateString();
  };

  if (!category) return null;

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { height: '80vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <CategoryIcon />
            <Typography variant="h6">{category.name}</Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
        <Typography variant="caption" color="text.secondary">
          {category.path}
        </Typography>
      </DialogTitle>

      <DialogContent dividers>
        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : (
          <Stack spacing={3}>
            {/* Health Metrics */}
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  {healthMetrics && getHealthIcon(healthMetrics.status)}
                  <Typography variant="h6">Health Metrics</Typography>
                </Box>
                
                {healthMetrics && (
                  <>
                    {healthMetrics.issues.length > 0 && (
                      <Alert severity="warning" sx={{ mb: 2 }}>
                        {healthMetrics.issues[0]}
                      </Alert>
                    )}
                    
                    <Grid container spacing={2}>
                      <Grid item xs={6} md={3}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="body2" color="text.secondary">
                            Products
                          </Typography>
                          <Typography variant="h4">
                            {category.product_count}
                          </Typography>
                        </Paper>
                      </Grid>
                      
                      <Grid item xs={6} md={3}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="body2" color="text.secondary">
                            Active %
                          </Typography>
                          <Typography variant="h4">
                            {healthMetrics.activeProductPercentage.toFixed(1)}%
                          </Typography>
                        </Paper>
                      </Grid>
                      
                      <Grid item xs={6} md={3}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="body2" color="text.secondary">
                            Growth Rate
                          </Typography>
                          <Typography variant="h4" color={healthMetrics.productGrowthRate >= 0 ? 'success.main' : 'error.main'}>
                            {healthMetrics.productGrowthRate >= 0 ? '+' : ''}{healthMetrics.productGrowthRate.toFixed(1)}%
                          </Typography>
                        </Paper>
                      </Grid>
                      
                      <Grid item xs={6} md={3}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="body2" color="text.secondary">
                            Last Scraped
                          </Typography>
                          <Typography variant="h4">
                            {healthMetrics.lastScrapedHours !== null 
                              ? `${healthMetrics.lastScrapedHours}h`
                              : 'Never'
                            }
                          </Typography>
                        </Paper>
                      </Grid>
                    </Grid>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Category Tree */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Category Structure
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, maxHeight: 300, overflow: 'auto' }}>
                  <TreeView
                    defaultCollapseIcon={<ExpandMoreIcon />}
                    defaultExpandIcon={<ChevronRightIcon />}
                    expanded={expandedNodes}
                    onNodeToggle={handleNodeToggle}
                  >
                    {renderCategoryTree(category)}
                  </TreeView>
                </Paper>
              </CardContent>
            </Card>

            {/* Recent Changes */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Changes
                </Typography>
                <List>
                  {recentChanges.length === 0 ? (
                    <ListItem>
                      <ListItemText 
                        primary="No recent changes"
                        secondary="Category has not been updated recently"
                      />
                    </ListItem>
                  ) : (
                    recentChanges.map(change => (
                      <ListItem key={change.id}>
                        <ListItemIcon>
                          {getChangeIcon(change.type)}
                        </ListItemIcon>
                        <ListItemText
                          primary={change.description}
                          secondary={
                            <Box display="flex" alignItems="center" gap={1}>
                              <ScheduleIcon fontSize="small" />
                              {formatTimestamp(change.timestamp)}
                            </Box>
                          }
                        />
                      </ListItem>
                    ))
                  )}
                </List>
              </CardContent>
            </Card>
          </Stack>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          Close
        </Button>
        <Box flex={1} />
        <Tooltip title="Discover new products in this category">
          <Button
            variant="outlined"
            startIcon={actionLoading === 'discovery' ? <CircularProgress size={20} /> : <SearchIcon />}
            onClick={handleRunDiscovery}
            disabled={!!actionLoading}
          >
            Run Discovery
          </Button>
        </Tooltip>
        <Tooltip title="Verify existing products and update information">
          <Button
            variant="contained"
            startIcon={actionLoading === 'verification' ? <CircularProgress size={20} /> : <VerifiedUserIcon />}
            onClick={handleRunVerification}
            disabled={!!actionLoading}
          >
            Run Verification
          </Button>
        </Tooltip>
      </DialogActions>
    </Dialog>
  );
};

export default CategoryDetailDialog;