import React from 'react';
import { Box, Typography, Paper, Grid } from '@mui/material';

export default function Analytics() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Analytics
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Price Trends
            </Typography>
            <Box height={400} display="flex" alignItems="center" justifyContent="center">
              <Typography color="textSecondary">
                Analytics charts will be implemented here
              </Typography>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Scraping Performance
            </Typography>
            <Box height={300} display="flex" alignItems="center" justifyContent="center">
              <Typography color="textSecondary">
                Performance metrics will be displayed here
              </Typography>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Category Distribution
            </Typography>
            <Box height={300} display="flex" alignItems="center" justifyContent="center">
              <Typography color="textSecondary">
                Category chart will be displayed here
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}