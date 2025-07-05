import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  IconButton,
  LinearProgress,
  Grid,
  Container,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import {
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  RocketLaunch as RocketLaunchIcon,
} from '@mui/icons-material';
import { scrapingApi } from '../services/api';
import ScrapingWizard from '../components/scraping/ScrapingWizard';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function Scraping() {
  const queryClient = useQueryClient();
  const [tabValue, setTabValue] = useState(0);
  const [openWizard, setOpenWizard] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [newJobForm, setNewJobForm] = useState({
    job_type: 'category',
    target_url: '',
    urls: [] as string[],
    max_pages: 5,
  });

  // Fetch jobs
  const { data: jobsData, isLoading } = useQuery({
    queryKey: ['scraping-jobs', tabValue],
    queryFn: async () => {
      const status = tabValue === 0 ? undefined : tabValue === 1 ? 'running' : 'completed';
      const response = await scrapingApi.listJobs(status);
      return response.data;
    },
    refetchInterval: tabValue === 1 ? 5000 : false, // Auto-refresh running jobs
  });

  // Create job mutation
  const createJobMutation = useMutation({
    mutationFn: (data: any) => scrapingApi.createJob(data),
    onSuccess: () => {
      setOpenDialog(false);
      queryClient.invalidateQueries({ queryKey: ['scraping-jobs'] });
      setNewJobForm({
        job_type: 'category',
        target_url: '',
        urls: [],
        max_pages: 5,
      });
    },
  });

  // Create batch job mutation for wizard
  const createBatchJobMutation = useMutation({
    mutationFn: async (data: any) => {
      // For now, create individual jobs for each category
      // In the future, this would be a single batch endpoint
      const { retailer_code, category_codes, max_pages } = data;
      
      // Get categories from the API (they're already cached in the wizard)
      const categoriesData = queryClient.getQueryData<any[]>(['retailer-categories', retailer_code]);
      const categories = categoriesData || [];
      
      const jobs = category_codes.map((categoryCode: string) => {
        const category = categories.find(c => c.code === categoryCode);
        return scrapingApi.createJob({
          job_type: 'category',
          target_url: category?.url || '',
          max_pages: max_pages,
          retailer_code: retailer_code,
          category_code: categoryCode,
        });
      });
      
      return Promise.all(jobs);
    },
    onSuccess: () => {
      setOpenWizard(false);
      queryClient.invalidateQueries({ queryKey: ['scraping-jobs'] });
    },
  });

  // Cancel job mutation
  const cancelJobMutation = useMutation({
    mutationFn: (jobId: string) => scrapingApi.cancelJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scraping-jobs'] });
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'default';
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      default: return 'default';
    }
  };

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'Job ID', width: 100 },
    { field: 'job_type', headerName: 'Type', width: 100 },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={getStatusColor(params.value)}
          size="small"
        />
      ),
    },
    { field: 'target_url', headerName: 'Target URL', flex: 1 },
    {
      field: 'progress',
      headerName: 'Progress',
      width: 200,
      renderCell: (params) => {
        const total = params.row.total_items || 0;
        const processed = params.row.processed_items || 0;
        const percentage = total > 0 ? (processed / total) * 100 : 0;
        
        return (
          <Box sx={{ width: '100%' }}>
            <LinearProgress
              variant="determinate"
              value={percentage}
              sx={{ height: 8, borderRadius: 4 }}
            />
            <Typography variant="caption">
              {processed}/{total} ({percentage.toFixed(0)}%)
            </Typography>
          </Box>
        );
      },
    },
    {
      field: 'success_rate',
      headerName: 'Success Rate',
      width: 120,
      renderCell: (params) => {
        const success = params.row.success_items || 0;
        const failed = params.row.failed_items || 0;
        const total = success + failed;
        const rate = total > 0 ? (success / total) * 100 : 0;
        
        return (
          <Typography color={rate > 80 ? 'success.main' : 'error.main'}>
            {rate.toFixed(1)}%
          </Typography>
        );
      },
    },
    { field: 'created_at', headerName: 'Created', width: 150 },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      renderCell: (params) => (
        <Box>
          {params.row.status === 'running' && (
            <IconButton
              size="small"
              onClick={() => cancelJobMutation.mutate(params.row.id)}
              disabled={cancelJobMutation.isPending}
              title="Cancel Job"
            >
              <StopIcon />
            </IconButton>
          )}
          {(params.row.status === 'failed' || params.row.status === 'completed') && (
            <IconButton 
              size="small" 
              onClick={() => {
                // Create a new job with the same parameters
                const retryData = {
                  job_type: params.row.job_type,
                  target_url: params.row.target_url,
                  retailer_code: params.row.retailer_code || 'TWD',
                  max_pages: params.row.max_pages || 5,
                  urls: params.row.urls || []
                };
                createJobMutation.mutate(retryData);
              }}
              disabled={createJobMutation.isPending}
              title="Retry Job"
            >
              <RefreshIcon />
            </IconButton>
          )}
        </Box>
      ),
    },
  ];

  const handleCreateJob = () => {
    const jobData = {
      ...newJobForm,
      urls: newJobForm.job_type === 'product' ? newJobForm.urls : undefined,
    };
    createJobMutation.mutate(jobData);
  };

  return (
    <Container maxWidth="xl">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Scraping Jobs</Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            startIcon={<RocketLaunchIcon />}
            onClick={() => setOpenWizard(true)}
            sx={{
              background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
              boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)',
            }}
          >
            Start Scraping
          </Button>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => setOpenDialog(true)}
          >
            Classic Mode
          </Button>
        </Box>
      </Box>

      {/* Stats */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="textSecondary">
              Total Jobs
            </Typography>
            <Typography variant="h4">{jobsData?.total || 0}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="textSecondary">
              Active Jobs
            </Typography>
            <Typography variant="h4" color="primary.main">
              {jobsData?.active_jobs || 0}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="textSecondary">
              Completed
            </Typography>
            <Typography variant="h4" color="success.main">
              {jobsData?.completed_jobs || 0}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="textSecondary">
              Failed
            </Typography>
            <Typography variant="h4" color="error.main">
              {jobsData?.failed_jobs || 0}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Jobs Table */}
      <Paper>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="All Jobs" />
          <Tab label="Running" />
          <Tab label="Completed" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <DataGrid
            rows={jobsData?.jobs || []}
            columns={columns}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 10, page: 0 },
              },
            }}
            pageSizeOptions={[10, 25, 50]}
            loading={isLoading}
            autoHeight
            disableRowSelectionOnClick
          />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <DataGrid
            rows={jobsData?.jobs?.filter((job: any) => job.status === 'running') || []}
            columns={columns}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 10, page: 0 },
              },
            }}
            pageSizeOptions={[10, 25, 50]}
            loading={isLoading}
            autoHeight
            disableRowSelectionOnClick
          />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <DataGrid
            rows={jobsData?.jobs?.filter((job: any) => job.status === 'completed') || []}
            columns={columns}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 10, page: 0 },
              },
            }}
            pageSizeOptions={[10, 25, 50]}
            loading={isLoading}
            autoHeight
            disableRowSelectionOnClick
          />
        </TabPanel>
      </Paper>

      {/* Scraping Wizard */}
      <ScrapingWizard
        open={openWizard}
        onClose={() => setOpenWizard(false)}
        onSubmit={(jobData) => createBatchJobMutation.mutate(jobData)}
        isSubmitting={createBatchJobMutation.isPending}
      />

      {/* Create Job Dialog (Classic Mode) */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Scraping Job</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Job Type</InputLabel>
              <Select
                value={newJobForm.job_type}
                onChange={(e) => setNewJobForm({ ...newJobForm, job_type: e.target.value })}
              >
                <MenuItem value="category">Category Scraping</MenuItem>
                <MenuItem value="product">Product Scraping</MenuItem>
                <MenuItem value="search">Search Results</MenuItem>
              </Select>
            </FormControl>

            {newJobForm.job_type === 'product' ? (
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Product URLs (one per line)"
                value={newJobForm.urls.join('\n')}
                onChange={(e) => setNewJobForm({
                  ...newJobForm,
                  urls: e.target.value.split('\n').filter(url => url.trim()),
                })}
                sx={{ mb: 2 }}
              />
            ) : (
              <TextField
                fullWidth
                label="Target URL"
                placeholder="https://www.homepro.co.th/c/electrical"
                value={newJobForm.target_url}
                onChange={(e) => setNewJobForm({ ...newJobForm, target_url: e.target.value })}
                sx={{ mb: 2 }}
              />
            )}

            {newJobForm.job_type !== 'product' && (
              <TextField
                fullWidth
                type="number"
                label="Max Pages"
                value={newJobForm.max_pages}
                onChange={(e) => setNewJobForm({
                  ...newJobForm,
                  max_pages: parseInt(e.target.value) || 5,
                })}
                inputProps={{ min: 1, max: 200 }}
              />
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            onClick={handleCreateJob}
            variant="contained"
            disabled={createJobMutation.isPending}
          >
            Create Job
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}


