/**
 * Ultra-Strict Match Validation Indicator Component
 * Displays detailed validation results from ultra-strict matching
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Grid,
  LinearProgress,
  Tooltip,
  Alert,
  IconButton,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Collapse
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Search as SearchIcon,
  Speed as SpeedIcon,
  Verified as VerifiedIcon
} from '@mui/icons-material';
import {
  UltraStrictMatchResult,
  ultraStrictMatchingApi
} from '../services/ultraStrictMatchingApi';

interface UltraStrictMatchValidationIndicatorProps {
  result: UltraStrictMatchResult;
  showDetails?: boolean;
  compact?: boolean;
  onDetailsToggle?: (expanded: boolean) => void;
}

const UltraStrictMatchValidationIndicator: React.FC<UltraStrictMatchValidationIndicatorProps> = ({
  result,
  showDetails = false,
  compact = false,
  onDetailsToggle
}) => {
  const [expanded, setExpanded] = useState(showDetails);
  const [showScoreBreakdown, setShowScoreBreakdown] = useState(false);

  const handleExpandClick = () => {
    const newExpanded = !expanded;
    setExpanded(newExpanded);
    onDetailsToggle?.(newExpanded);
  };

  const { confidence, match_type, ultra_strict_details, warnings, rejection_reasons } = result;
  const matchQuality = ultraStrictMatchingApi.calculateMatchQuality(result);
  const confidenceColor = ultraStrictMatchingApi.getConfidenceColor(confidence, match_type);
  const validationIcon = ultraStrictMatchingApi.getValidationIcon(ultra_strict_details);

  // Determine overall status
  const getOverallStatus = () => {
    if (match_type === 'exact') return 'excellent';
    if (match_type === 'high') return 'good';
    if (match_type === 'medium') return 'fair';
    if (match_type === 'low') return 'poor';
    return 'rejected';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return '#4CAF50';
      case 'good': return '#2196F3';
      case 'fair': return '#FF9800';
      case 'poor': return '#FF5722';
      case 'rejected': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'excellent': return <VerifiedIcon sx={{ color: '#4CAF50' }} />;
      case 'good': return <CheckCircleIcon sx={{ color: '#2196F3' }} />;
      case 'fair': return <WarningIcon sx={{ color: '#FF9800' }} />;
      case 'poor': return <ErrorIcon sx={{ color: '#FF5722' }} />;
      case 'rejected': return <ErrorIcon sx={{ color: '#F44336' }} />;
      default: return <SearchIcon sx={{ color: '#9E9E9E' }} />;
    }
  };

  const overallStatus = getOverallStatus();
  const statusColor = getStatusColor(overallStatus);

  if (compact) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Chip
          label={`${(confidence * 100).toFixed(1)}%`}
          size="small"
          sx={{
            backgroundColor: `${confidenceColor}20`,
            color: confidenceColor,
            fontWeight: 'bold'
          }}
        />
        <Typography variant="body2" sx={{ color: confidenceColor }}>
          {validationIcon} {match_type.toUpperCase()}
        </Typography>
        {(warnings.length > 0 || rejection_reasons.length > 0) && (
          <Tooltip title={`${warnings.length} warnings, ${rejection_reasons.length} rejections`}>
            <WarningIcon sx={{ color: '#FF9800', fontSize: 16 }} />
          </Tooltip>
        )}
      </Box>
    );
  }

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {getStatusIcon(overallStatus)}
            <Typography variant="h6" sx={{ color: statusColor }}>
              Ultra-Strict Match Validation
            </Typography>
            <Chip
              label={`${(confidence * 100).toFixed(1)}%`}
              sx={{
                backgroundColor: `${confidenceColor}20`,
                color: confidenceColor,
                fontWeight: 'bold'
              }}
            />
          </Box>
          <IconButton onClick={handleExpandClick}>
            <ExpandMoreIcon
              sx={{
                transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.3s'
              }}
            />
          </IconButton>
        </Box>

        {/* Confidence Progress */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Match Confidence
            </Typography>
            <Typography variant="body2" sx={{ color: confidenceColor }}>
              {ultraStrictMatchingApi.getConfidenceDescription(confidence, match_type)}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={confidence * 100}
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: '#f5f5f5',
              '& .MuiLinearProgress-bar': {
                backgroundColor: confidenceColor,
                borderRadius: 4,
              }
            }}
          />
        </Box>

        {/* Quick Status Indicators */}
        <Grid container spacing={1} sx={{ mb: 2 }}>
          <Grid item xs={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Model Match
              </Typography>
              <Typography variant="body2" sx={{ color: ultra_strict_details.model_exact_match ? '#4CAF50' : '#FF5722' }}>
                {ultra_strict_details.model_exact_match ? '✅ Exact' : '❌ Different'}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Brand Match
              </Typography>
              <Typography variant="body2" sx={{ color: ultra_strict_details.brand_exact_match ? '#4CAF50' : '#FF5722' }}>
                {ultra_strict_details.brand_exact_match ? '✅ Exact' : '❌ Different'}
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Spec Validation
              </Typography>
              <Typography variant="body2" sx={{ color: ultra_strict_details.specification_validation ? '#4CAF50' : '#FF5722' }}>
                {ultra_strict_details.specification_validation ? '✅ Passed' : '❌ Failed'}
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Warnings and Rejections */}
        {(warnings.length > 0 || rejection_reasons.length > 0) && (
          <Box sx={{ mb: 2 }}>
            {warnings.length > 0 && (
              <Alert severity="warning" sx={{ mb: 1 }}>
                <Typography variant="body2">
                  <strong>Warnings:</strong> {warnings.join(', ')}
                </Typography>
              </Alert>
            )}
            {rejection_reasons.length > 0 && (
              <Alert severity="error">
                <Typography variant="body2">
                  <strong>Rejection Reasons:</strong> {ultraStrictMatchingApi.formatRejectionReasons(rejection_reasons)}
                </Typography>
              </Alert>
            )}
          </Box>
        )}

        {/* Expandable Details */}
        <Collapse in={expanded}>
          <Divider sx={{ mb: 2 }} />
          
          {/* Detailed Validation Results */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <SpeedIcon fontSize="small" />
              Detailed Validation Results
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      {ultra_strict_details.model_exact_match ? <CheckCircleIcon color="success" /> : <ErrorIcon color="error" />}
                    </ListItemIcon>
                    <ListItemText 
                      primary="Model Exact Match"
                      secondary={`Similarity: ${(ultra_strict_details.model_similarity * 100).toFixed(1)}%`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      {ultra_strict_details.brand_exact_match ? <CheckCircleIcon color="success" /> : <ErrorIcon color="error" />}
                    </ListItemIcon>
                    <ListItemText 
                      primary="Brand Exact Match"
                      secondary={`Similarity: ${(ultra_strict_details.brand_similarity * 100).toFixed(1)}%`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      {ultra_strict_details.specification_validation ? <CheckCircleIcon color="success" /> : <ErrorIcon color="error" />}
                    </ListItemIcon>
                    <ListItemText 
                      primary="Specification Validation"
                      secondary={`Score: ${(ultra_strict_details.validation_score * 100).toFixed(1)}%`}
                    />
                  </ListItem>
                </List>
              </Grid>
              <Grid item xs={12} md={6}>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      {ultra_strict_details.early_rejection ? <ErrorIcon color="error" /> : <CheckCircleIcon color="success" />}
                    </ListItemIcon>
                    <ListItemText 
                      primary="Early Rejection Check"
                      secondary={ultra_strict_details.early_rejection ? 'Rejected early' : 'Passed initial validation'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <InfoIcon color="info" />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Match Quality Score"
                      secondary={`${matchQuality.toFixed(1)}/100`}
                    />
                  </ListItem>
                  {ultra_strict_details.rejection_reason && (
                    <ListItem>
                      <ListItemIcon>
                        <ErrorIcon color="error" />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Primary Rejection Reason"
                        secondary={ultra_strict_details.rejection_reason}
                      />
                    </ListItem>
                  )}
                </List>
              </Grid>
            </Grid>
          </Box>

          {/* Score Breakdown */}
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <InfoIcon fontSize="small" />
                Score Breakdown
              </Typography>
              <IconButton size="small" onClick={() => setShowScoreBreakdown(!showScoreBreakdown)}>
                <ExpandMoreIcon
                  sx={{
                    transform: showScoreBreakdown ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.3s'
                  }}
                />
              </IconButton>
            </Box>
            <Collapse in={showScoreBreakdown}>
              <Grid container spacing={2}>
                {Object.entries(result.score_breakdown).map(([key, value]) => (
                  <Grid item xs={6} md={4} key={key}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        {key.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : value}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={typeof value === 'number' ? value * 100 : 0}
                        sx={{
                          height: 4,
                          borderRadius: 2,
                          mt: 0.5,
                          backgroundColor: '#f5f5f5',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: value > 0.8 ? '#4CAF50' : value > 0.5 ? '#FF9800' : '#FF5722',
                            borderRadius: 2,
                          }
                        }}
                      />
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Collapse>
          </Box>

          {/* Matched Fields */}
          {result.matched_fields.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Matched Fields
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {result.matched_fields.map((field, index) => (
                  <Chip
                    key={index}
                    label={field}
                    size="small"
                    color="success"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Price Comparison */}
          {result.price_comparison && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Price Comparison
              </Typography>
              <Alert severity={result.price_comparison.is_better_deal ? 'success' : 'info'}>
                <Typography variant="body2">
                  <strong>Price Difference:</strong> ฿{result.price_comparison.price_difference.toLocaleString()} 
                  ({result.price_comparison.is_better_deal ? 'Better Deal' : 'Higher Price'})
                </Typography>
                <Typography variant="body2">
                  <strong>Potential Savings:</strong> ฿{result.price_comparison.savings.toLocaleString()}
                </Typography>
              </Alert>
            </Box>
          )}
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default UltraStrictMatchValidationIndicator;