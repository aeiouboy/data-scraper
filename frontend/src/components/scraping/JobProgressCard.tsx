import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Collapse,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Stop as StopIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  PlayArrow as RunningIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';

interface JobCategory {
  code: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  processed: number;
  total: number;
  success: number;
  failed: number;
}

interface JobProgress {
  id: string;
  retailer_name: string;
  retailer_code: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_categories: number;
  processed_categories: number;
  total_products: number;
  processed_products: number;
  success_products: number;
  failed_products: number;
  started_at?: string;
  completed_at?: string;
  categories: JobCategory[];
}

interface JobProgressCardProps {
  job: JobProgress;
  onCancel?: (jobId: string) => void;
  expanded?: boolean;
}

const statusIcons = {
  pending: <PendingIcon />,
  running: <RunningIcon />,
  completed: <CheckCircleIcon />,
  failed: <ErrorIcon />,
};

const statusColors = {
  pending: 'default',
  running: 'primary',
  completed: 'success',
  failed: 'error',
} as const;

export default function JobProgressCard({
  job,
  onCancel,
  expanded: defaultExpanded = false,
}: JobProgressCardProps) {
  const [expanded, setExpanded] = React.useState(defaultExpanded);

  const overallProgress = job.total_products > 0 
    ? (job.processed_products / job.total_products) * 100 
    : 0;

  const successRate = job.processed_products > 0
    ? (job.success_products / job.processed_products) * 100
    : 0;

  const getElapsedTime = () => {
    if (!job.started_at) return null;
    const start = new Date(job.started_at);
    const end = job.completed_at ? new Date(job.completed_at) : new Date();
    const elapsed = end.getTime() - start.getTime();
    const minutes = Math.floor(elapsed / 60000);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    }
    return `${minutes}m`;
  };

  const getEstimatedTimeRemaining = () => {
    if (job.status !== 'running' || job.processed_products === 0) return null;
    
    const elapsedMs = new Date().getTime() - new Date(job.started_at!).getTime();
    const avgTimePerProduct = elapsedMs / job.processed_products;
    const remainingProducts = job.total_products - job.processed_products;
    const remainingMs = avgTimePerProduct * remainingProducts;
    
    const minutes = Math.ceil(remainingMs / 60000);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `~${hours}h ${minutes % 60}m remaining`;
    }
    return `~${minutes}m remaining`;
  };

  return (
    <Card 
      sx={{ 
        mb: 2,
        border: job.status === 'running' ? 2 : 1,
        borderColor: job.status === 'running' ? 'primary.main' : 'divider',
        transition: 'all 0.3s ease',
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={2}>
            <Chip
              icon={statusIcons[job.status]}
              label={job.status.toUpperCase()}
              color={statusColors[job.status]}
              size="small"
            />
            <Typography variant="h6">
              {job.retailer_name}
            </Typography>
            {job.status === 'running' && (
              <Box display="flex" alignItems="center">
                <CircularProgress size={16} sx={{ mr: 0.5 }} />
                <Typography variant="caption" color="text.secondary">
                  {job.processed_categories}/{job.total_categories} categories
                </Typography>
              </Box>
            )}
          </Box>
          
          <Box display="flex" alignItems="center" gap={1}>
            {getElapsedTime() && (
              <Chip
                icon={<ScheduleIcon />}
                label={getElapsedTime()}
                size="small"
                variant="outlined"
              />
            )}
            {job.status === 'running' && onCancel && (
              <Tooltip title="Cancel job">
                <IconButton
                  size="small"
                  onClick={() => onCancel(job.id)}
                  color="error"
                >
                  <StopIcon />
                </IconButton>
              </Tooltip>
            )}
            <IconButton
              size="small"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
        </Box>

        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" mb={0.5}>
            <Typography variant="body2" color="text.secondary">
              Overall Progress
            </Typography>
            <Typography variant="body2">
              {job.processed_products.toLocaleString()}/{job.total_products.toLocaleString()} products
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={overallProgress}
            sx={{ height: 8, borderRadius: 4 }}
          />
          {job.status === 'running' && getEstimatedTimeRemaining() && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
              {getEstimatedTimeRemaining()}
            </Typography>
          )}
        </Box>

        <Box display="flex" justifyContent="space-around">
          <Box textAlign="center">
            <Typography variant="h6" color="success.main">
              {job.success_products.toLocaleString()}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Successful
            </Typography>
          </Box>
          <Divider orientation="vertical" flexItem />
          <Box textAlign="center">
            <Typography variant="h6" color="error.main">
              {job.failed_products.toLocaleString()}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Failed
            </Typography>
          </Box>
          <Divider orientation="vertical" flexItem />
          <Box textAlign="center">
            <Typography variant="h6" color={successRate > 90 ? 'success.main' : 'warning.main'}>
              {successRate.toFixed(1)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Success Rate
            </Typography>
          </Box>
        </Box>

        <Collapse in={expanded}>
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" gutterBottom>
            Category Progress:
          </Typography>
          <List dense>
            {job.categories.map((category) => {
              const categoryProgress = category.total > 0
                ? (category.processed / category.total) * 100
                : 0;
              
              return (
                <ListItem key={category.code}>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Chip
                          icon={statusIcons[category.status]}
                          label={category.name}
                          size="small"
                          variant="outlined"
                          color={statusColors[category.status]}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {category.processed}/{category.total}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <LinearProgress
                        variant="determinate"
                        value={categoryProgress}
                        sx={{ height: 4, borderRadius: 2, mt: 1 }}
                      />
                    }
                  />
                </ListItem>
              );
            })}
          </List>
        </Collapse>
      </CardContent>
    </Card>
  );
}