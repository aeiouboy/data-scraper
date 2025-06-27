import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Switch,
  FormControlLabel,
  Button,
  Alert,
  Divider,
  Grid,
} from '@mui/material';
import { configApi } from '../services/api';

export default function Settings() {
  const [formData, setFormData] = useState({
    scraping_enabled: true,
    max_concurrent_jobs: 5,
    default_max_pages: 10,
    rate_limit_delay: 5,
  });
  const [saved, setSaved] = useState(false);

  // Fetch current config
  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const response = await configApi.get();
      return response.data;
    },
    onSuccess: (data) => {
      setFormData({
        scraping_enabled: data.scraping_enabled,
        max_concurrent_jobs: data.max_concurrent_jobs,
        default_max_pages: data.default_max_pages,
        rate_limit_delay: data.rate_limit_delay,
      });
    },
  });

  // Update config mutation
  const updateMutation = useMutation({
    mutationFn: (data: any) => configApi.update(data),
    onSuccess: () => {
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  // Reset config mutation
  const resetMutation = useMutation({
    mutationFn: () => configApi.reset(),
    onSuccess: () => {
      window.location.reload();
    },
  });

  const handleSave = () => {
    updateMutation.mutate(formData);
  };

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      {saved && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Settings saved successfully!
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Scraping Settings */}
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

        {/* Environment Info */}
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

        {/* Actions */}
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
    </Box>
  );
}