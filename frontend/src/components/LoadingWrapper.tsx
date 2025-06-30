import React from 'react';
import { Box, CircularProgress, Typography, Fade } from '@mui/material';

interface LoadingWrapperProps {
  loading: boolean;
  error?: Error | null;
  children: React.ReactNode;
  loadingText?: string;
  minHeight?: string | number;
}

const LoadingWrapper: React.FC<LoadingWrapperProps> = ({
  loading,
  error,
  children,
  loadingText = 'Loading...',
  minHeight = '200px',
}) => {
  if (loading) {
    return (
      <Fade in>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight,
            gap: 2,
          }}
        >
          <CircularProgress />
          <Typography variant="body2" color="text.secondary">
            {loadingText}
          </Typography>
        </Box>
      </Fade>
    );
  }

  if (error) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight,
          p: 3,
        }}
      >
        <Typography color="error" align="center">
          {error.message || 'An error occurred'}
        </Typography>
      </Box>
    );
  }

  return <>{children}</>;
};

export default LoadingWrapper;