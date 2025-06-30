import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Container,
  Typography,
  Paper,
  TextField,
  Switch,
  FormControlLabel,
  Button,
  Alert,
  Divider,
  Grid,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Schedule as ScheduleIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayArrowIcon,
  Refresh as RefreshIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { configApi, scheduleApi } from '../services/api';
import {
  ScheduleType,
  TaskType,
  ScheduleResponse,
  ScheduleCreate,
  ScheduleUpdate,
  IntervalSchedule,
  getTaskTypeLabel,
  formatInterval,
  getStatusColor,
} from '../types/schedule';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState(0);
  const [formData, setFormData] = useState({
    scraping_enabled: true,
    max_concurrent_jobs: 5,
    default_max_pages: 10,
    rate_limit_delay: 5,
  });
  const [saved, setSaved] = useState(false);
  
  // Schedule management state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState<ScheduleResponse | null>(null);
  const [scheduleFormData, setScheduleFormData] = useState<Partial<ScheduleCreate>>({
    task_name: '',
    task_type: TaskType.CATEGORY_MONITOR,
    description: '',
    schedule_type: ScheduleType.INTERVAL,
    schedule_value: { hours: 6 },
    task_params: {},
    enabled: true,
  });
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const queryClient = useQueryClient();

  // Fetch current config
  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const response = await configApi.get();
      return response.data;
    },
  });

  // Update form data when config changes
  React.useEffect(() => {
    if (config) {
      setFormData({
        scraping_enabled: config.scraping_enabled,
        max_concurrent_jobs: config.max_concurrent_jobs,
        default_max_pages: config.default_max_pages,
        rate_limit_delay: config.rate_limit_delay,
      });
    }
  }, [config]);

  // Fetch schedules
  const { data: schedules = [], isLoading: schedulesLoading, refetch: refetchSchedules } = useQuery<ScheduleResponse[]>({
    queryKey: ['schedules'],
    queryFn: async () => {
      const response = await scheduleApi.getAll();
      return response.data;
    },
  });

  // Update config mutation
  const updateMutation = useMutation({
    mutationFn: (data: any) => configApi.update(data),
  });

  // Reset config mutation
  const resetMutation = useMutation({
    mutationFn: async () => {
      const result = await configApi.reset();
      window.location.reload();
      return result;
    },
  });

  // Schedule mutations
  const createScheduleMutation = useMutation({
    mutationFn: (data: ScheduleCreate) => scheduleApi.create(data),
  });

  const updateScheduleMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ScheduleUpdate }) =>
      scheduleApi.update(id, data),
  });

  const toggleScheduleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      scheduleApi.toggle(id, enabled),
  });

  const deleteScheduleMutation = useMutation({
    mutationFn: (id: string) => scheduleApi.delete(id),
  });

  const runScheduleMutation = useMutation({
    mutationFn: (id: string) => scheduleApi.runNow(id),
  });

  const handleSave = () => {
    updateMutation.mutate(formData, {
      onSuccess: () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      },
    });
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleAddSchedule = () => {
    setSelectedSchedule(null);
    resetScheduleForm();
    setEditDialogOpen(true);
  };

  const handleEditSchedule = (schedule: ScheduleResponse) => {
    setSelectedSchedule(schedule);
    setScheduleFormData({
      task_name: schedule.task_name,
      task_type: schedule.task_type,
      description: schedule.description,
      schedule_type: schedule.schedule_type,
      schedule_value: schedule.schedule_value,
      task_params: schedule.task_params,
      enabled: schedule.enabled,
    });
    setEditDialogOpen(true);
  };

  const handleDeleteSchedule = (id: string) => {
    if (window.confirm('Are you sure you want to delete this schedule?')) {
      deleteScheduleMutation.mutate(id, {
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['schedules'] });
          setSnackbar({
            open: true,
            message: 'Schedule deleted successfully',
            severity: 'success',
          });
        },
      });
    }
  };

  const handleToggleSchedule = (id: string, enabled: boolean) => {
    toggleScheduleMutation.mutate({ id, enabled }, {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['schedules'] });
        setSnackbar({
          open: true,
          message: 'Schedule status updated',
          severity: 'success',
        });
      },
    });
  };

  const handleRunSchedule = (id: string) => {
    runScheduleMutation.mutate(id, {
      onSuccess: () => {
        setSnackbar({
          open: true,
          message: 'Schedule task started',
          severity: 'success',
        });
      },
    });
  };

  const handleSaveSchedule = () => {
    if (selectedSchedule) {
      const updateData: ScheduleUpdate = {
        description: scheduleFormData.description,
        schedule_type: scheduleFormData.schedule_type,
        schedule_value: scheduleFormData.schedule_value,
        task_params: scheduleFormData.task_params,
        enabled: scheduleFormData.enabled,
      };
      updateScheduleMutation.mutate({ id: selectedSchedule.id!, data: updateData }, {
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['schedules'] });
          setEditDialogOpen(false);
          setSnackbar({
            open: true,
            message: 'Schedule updated successfully',
            severity: 'success',
          });
          resetScheduleForm();
        },
        onError: (error: any) => {
          setSnackbar({
            open: true,
            message: error.response?.data?.detail || 'Failed to update schedule',
            severity: 'error',
          });
        },
      });
    } else {
      createScheduleMutation.mutate(scheduleFormData as ScheduleCreate, {
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['schedules'] });
          setEditDialogOpen(false);
          setSnackbar({
            open: true,
            message: 'Schedule created successfully',
            severity: 'success',
          });
          resetScheduleForm();
        },
        onError: (error: any) => {
          setSnackbar({
            open: true,
            message: error.response?.data?.detail || 'Failed to create schedule',
            severity: 'error',
          });
        },
      });
    }
  };

  const resetScheduleForm = () => {
    setScheduleFormData({
      task_name: '',
      task_type: TaskType.CATEGORY_MONITOR,
      description: '',
      schedule_type: ScheduleType.INTERVAL,
      schedule_value: { hours: 6 },
      task_params: {},
      enabled: true,
    });
    setSelectedSchedule(null);
  };

  const updateIntervalValue = (field: keyof IntervalSchedule, value: number) => {
    const interval = (scheduleFormData.schedule_value as IntervalSchedule) || {};
    setScheduleFormData({
      ...scheduleFormData,
      schedule_value: {
        ...interval,
        [field]: value || undefined,
      },
    });
  };

  if (configLoading || schedulesLoading) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure system settings and automation schedules
        </Typography>
      </Box>

      {saved && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Settings saved successfully!
        </Alert>
      )}

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab icon={<SettingsIcon />} label="General" />
          <Tab icon={<ScheduleIcon />} label="Schedules" />
        </Tabs>

        <TabPanel value={activeTab} index={0}>
          {/* General Settings */}
          <Grid container spacing={3} sx={{ px: 2 }}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Scraping Configuration
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.scraping_enabled}
                      onChange={(e) => setFormData({
                        ...formData,
                        scraping_enabled: e.target.checked,
                      })}
                    />
                  }
                  label="Enable Scraping"
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  type="number"
                  label="Max Concurrent Jobs"
                  value={formData.max_concurrent_jobs}
                  onChange={(e) => setFormData({
                    ...formData,
                    max_concurrent_jobs: parseInt(e.target.value) || 1,
                  })}
                  inputProps={{ min: 1, max: 10 }}
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  type="number"
                  label="Default Max Pages"
                  value={formData.default_max_pages}
                  onChange={(e) => setFormData({
                    ...formData,
                    default_max_pages: parseInt(e.target.value) || 1,
                  })}
                  inputProps={{ min: 1, max: 100 }}
                  sx={{ mb: 2 }}
                />

                <TextField
                  fullWidth
                  type="number"
                  label="Rate Limit Delay (seconds)"
                  value={formData.rate_limit_delay}
                  onChange={(e) => setFormData({
                    ...formData,
                    rate_limit_delay: parseInt(e.target.value) || 1,
                  })}
                  inputProps={{ min: 1, max: 60 }}
                  helperText="Delay between requests to avoid rate limiting"
                />
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Environment Information
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Current Environment
                  </Typography>
                  <Typography variant="body1">
                    {config?.current_environment || 'development'}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    API Endpoint
                  </Typography>
                  <Typography variant="body1">
                    {process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Available Environments
                  </Typography>
                  <Typography variant="body1">
                    {config?.environments?.join(', ') || 'development, staging, production'}
                  </Typography>
                </Box>
              </Paper>
            </Grid>

            <Grid item xs={12}>
              <Paper sx={{ p: 3 }}>
                <Box display="flex" gap={2}>
                  <Button
                    variant="contained"
                    onClick={handleSave}
                    disabled={updateMutation.isPending}
                  >
                    Save Settings
                  </Button>
                  <Button
                    variant="outlined"
                    color="warning"
                    onClick={() => resetMutation.mutate()}
                    disabled={resetMutation.isPending}
                  >
                    Reset to Defaults
                  </Button>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {/* Schedule Management */}
          <Box sx={{ px: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">Monitoring Schedules</Typography>
              <Box>
                <IconButton onClick={() => refetchSchedules()} sx={{ mr: 1 }}>
                  <RefreshIcon />
                </IconButton>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={handleAddSchedule}
                >
                  Add Schedule
                </Button>
              </Box>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Task Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Schedule</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Last Run</TableCell>
                    <TableCell>Next Run</TableCell>
                    <TableCell align="center">Enabled</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {schedules.map((schedule) => (
                    <TableRow key={schedule.id}>
                      <TableCell>
                        <Typography variant="subtitle2">{schedule.task_name}</Typography>
                        {schedule.description && (
                          <Typography variant="caption" color="text.secondary">
                            {schedule.description}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getTaskTypeLabel(schedule.task_type)}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={0.5}>
                          <TimerIcon fontSize="small" color="action" />
                          <Typography variant="body2">
                            {schedule.schedule_type === ScheduleType.INTERVAL
                              ? formatInterval(schedule.schedule_value as IntervalSchedule)
                              : 'Cron: ' + schedule.schedule_value}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {schedule.last_status && (
                          <Chip
                            label={schedule.last_status}
                            size="small"
                            color={getStatusColor(schedule.last_status)}
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        {schedule.last_run ? (
                          <Typography variant="caption">
                            {format(new Date(schedule.last_run), 'MMM d, HH:mm')}
                          </Typography>
                        ) : (
                          <Typography variant="caption" color="text.secondary">
                            Never
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {schedule.next_run ? (
                          <Typography
                            variant="caption"
                            color={schedule.is_overdue ? 'error' : 'inherit'}
                          >
                            {format(new Date(schedule.next_run), 'MMM d, HH:mm')}
                          </Typography>
                        ) : (
                          <Typography variant="caption" color="text.secondary">
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        <Switch
                          checked={schedule.enabled}
                          onChange={(e) => handleToggleSchedule(schedule.id!, e.target.checked)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Box>
                          <Tooltip title="Run Now">
                            <IconButton
                              size="small"
                              onClick={() => handleRunSchedule(schedule.id!)}
                              disabled={!schedule.enabled}
                            >
                              <PlayArrowIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit">
                            <IconButton
                              size="small"
                              onClick={() => handleEditSchedule(schedule)}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteSchedule(schedule.id!)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {schedules.length === 0 && (
              <Box textAlign="center" py={4}>
                <Typography variant="body2" color="text.secondary">
                  No schedules configured. Add a schedule to automate monitoring tasks.
                </Typography>
              </Box>
            )}
          </Box>
        </TabPanel>
      </Paper>

      {/* Edit/Create Schedule Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedSchedule ? 'Edit Schedule' : 'Create Schedule'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  label="Task Name"
                  fullWidth
                  value={scheduleFormData.task_name}
                  onChange={(e) => setScheduleFormData({ ...scheduleFormData, task_name: e.target.value })}
                  disabled={!!selectedSchedule}
                  helperText={selectedSchedule ? "Task name cannot be changed" : "Unique identifier for this schedule"}
                />
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Task Type</InputLabel>
                  <Select
                    value={scheduleFormData.task_type}
                    onChange={(e) => setScheduleFormData({ ...scheduleFormData, task_type: e.target.value as TaskType })}
                    label="Task Type"
                  >
                    <MenuItem value={TaskType.CATEGORY_MONITOR}>Category Monitoring</MenuItem>
                    <MenuItem value={TaskType.PRODUCT_SCRAPE} disabled>Product Scraping (Coming Soon)</MenuItem>
                    <MenuItem value={TaskType.PRICE_UPDATE} disabled>Price Update (Coming Soon)</MenuItem>
                    <MenuItem value={TaskType.INVENTORY_CHECK} disabled>Inventory Check (Coming Soon)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  label="Description"
                  fullWidth
                  multiline
                  rows={2}
                  value={scheduleFormData.description || ''}
                  onChange={(e) => setScheduleFormData({ ...scheduleFormData, description: e.target.value })}
                />
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Schedule Type</InputLabel>
                  <Select
                    value={scheduleFormData.schedule_type}
                    onChange={(e) => setScheduleFormData({ 
                      ...scheduleFormData, 
                      schedule_type: e.target.value as ScheduleType,
                      schedule_value: e.target.value === ScheduleType.INTERVAL 
                        ? { hours: 6 } 
                        : { minute: '0', hour: '*/6', day_of_week: '*', day_of_month: '*', month_of_year: '*' }
                    })}
                    label="Schedule Type"
                  >
                    <MenuItem value={ScheduleType.INTERVAL}>Interval</MenuItem>
                    <MenuItem value={ScheduleType.CRON} disabled>Cron Expression (Coming Soon)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {scheduleFormData.schedule_type === ScheduleType.INTERVAL && (
                <>
                  <Grid item xs={3}>
                    <TextField
                      label="Days"
                      type="number"
                      fullWidth
                      InputProps={{ inputProps: { min: 0 } }}
                      value={(scheduleFormData.schedule_value as IntervalSchedule)?.days || ''}
                      onChange={(e) => updateIntervalValue('days', parseInt(e.target.value) || 0)}
                    />
                  </Grid>
                  <Grid item xs={3}>
                    <TextField
                      label="Hours"
                      type="number"
                      fullWidth
                      InputProps={{ inputProps: { min: 0 } }}
                      value={(scheduleFormData.schedule_value as IntervalSchedule)?.hours || ''}
                      onChange={(e) => updateIntervalValue('hours', parseInt(e.target.value) || 0)}
                    />
                  </Grid>
                  <Grid item xs={3}>
                    <TextField
                      label="Minutes"
                      type="number"
                      fullWidth
                      InputProps={{ inputProps: { min: 0 } }}
                      value={(scheduleFormData.schedule_value as IntervalSchedule)?.minutes || ''}
                      onChange={(e) => updateIntervalValue('minutes', parseInt(e.target.value) || 0)}
                    />
                  </Grid>
                  <Grid item xs={3}>
                    <TextField
                      label="Seconds"
                      type="number"
                      fullWidth
                      InputProps={{ inputProps: { min: 0 } }}
                      value={(scheduleFormData.schedule_value as IntervalSchedule)?.seconds || ''}
                      onChange={(e) => updateIntervalValue('seconds', parseInt(e.target.value) || 0)}
                    />
                  </Grid>
                </>
              )}

              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={scheduleFormData.enabled}
                      onChange={(e) => setScheduleFormData({ ...scheduleFormData, enabled: e.target.checked })}
                    />
                  }
                  label="Enabled"
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSaveSchedule}
            variant="contained"
            disabled={!scheduleFormData.task_name || (scheduleFormData.schedule_type === ScheduleType.INTERVAL && 
              !Object.values((scheduleFormData.schedule_value as IntervalSchedule) || {}).some(v => v > 0))}
          >
            {selectedSchedule ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}