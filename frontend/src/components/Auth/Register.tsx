// frontend/src/components/Auth/Register.tsx
import React, { useState } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  Link,
  useTheme,
  alpha,
  Divider,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { PersonAdd } from '@mui/icons-material';

const Register: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { register } = useAuth();
  const theme = useTheme();

  // Helper function to extract error message from API response
  const getErrorMessage = (error: any): string => {
    if (typeof error === 'string') return error;
    if (error.response?.data?.detail) {
      if (Array.isArray(error.response.data.detail)) {
        // Handle Pydantic validation errors (array of errors)
        return error.response.data.detail
          .map((err: any) => err.msg || JSON.stringify(err))
          .join(', ');
      } else if (typeof error.response.data.detail === 'object') {
        // Handle single object error
        return JSON.stringify(error.response.data.detail);
      } else {
        // Handle string error
        return error.response.data.detail;
      }
    }
    if (error.message) return error.message;
    return 'Registration failed. Please try again.';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Basic validation
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    const result = await register(email, password);
    
    if (!result.success) {
      setError(getErrorMessage(result.error));
    }
    
    setLoading(false);
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
          py: 4,
        }}
      >
        <Box sx={{ width: '100%', maxWidth: 450 }}>
          {/* Header Branding */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 60,
                height: 60,
                borderRadius: 3,
                background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                color: 'white',
                fontWeight: 'bold',
                fontSize: '1.5rem',
                mb: 2,
              }}
            >
              FL
            </Box>
            <Typography
              variant="h4"
              component="h1"
              fontWeight="800"
              gutterBottom
              sx={{
                background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                color: 'transparent',
              }}
            >
              FreshLense
            </Typography>
            <Typography variant="h6" color="text.secondary" fontWeight="500">
              Create your account
            </Typography>
          </Box>

          <Paper
            elevation={8}
            sx={{
              padding: 4,
              borderRadius: 4,
              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              background: 'white',
              position: 'relative',
              overflow: 'hidden',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 4,
                background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
              },
            }}
          >
            {error && (
              <Alert 
                severity="error" 
                sx={{ 
                  mb: 3,
                  borderRadius: 2,
                  border: `1px solid ${theme.palette.error.light}`,
                }}
              >
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="email"
                label="Email Address"
                name="email"
                autoComplete="email"
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                sx={{
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    '&:hover fieldset': {
                      borderColor: theme.palette.primary.main,
                    },
                  },
                }}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type="password"
                id="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                sx={{
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    '&:hover fieldset': {
                      borderColor: theme.palette.primary.main,
                    },
                  },
                }}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="confirmPassword"
                label="Confirm Password"
                type="password"
                id="confirmPassword"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    '&:hover fieldset': {
                      borderColor: theme.palette.primary.main,
                    },
                  },
                }}
              />
              
              {/* Password Requirements */}
              <Box 
                sx={{ 
                  mb: 3, 
                  p: 2, 
                  borderRadius: 2,
                  backgroundColor: alpha(theme.palette.info.main, 0.05),
                  border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`,
                }}
              >
                <Typography variant="caption" fontWeight="600" color="text.secondary" display="block" gutterBottom>
                  Password Requirements:
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block">
                  • At least 6 characters long
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block">
                  • Passwords must match
                </Typography>
              </Box>

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                startIcon={<PersonAdd />}
                disabled={loading}
                sx={{
                  py: 1.5,
                  borderRadius: 3,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                  boxShadow: `0 4px 15px ${alpha(theme.palette.primary.main, 0.3)}`,
                  '&:hover': {
                    transform: 'translateY(-1px)',
                    boxShadow: `0 6px 20px ${alpha(theme.palette.primary.main, 0.4)}`,
                  },
                  '&:disabled': {
                    background: theme.palette.action.disabled,
                    transform: 'none',
                    boxShadow: 'none',
                  },
                  transition: 'all 0.2s ease-in-out',
                }}
              >
                {loading ? 'Creating Account...' : 'Create Account'}
              </Button>
            </Box>

            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">
                Already have an account?
              </Typography>
            </Divider>

            <Box textAlign="center">
              <Link
                component={RouterLink}
                to="/login"
                variant="body1"
                sx={{
                  fontWeight: 600,
                  textDecoration: 'none',
                  color: theme.palette.primary.main,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 1,
                  padding: '8px 16px',
                  borderRadius: 2,
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                  '&:hover': {
                    background: alpha(theme.palette.primary.main, 0.04),
                    borderColor: theme.palette.primary.main,
                  },
                  transition: 'all 0.2s ease-in-out',
                }}
              >
                Sign in to your account
              </Link>
            </Box>
          </Paper>

          {/* Footer Links */}
          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Typography variant="body2" color="text.secondary">
              By creating an account, you agree to our Terms of Service
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              © 2024 FreshLense. All rights reserved.
            </Typography>
          </Box>
        </Box>
      </Box>
    </Container>
  );
};

export default Register;