// frontend/src/components/Auth/Login.tsx
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
import { Login as LoginIcon } from '@mui/icons-material';
import ForgotPassword from './ForgotPassword';
import MFAVerify from './MFAVerify';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  
  // MFA States
  const [requiresMFA, setRequiresMFA] = useState<boolean>(false);
  const [mfaEmail, setMfaEmail] = useState<string>('');
  
  const { login } = useAuth();
  const theme = useTheme();

  // Helper function to extract error message from API response
  const getErrorMessage = (error: any): string => {
    if (typeof error === 'string') return error;
    if (error.response?.data?.detail) {
      if (Array.isArray(error.response.data.detail)) {
        return error.response.data.detail
          .map((err: any) => err.msg || JSON.stringify(err))
          .join(', ');
      } else if (typeof error.response.data.detail === 'object') {
        return JSON.stringify(error.response.data.detail);
      } else {
        return error.response.data.detail;
      }
    }
    if (error.message) return error.message;
    return 'Login failed. Please try again.';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(email, password);
      
      if (!result.success) {
        // Check if MFA is required
        if (result.error?.requires_mfa) {
          setRequiresMFA(true);
          setMfaEmail(result.error.email || email);
          setError(''); // Clear any previous errors
        } else {
          setError(getErrorMessage(result.error));
        }
      }
      // If login was successful, AuthContext will handle redirect
    } catch (err: any) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleBackToLogin = () => {
    setRequiresMFA(false);
    setMfaEmail('');
    setError('');
  };

  // Show Forgot Password component if needed
  if (showForgotPassword) {
    return (
      <ForgotPassword 
        onBackToLogin={() => setShowForgotPassword(false)}
        onSuccess={() => setShowForgotPassword(false)}
      />
    );
  }

  // Show MFA verification if needed
  if (requiresMFA) {
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
            {/* Header Branding - Same as login */}
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
                Two-Factor Verification
              </Typography>
            </Box>

            {/* MFA Verification Component - Simplified */}
            <MFAVerify
              email={mfaEmail}
              onBackToLogin={handleBackToLogin}
            />
          </Box>
        </Box>
      </Container>
    );
  }

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
              Welcome back
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
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                sx={{
                  mb: 1,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    '&:hover fieldset': {
                      borderColor: theme.palette.primary.main,
                    },
                  },
                }}
              />

              {/* Forgot Password Link */}
              <Box sx={{ textAlign: 'right', mb: 2 }}>
                <Link 
                  component="button" 
                  type="button"
                  variant="body2" 
                  onClick={() => setShowForgotPassword(true)}
                  sx={{
                    color: theme.palette.primary.main,
                    textDecoration: 'none',
                    fontWeight: 500,
                    '&:hover': {
                      textDecoration: 'underline',
                    },
                  }}
                >
                  Forgot your password?
                </Link>
              </Box>

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                startIcon={<LoginIcon />}
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
                {loading ? 'Signing In...' : 'Sign In'}
              </Button>
            </Box>

            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">
                New to FreshLense?
              </Typography>
            </Divider>

            <Box textAlign="center">
              <Link
                component={RouterLink}
                to="/register"
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
                Create an account
              </Link>
            </Box>
          </Paper>

          {/* MFA Info Note */}
          <Alert 
            severity="info" 
            sx={{ 
              mt: 3,
              borderRadius: 2,
              border: `1px solid ${theme.palette.info.light}`,
              fontSize: '0.875rem',
            }}
          >
            <strong>Enhanced Security:</strong> Your account is protected with Multi-Factor Authentication (MFA). 
            After entering your password, you'll receive a verification code via email.
          </Alert>

          {/* Footer Links */}
          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Typography variant="body2" color="text.secondary">
              © 2024 FreshLense. All rights reserved.
            </Typography>
          </Box>
        </Box>
      </Box>
    </Container>
  );
};

export default Login;

