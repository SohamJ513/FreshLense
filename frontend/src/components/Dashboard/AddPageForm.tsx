// frontend/src/components/Dashboard/AddPageForm.tsx
import React, { useState } from 'react';
import {
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  MenuItem,
  InputAdornment,
  Fade,
  alpha,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  Add as AddIcon,
  Link as LinkIcon,
  Schedule as ScheduleIcon,
  DriveFileRenameOutline as RenameIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { pagesAPI, TrackedPage } from '../../services/api';

interface AddPageFormProps {
  onPageAdded: (page: TrackedPage) => void;
  onCancel?: () => void;
}

const AddPageForm: React.FC<AddPageFormProps> = ({ onPageAdded, onCancel }) => {
  const [url, setUrl] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [checkInterval, setCheckInterval] = useState(1440);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [touched, setTouched] = useState({
    url: false,
    displayName: false,
  });
  const [isExpanded, setIsExpanded] = useState(true);

  const intervalOptions = [
    { value: 60, label: '1 hour', icon: '⚡', description: 'Frequent checks for critical pages' },
    { value: 180, label: '3 hours', icon: '🕐', description: 'Regular monitoring' },
    { value: 360, label: '6 hours', icon: '🕒', description: 'Balanced approach' },
    { value: 720, label: '12 hours', icon: '🕛', description: 'Twice daily' },
    { value: 1440, label: '24 hours', icon: '📅', description: 'Daily checks (recommended)' },
    { value: 4320, label: '3 days', icon: '📆', description: 'Weekly-ish' },
    { value: 10080, label: '1 week', icon: '🗓️', description: 'Weekly monitoring' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const pageData = {
        url: url.trim(),
        display_name: displayName.trim() || undefined,
        check_interval_minutes: checkInterval,
      };

      const response = await pagesAPI.create(pageData);
      onPageAdded(response.data);
      
      setSuccess('Page added successfully!');
      setTimeout(() => {
        setUrl('');
        setDisplayName('');
        setCheckInterval(1440);
        setTouched({ url: false, displayName: false });
        setSuccess('');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add page');
    } finally {
      setLoading(false);
    }
  };

  const isUrlValid = (url: string) => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const getUrlError = () => {
    if (!touched.url) return '';
    if (!url) return 'URL is required';
    if (!isUrlValid(url)) return 'Please enter a valid URL (e.g., https://example.com)';
    return '';
  };

  const urlError = getUrlError();
  const isFormValid = url && isUrlValid(url) && !loading;

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <Box>
        {error && (
          <Fade in>
            <Alert 
              severity="error" 
              sx={{ mb: 3, borderRadius: 2 }}
              onClose={() => setError('')}
              icon={<WarningIcon />}
            >
              {error}
            </Alert>
          </Fade>
        )}

        {success && (
          <Fade in>
            <Alert 
              severity="success" 
              sx={{ mb: 3, borderRadius: 2 }}
              icon={<CheckCircleIcon />}
            >
              {success}
            </Alert>
          </Fade>
        )}

        {/* Header with Minimize/Expand Button */}
        <Box 
          sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 2,
            cursor: 'pointer',
            '&:hover': {
              backgroundColor: alpha('#1976d2', 0.02),
            },
            borderRadius: 1,
            p: 1,
            mx: -1,
          }}
          onClick={toggleExpand}
        >
          <Typography variant="subtitle1" fontWeight="bold" color="#1976d2">
            Page Details
          </Typography>
          <IconButton size="small" onClick={toggleExpand}>
            {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        <Collapse in={isExpanded} timeout="auto">
          <Box component="form" onSubmit={handleSubmit}>
            {/* URL Field */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                <LinkIcon sx={{ fontSize: 18, color: '#1976d2' }} />
                Page URL *
              </Typography>
              <TextField
                fullWidth
                placeholder="https://example.com/blog/technical-article"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onBlur={() => setTouched({ ...touched, url: true })}
                error={touched.url && !!urlError}
                helperText={touched.url && urlError}
                disabled={loading}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#1976d2',
                      },
                    },
                    '&.Mui-focused': {
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#1976d2',
                        borderWidth: 2,
                      },
                    },
                  },
                }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LinkIcon sx={{ color: '#9e9e9e', fontSize: 20 }} />
                    </InputAdornment>
                  ),
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                Enter the full URL of the page you want to monitor
              </Typography>
            </Box>

            {/* Display Name Field */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                <RenameIcon sx={{ fontSize: 18, color: '#1976d2' }} />
                Display Name (Optional)
              </Typography>
              <TextField
                fullWidth
                placeholder="e.g., My Technical Blog, Documentation Page"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                onBlur={() => setTouched({ ...touched, displayName: true })}
                disabled={loading}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#1976d2',
                      },
                    },
                    '&.Mui-focused': {
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#1976d2',
                        borderWidth: 2,
                      },
                    },
                  },
                }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <RenameIcon sx={{ color: '#9e9e9e', fontSize: 20 }} />
                    </InputAdornment>
                  ),
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                Give your page a friendly name for easy identification
              </Typography>
            </Box>

            {/* Check Interval Field */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                <ScheduleIcon sx={{ fontSize: 18, color: '#1976d2' }} />
                Check Interval *
              </Typography>
              <TextField
                fullWidth
                select
                value={checkInterval}
                onChange={(e) => setCheckInterval(Number(e.target.value))}
                disabled={loading}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#1976d2',
                      },
                    },
                    '&.Mui-focused': {
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: '#1976d2',
                        borderWidth: 2,
                      },
                    },
                  },
                }}
              >
                {intervalOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1">{option.icon}</Typography>
                        <Typography variant="body1" fontWeight={checkInterval === option.value ? 600 : 400}>
                          {option.label}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                        {option.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </TextField>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                How often should we check this page for changes?
              </Typography>
            </Box>

            {/* Selected Interval Preview */}
            <AnimatePresence>
              {checkInterval && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <Box 
                    sx={{ 
                      mb: 3, 
                      p: 2, 
                      bgcolor: alpha('#1976d2', 0.05), 
                      borderRadius: 2,
                      border: '1px solid',
                      borderColor: alpha('#1976d2', 0.1),
                    }}
                  >
                    <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <ScheduleIcon sx={{ fontSize: 14, color: '#1976d2' }} />
                      Selected interval: <strong>{intervalOptions.find(opt => opt.value === checkInterval)?.label}</strong>
                    </Typography>
                  </Box>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Form Actions */}
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              {onCancel && (
                <Button
                  onClick={onCancel}
                  disabled={loading}
                  variant="outlined"
                  sx={{
                    borderRadius: 2,
                    px: 3,
                    borderColor: '#e0e0e0',
                    color: '#757575',
                    '&:hover': {
                      borderColor: '#1976d2',
                      backgroundColor: alpha('#1976d2', 0.02),
                    },
                  }}
                >
                  Cancel
                </Button>
              )}
              <motion.div
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Button
                  type="submit"
                  variant="contained"
                  disabled={!isFormValid}
                  startIcon={loading ? <ScheduleIcon sx={{ animation: 'spin 1s linear infinite' }} /> : <AddIcon />}
                  sx={{
                    background: '#1976d2',
                    borderRadius: 2,
                    px: 4,
                    py: 1,
                    minWidth: 140,
                    '&:hover': {
                      background: '#1565c0',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 10px 20px rgba(25, 118, 210, 0.3)',
                    },
                    '&:disabled': {
                      background: '#bdbdbd',
                      transform: 'none',
                    },
                    transition: 'all 0.3s ease',
                  }}
                >
                  {loading ? 'Adding Page...' : 'Add Page'}
                </Button>
              </motion.div>
            </Box>
          </Box>
        </Collapse>

        {/* Helpful Tips */}
        <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid', borderColor: '#e0e0e0' }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
            <span>💡 <strong>Pro tip:</strong> Use a descriptive display name to easily identify pages</span>
            <span>⚡ <strong>Note:</strong> Shorter intervals = faster detection but more resources</span>
          </Typography>
        </Box>
      </Box>

      {/* Add spinning animation */}
      <style>
        {`
          @keyframes spin {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(360deg);
            }
          }
        `}
      </style>
    </motion.div>
  );
};

export default AddPageForm;