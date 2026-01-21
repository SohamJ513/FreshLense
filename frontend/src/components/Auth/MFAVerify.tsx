// frontend/src/components/Auth/MFAVerify.tsx
import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, 
  Typography, 
  TextField, 
  Button, 
  Alert, 
  CircularProgress, 
  Paper,
  Container
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { useAuth } from '../../contexts/AuthContext';
import { resendMFACode } from '../../services/mfaApi';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api'; // ✅ Add axios import

interface MFAVerifyProps {
  email: string;
  onBackToLogin?: () => void;
}

const CodeInput = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    textAlign: 'center',
    letterSpacing: '8px',
    width: '220px',
    '& input': {
      textAlign: 'center',
    },
  },
}));

const TimerText = styled(Typography)(({ theme }) => ({
  fontFamily: 'monospace',
  fontSize: '1.2rem',
  fontWeight: 'bold',
}));

const ResendButton = styled(Button)(({ theme }) => ({
  marginTop: theme.spacing(2),
}));

const MFAVerify: React.FC<MFAVerifyProps> = ({ email, onBackToLogin }) => {
  const [code, setCode] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [resendLoading, setResendLoading] = useState<boolean>(false);
  const [timeLeft, setTimeLeft] = useState<number>(600); // 10 minutes in seconds
  const [canResend, setCanResend] = useState<boolean>(false);
  const [resendMessage, setResendMessage] = useState<string>('');
  
  const { loginWithMFA } = useAuth();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  // Timer countdown
  useEffect(() => {
    if (timeLeft <= 0) {
      setCanResend(true);
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          setCanResend(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft]);

  // Auto-focus on input
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // Auto-submit when code is 6 digits
  useEffect(() => {
    if (code.length === 6 && !loading) {
      handleSubmit();
    }
  }, [code]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/[^0-9]/g, '');
    if (value.length <= 6) {
      setCode(value);
      setError('');
    }
  };

  // ✅ Helper function to test API with current token
  const testTokenWithAPI = async (): Promise<boolean> => {
    try {
      console.log('🧪 [MFA Component] Testing token with API...');
      
      // Check what's in localStorage
      const token = localStorage.getItem('token');
      console.log('🔍 [MFA Component] Token from localStorage:', token ? `Present (${token.length} chars)` : 'Missing');
      
      if (!token) {
        console.error('❌ [MFA Component] No token found in localStorage');
        return false;
      }

      // Try a simple protected endpoint
      // Try /auth/me or /pages (whichever exists)
      console.log('📡 [MFA Component] Making test API call...');
      
      // First try /auth/me
      try {
        const response = await api.get('/auth/me', {
          validateStatus: (status) => status < 500 // Don't throw on 401/403
        });
        
        console.log('✅ [MFA Component] Test API call to /auth/me:', response.status);
        
        if (response.status === 200) {
          console.log('🎯 [MFA Component] Token verified successfully!');
          return true;
        } else if (response.status === 401) {
          console.error('❌ [MFA Component] Token invalid (401 Unauthorized)');
          return false;
        }
      } catch (authError: any) {
        console.log('⚠️ [MFA Component] /auth/me endpoint not available, trying /pages...');
      }

      // If /auth/me doesn't exist or failed, try /pages
      try {
        const response = await api.get('/pages', {
          validateStatus: (status) => status < 500
        });
        
        console.log('✅ [MFA Component] Test API call to /pages:', response.status);
        
        if (response.status === 200) {
          console.log('🎯 [MFA Component] Token verified successfully!');
          return true;
        } else if (response.status === 401) {
          console.error('❌ [MFA Component] Token invalid (401 Unauthorized)');
          return false;
        } else {
          console.log(`⚠️ [MFA Component] Got status ${response.status} - might be OK`);
          return true; // Even if not 200, might be OK (e.g., 404, 403)
        }
      } catch (pagesError: any) {
        console.error('❌ [MFA Component] Both test endpoints failed:', pagesError.message);
        return false;
      }
      
      return false;
    } catch (error: any) {
      console.error('❌ [MFA Component] Token test failed:', error.message);
      return false;
    }
  };

  const handleSubmit = async () => {
    if (code.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    if (timeLeft <= 0) {
      setError('Code has expired. Please request a new one.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      console.log('🔐 [MFA Component] Starting verification...');
      console.log('📧 Email:', email);
      console.log('🔢 Code:', code);
      
      const result = await loginWithMFA(email, code);
      
      console.log('🔐 [MFA Component] Verification result:', result);
      
      if (result.success) {
        console.log('✅ [MFA Component] SUCCESS!');
        
        // ✅ DEBUG: Check localStorage before redirect
        const token = localStorage.getItem('token');
        const user = localStorage.getItem('user');
        console.log('🔍 [MFA Component] Before redirect - Token:', token ? `Present (${token.length} chars)` : 'Missing');
        console.log('🔍 [MFA Component] Before redirect - User:', user ? 'Present' : 'Missing');
        
        // ✅ NEW: Test the token with API before redirect
        console.log('🧪 [MFA Component] Testing token with API before redirect...');
        const tokenIsValid = await testTokenWithAPI();
        
        if (!tokenIsValid) {
          console.error('❌ [MFA Component] Token test FAILED! Not redirecting.');
          setError('Authentication failed. Token is not valid. Please try again.');
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setCode('');
          setLoading(false);
          return;
        }
        
        console.log('✅ [MFA Component] Token verified with API! Proceeding to redirect...');
        
        // ✅ Wait 1 second to see logs (reduced from 3)
        console.log('⏳ [MFA Component] Waiting 1 second before redirect...');
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        console.log('🚀 [MFA Component] Now redirecting to dashboard...');
        navigate('/dashboard');
      } else {
        console.error('❌ [MFA Component] Verification failed:', result.error);
        throw new Error(result.error?.message || 'Invalid verification code. Please try again.');
      }
    } catch (err: any) {
      console.error('❌ [MFA Component] Error:', err);
      setError(err.message || 'Invalid verification code. Please try again.');
      setCode(''); // Clear code on error
      if (inputRef.current) {
        inputRef.current.focus();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (!canResend && timeLeft > 0) {
      setError(`Please wait ${formatTime(timeLeft)} before requesting a new code`);
      return;
    }

    setResendLoading(true);
    setResendMessage('');
    setError('');

    try {
      console.log('📨 [MFA Component] Resending code to:', email);
      await resendMFACode(email);
      
      console.log('✅ [MFA Component] Resend successful');
      setResendMessage('A new verification code has been sent to your email.');
      
      // Reset timer
      setTimeLeft(600); // 10 minutes
      setCanResend(false);
      setCode('');
      
      if (inputRef.current) {
        inputRef.current.focus();
      }
      
      // Clear success message after 5 seconds
      setTimeout(() => {
        setResendMessage('');
      }, 5000);
    } catch (err: any) {
      console.error('❌ [MFA Component] Resend error:', err);
      setError(err.message || 'Failed to send new code. Please try again.');
    } finally {
      setResendLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && code.length === 6 && !loading) {
      handleSubmit();
    }
  };

  const handleBack = () => {
    console.log('🔙 [MFA Component] Going back to login');
    if (onBackToLogin) {
      onBackToLogin();
    } else {
      navigate('/login');
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          py: 4,
        }}
      >
        <Paper elevation={3} sx={{ p: 4, width: '100%', maxWidth: 450, mx: 'auto' }}>
          <Box sx={{ textAlign: 'center' }}>
            {/* Header */}
            <Typography variant="h5" component="h1" gutterBottom fontWeight="bold">
              🔐 Verify Your Identity
            </Typography>
            
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              We've sent a 6-digit verification code to:
              <br />
              <strong>{email}</strong>
            </Typography>

            {/* Timer */}
            <Box sx={{ mb: 3 }}>
              <TimerText color={timeLeft < 60 ? 'error' : timeLeft < 300 ? 'warning.main' : 'primary'}>
                ⏳ Code expires in: {formatTime(timeLeft)}
              </TimerText>
              {timeLeft < 60 && (
                <Typography variant="caption" color="error">
                  Code expiring soon!
                </Typography>
              )}
            </Box>

            {/* Error/Success Messages */}
            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
                {error}
              </Alert>
            )}
            
            {resendMessage && (
              <Alert severity="success" sx={{ mb: 2 }} onClose={() => setResendMessage('')}>
                {resendMessage}
              </Alert>
            )}

            {/* Code Input */}
            <Box sx={{ mb: 3 }}>
              <CodeInput
                inputRef={inputRef}
                type="text"
                value={code}
                onChange={handleCodeChange}
                onKeyDown={handleKeyDown}
                placeholder="000000"
                disabled={loading || timeLeft <= 0}
                inputProps={{
                  inputMode: 'numeric',
                  pattern: '[0-9]*',
                  maxLength: 6,
                }}
                error={!!error}
                helperText={error ? '' : "Enter the 6-digit code from your email"}
              />
            </Box>

            {/* Verify Button */}
            <Button
              variant="contained"
              color="primary"
              fullWidth
              size="large"
              onClick={handleSubmit}
              disabled={code.length !== 6 || loading || timeLeft <= 0}
              sx={{ mb: 2 }}
            >
              {loading ? (
                <>
                  <CircularProgress size={24} sx={{ mr: 1 }} />
                  Verifying...
                </>
              ) : (
                'Verify & Continue'
              )}
            </Button>

            {/* Resend Code Button */}
            <ResendButton
              variant="outlined"
              color="secondary"
              onClick={handleResendCode}
              disabled={(!canResend && timeLeft > 0) || resendLoading}
              fullWidth
            >
              {resendLoading ? (
                <CircularProgress size={20} />
              ) : (
                `Resend Code ${!canResend ? `(${formatTime(timeLeft)})` : ''}`
              )}
            </ResendButton>

            {/* Back to Login */}
            <Button
              variant="text"
              color="inherit"
              onClick={handleBack}
              sx={{ mt: 2 }}
              fullWidth
            >
              ← Back to Login
            </Button>

            {/* Help Text */}
            <Typography variant="caption" color="text.secondary" sx={{ mt: 3, display: 'block' }}>
              Can't find the email? Check your spam folder or ensure {email} is correct.
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default MFAVerify;

