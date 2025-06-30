import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Fade,
  Zoom,
} from '@mui/material';
import {
  Store as StoreIcon,
  Category as CategoryIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';
import RetailerSelector from './RetailerSelector';
import CategorySelector from './CategorySelector';
import { useQuery } from '@tanstack/react-query';
import { retailerApi } from '../../services/api';

const steps = [
  { label: 'Select Retailer', icon: <StoreIcon /> },
  { label: 'Choose Categories', icon: <CategoryIcon /> },
  { label: 'Configure Settings', icon: <SettingsIcon /> },
  { label: 'Review & Start', icon: <CheckCircleIcon /> },
];

interface Category {
  code: string;
  name: string;
  name_th: string;
  url: string;
  estimated_products?: number;
  actual_products?: number | null;
  last_scraped?: string | null;
}

interface Retailer {
  id: string;
  code: string;
  name: string;
  base_url: string;
  market_position: string;
  estimated_products: number;
  rate_limit_delay: number;
  max_concurrent: number;
  focus_categories: string[];
  price_volatility: string;
  is_active: boolean;
}

interface ScrapingWizardProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (jobData: any) => void;
  isSubmitting?: boolean;
}

export default function ScrapingWizard({
  open,
  onClose,
  onSubmit,
  isSubmitting = false,
}: ScrapingWizardProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedRetailer, setSelectedRetailer] = useState<string | null>(null);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [settings, setSettings] = useState({
    maxPages: 10,
    priority: 'normal',
    concurrent: false,
  });

  // Fetch retailers
  const { data: retailers = [], isLoading: loadingRetailers } = useQuery<Retailer[]>({
    queryKey: ['retailers'],
    queryFn: async () => {
      const response = await retailerApi.getAll();
      return response.data;
    },
  });

  // Fetch categories for selected retailer
  const { data: categories = [], isLoading: loadingCategories } = useQuery<Category[]>({
    queryKey: ['retailer-categories', selectedRetailer],
    queryFn: async () => {
      if (!selectedRetailer) return [];
      const response = await retailerApi.getCategories(selectedRetailer);
      return response.data;
    },
    enabled: !!selectedRetailer,
  });

  const handleNext = () => {
    if (activeStep === steps.length - 1) {
      // Submit the job
      const jobData = {
        retailer_code: selectedRetailer,
        category_codes: selectedCategories,
        max_pages: settings.maxPages,
        priority: settings.priority,
        concurrent: settings.concurrent,
      };
      onSubmit(jobData);
    } else {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const canProceed = () => {
    switch (activeStep) {
      case 0:
        return !!selectedRetailer;
      case 1:
        return selectedCategories.length > 0;
      case 2:
        return true;
      case 3:
        return true;
      default:
        return false;
    }
  };

  const getStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Fade in timeout={300}>
            <Box>
              {loadingRetailers ? (
                <Box display="flex" justifyContent="center" py={4}>
                  <CircularProgress />
                </Box>
              ) : (
                <RetailerSelector
                  retailers={retailers}
                  selectedRetailer={selectedRetailer}
                  onSelectRetailer={setSelectedRetailer}
                />
              )}
            </Box>
          </Fade>
        );

      case 1:
        return (
          <Fade in timeout={300}>
            <Box>
              {loadingCategories ? (
                <Box display="flex" justifyContent="center" py={4}>
                  <CircularProgress />
                </Box>
              ) : (
                <CategorySelector
                  categories={categories}
                  selectedCategories={selectedCategories}
                  onCategoryChange={setSelectedCategories}
                  retailerName={retailers.find(r => r.code === selectedRetailer)?.name || ''}
                />
              )}
            </Box>
          </Fade>
        );

      case 2:
        return (
          <Fade in timeout={300}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Configure Scraping Settings
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Fine-tune how the scraping job will run
              </Typography>

              <Box sx={{ mt: 3 }}>
                <Paper sx={{ p: 3, mb: 2 }}>
                  <Typography gutterBottom>
                    Maximum Pages per Category
                  </Typography>
                  <Slider
                    value={settings.maxPages}
                    onChange={(_, value) => setSettings({ ...settings, maxPages: value as number })}
                    min={1}
                    max={50}
                    marks={[
                      { value: 1, label: '1' },
                      { value: 10, label: '10' },
                      { value: 25, label: '25' },
                      { value: 50, label: '50' },
                    ]}
                    valueLabelDisplay="on"
                  />
                  <Typography variant="caption" color="text.secondary">
                    Controls how many pages to scrape from each category
                  </Typography>
                </Paper>

                <Paper sx={{ p: 3, mb: 2 }}>
                  <FormControl fullWidth>
                    <InputLabel>Priority Level</InputLabel>
                    <Select
                      value={settings.priority}
                      onChange={(e) => setSettings({ ...settings, priority: e.target.value })}
                      label="Priority Level"
                    >
                      <MenuItem value="low">Low - Run when idle</MenuItem>
                      <MenuItem value="normal">Normal - Standard queue</MenuItem>
                      <MenuItem value="high">High - Process first</MenuItem>
                    </Select>
                  </FormControl>
                </Paper>

                <Alert severity="info">
                  <Typography variant="body2">
                    Jobs will respect rate limits to avoid overwhelming the retailer's website.
                    Higher priority jobs will be processed first but not faster.
                  </Typography>
                </Alert>
              </Box>
            </Box>
          </Fade>
        );

      case 3:
        const retailer = retailers.find((r: Retailer) => r.code === selectedRetailer);
        const selectedCats = categories.filter((cat: Category) => selectedCategories.includes(cat.code));
        const totalProducts = selectedCats.reduce((sum: number, cat: Category) => sum + (cat.estimated_products || 0), 0);
        const estimatedHours = totalProducts / 500;

        return (
          <Zoom in timeout={300}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Review Your Scraping Job
              </Typography>
              
              <Paper sx={{ p: 3, mb: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                <Typography variant="h5" gutterBottom>
                  {retailer?.name}
                </Typography>
                <Typography variant="body1">
                  {selectedCategories.length} categories selected
                </Typography>
              </Paper>

              <Paper sx={{ p: 3, mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Selected Categories:
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {selectedCats.map((cat: Category) => (
                    <Chip key={cat.code} label={cat.name} variant="outlined" />
                  ))}
                </Box>
              </Paper>

              <Paper sx={{ p: 3, mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Job Configuration:
                </Typography>
                <Box>
                  <Typography variant="body2">
                    • Max pages per category: {settings.maxPages}
                  </Typography>
                  <Typography variant="body2">
                    • Priority: {settings.priority}
                  </Typography>
                  <Typography variant="body2">
                    • Estimated products: ~{totalProducts.toLocaleString()}
                  </Typography>
                  <Typography variant="body2">
                    • Estimated time: ~{estimatedHours < 1 
                      ? `${Math.round(estimatedHours * 60)} minutes`
                      : `${Math.round(estimatedHours)} hours`}
                  </Typography>
                </Box>
              </Paper>

              {isSubmitting && (
                <Alert severity="info" icon={<CircularProgress size={20} />}>
                  Creating scraping job...
                </Alert>
              )}
            </Box>
          </Zoom>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          minHeight: '80vh',
          maxHeight: '90vh',
        },
      }}
    >
      <DialogTitle>
        <Typography variant="h5">Create Scraping Job</Typography>
      </DialogTitle>
      
      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ pt: 3, pb: 5 }}>
          {steps.map((step, index) => (
            <Step key={step.label}>
              <StepLabel
                StepIconComponent={() => (
                  <Box
                    sx={{
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      bgcolor: activeStep >= index ? 'primary.main' : 'grey.300',
                      color: 'white',
                    }}
                  >
                    {step.icon}
                  </Box>
                )}
              >
                {step.label}
              </StepLabel>
            </Step>
          ))}
        </Stepper>

        <Box sx={{ mt: 2, mb: 1, minHeight: 400 }}>
          {getStepContent()}
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button onClick={onClose} disabled={isSubmitting}>
          Cancel
        </Button>
        <Box flex={1} />
        <Button
          onClick={handleBack}
          disabled={activeStep === 0 || isSubmitting}
          startIcon={<ArrowBackIcon />}
        >
          Back
        </Button>
        <Button
          onClick={handleNext}
          variant="contained"
          disabled={!canProceed() || isSubmitting}
          endIcon={activeStep === steps.length - 1 ? <PlayArrowIcon /> : <ArrowForwardIcon />}
        >
          {activeStep === steps.length - 1 ? 'Start Scraping' : 'Next'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}