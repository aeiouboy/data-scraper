import React from 'react';
import {
  Box,
  Chip,
  Tooltip,
  Typography,
  Alert,
  Stack,
} from '@mui/material';
import {
  CheckCircle as ValidIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

interface MatchValidationIndicatorProps {
  confidence: number;
  matchType: string;
  rejectionReasons?: string[];
  warnings?: string[];
  matchedFields?: string[];
  details?: {
    sku_score?: number;
    brand_score?: number;
    name_score?: number;
    spec_score?: number;
    category_score?: number;
  };
}

const MatchValidationIndicator: React.FC<MatchValidationIndicatorProps> = ({
  confidence,
  matchType,
  rejectionReasons = [],
  warnings = [],
  matchedFields = [],
  details = {},
}) => {
  const getConfidenceColor = (score: number) => {
    if (score >= 0.85) return 'success';
    if (score >= 0.70) return 'info';
    if (score >= 0.50) return 'warning';
    return 'error';
  };

  const getMatchTypeIcon = (type: string) => {
    switch (type) {
      case 'exact':
        return <ValidIcon color="success" />;
      case 'high':
        return <ValidIcon color="info" />;
      case 'medium':
        return <WarningIcon color="warning" />;
      case 'low':
        return <ErrorIcon color="warning" />;
      case 'none':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon color="action" />;
    }
  };

  const getMatchTypeLabel = (type: string) => {
    const labels = {
      exact: 'Exact Match',
      high: 'High Confidence',
      medium: 'Medium Confidence',
      low: 'Low Confidence',
      none: 'No Match',
    };
    return labels[type as keyof typeof labels] || type;
  };

  const hasRejections = rejectionReasons.length > 0;
  const hasWarnings = warnings.length > 0;

  return (
    <Box>
      <Stack direction="row" spacing={1} alignItems="center" mb={1}>
        <Tooltip title={`Confidence: ${(confidence * 100).toFixed(1)}%`}>
          <Chip
            icon={getMatchTypeIcon(matchType)}
            label={`${(confidence * 100).toFixed(1)}%`}
            color={getConfidenceColor(confidence)}
            size="small"
          />
        </Tooltip>
        
        <Typography variant="body2" color="text.secondary">
          {getMatchTypeLabel(matchType)}
        </Typography>
      </Stack>

      {hasRejections && (
        <Alert severity="error" sx={{ mb: 1 }}>
          <Typography variant="body2" fontWeight="bold">
            Match Rejected:
          </Typography>
          {rejectionReasons.map((reason, index) => (
            <Typography key={index} variant="body2" sx={{ mt: 0.5 }}>
              • {reason}
            </Typography>
          ))}
        </Alert>
      )}

      {hasWarnings && (
        <Alert severity="warning" sx={{ mb: 1 }}>
          <Typography variant="body2" fontWeight="bold">
            Warnings:
          </Typography>
          {warnings.map((warning, index) => (
            <Typography key={index} variant="body2" sx={{ mt: 0.5 }}>
              • {warning}
            </Typography>
          ))}
        </Alert>
      )}

      {matchedFields.length > 0 && (
        <Box sx={{ mb: 1 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Matched Fields:
          </Typography>
          <Stack direction="row" spacing={0.5} flexWrap="wrap">
            {matchedFields.map((field) => (
              <Chip
                key={field}
                label={field}
                size="small"
                color="success"
                variant="outlined"
              />
            ))}
          </Stack>
        </Box>
      )}

      {Object.keys(details).length > 0 && (
        <Box sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Score Breakdown:
          </Typography>
          <Stack spacing={0.5}>
            {Object.entries(details).map(([key, value]) => (
              <Box key={key} display="flex" justifyContent="space-between">
                <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                  {key.replace('_', ' ')}:
                </Typography>
                <Chip
                  label={`${(value * 100).toFixed(0)}%`}
                  size="small"
                  color={getConfidenceColor(value)}
                  variant="outlined"
                />
              </Box>
            ))}
          </Stack>
        </Box>
      )}
    </Box>
  );
};

export default MatchValidationIndicator;