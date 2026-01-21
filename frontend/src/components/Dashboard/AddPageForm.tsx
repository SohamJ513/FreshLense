// frontend/src/components/Dashboard/AddPageForm.tsx
import React, { useState } from 'react';
import {
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  MenuItem,
} from '@mui/material';
import { pagesAPI, TrackedPage } from '../../services/api';

interface AddPageFormProps {
  onPageAdded: (page: TrackedPage) => void;
}

const AddPageForm: React.FC<AddPageFormProps> = ({ onPageAdded }) => {
  const [url, setUrl] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [checkInterval, setCheckInterval] = useState(1440); // Default 24 hours
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const intervalOptions = [
    { value: 60, label: '1 hour' },
    { value: 180, label: '3 hours' },
    { value: 360, label: '6 hours' },
    { value: 720, label: '12 hours' },
    { value: 1440, label: '24 hours' },
    { value: 4320, label: '3 days' },
    { value: 10080, label: '1 week' },
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
      setUrl('');
      setDisplayName('');
      setCheckInterval(1440);
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

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Add New Page to Monitor
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField
          required
          fullWidth
          label="Page URL"
          placeholder="https://example.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          error={url.length > 0 && !isUrlValid(url)}
          helperText={url.length > 0 && !isUrlValid(url) ? 'Please enter a valid URL' : ''}
        />

        <Box sx={{ display: 'flex', gap: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
          <TextField
            fullWidth
            label="Display Name (Optional)"
            placeholder="My Example Page"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />

          <TextField
            required
            fullWidth
            select
            label="Check Interval"
            value={checkInterval}
            onChange={(e) => setCheckInterval(Number(e.target.value))}
          >
            {intervalOptions.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>
        </Box>

        <Button
          type="submit"
          variant="contained"
          disabled={loading || !isUrlValid(url)}
          sx={{ minWidth: 120, alignSelf: 'flex-start' }}
        >
          {loading ? 'Adding...' : 'Add Page'}
        </Button>
      </Box>
    </Paper>
  );
};

export default AddPageForm;