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
  Container,
  Checkbox,
  FormControlLabel,
  Divider
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { useAuth } from '../../contexts/AuthContext';
import { resendMFACode, verifyMFA } from '../../services/mfaApi';
import { useNavigate } from 'react-router-dom';

interface MFAVerifyProps {
  email: string;
  onBackToLogin?: () => void;
}

interface MFAVerifyResponse {
  access_token: string;
  token_type: string;
  email: string;
  message: string;
  mfa_session_token?: string;
  expires_in?: number;
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
  const [timeLeft, setTimeLeft] = useState<number>(600);
  const [canResend, setCanResend] = useState<boolean>(false);
  const [resendMessage, setResendMessage] = useState<string>('');
  const [rememberForDay, setRememberForDay] = useState<boolean>(true);
  
  const { loginWithMFA } = useAuth();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

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

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

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
      console.log('💾 Remember for 24 hours:', rememberForDay);
      
      const response = await verifyMFA(email, code, rememberForDay) as MFAVerifyResponse;
      
      console.log('🔐 [MFA Component] Verification result:', response);
      
      if (response.access_token) {
        // Clear any existing MFA state first
        localStorage.removeItem('mfa_pending');
        localStorage.removeItem('mfa_email');
        
        // Store the token
        localStorage.setItem('token', response.access_token);
        localStorage.setItem('user', JSON.stringify({ email: response.email }));
        
        // Store MFA session token if "Remember Me" was checked and token exists
        if (rememberForDay && response.mfa_session_token) {
          localStorage.setItem('mfa_session_token', response.mfa_session_token);
          localStorage.setItem('mfa_verified_at', new Date().toISOString());
          console.log('✅ MFA session token stored (valid for 24 hours)');
        } else {
          localStorage.removeItem('mfa_session_token');
          localStorage.removeItem('mfa_verified_at');
        }
        
        console.log('✅ [MFA Component] SUCCESS! Token stored');
        
        // ✅ IMPORTANT: Clear any pending MFA state before redirect
        if (onBackToLogin) {
          // Don't call onBackToLogin - that would go back to login!
          console.log('⚠️ Not calling onBackToLogin - going directly to dashboard');
        }
        
        // ✅ Navigate directly to dashboard
        console.log('🚀 [MFA Component] Now redirecting to dashboard...');
        
        // Small delay to ensure state is saved
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Use navigate with replace to prevent going back to MFA page
        navigate('/dashboard', { replace: true });
        
      } else {
        console.error('❌ [MFA Component] Verification failed: No token received');
        throw new Error('Invalid verification code. Please try again.');
      }
    } catch (err: any) {
      console.error('❌ [MFA Component] Error:', err);
      setError(err.message || 'Invalid verification code. Please try again.');
      setCode('');
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
      
      setTimeLeft(600);
      setCanResend(false);
      setCode('');
      
      if (inputRef.current) {
        inputRef.current.focus();
      }
      
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
    // Clear MFA state when going back
    localStorage.removeItem('mfa_pending');
    localStorage.removeItem('mfa_email');
    localStorage.removeItem('temp_user_email');
    localStorage.removeItem('temp_user_password');
    
    if (onBackToLogin) {
      onBackToLogin();
    } else {
      navigate('/login', { replace: true });
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
            <Typography variant="h5" component="h1" gutterBottom fontWeight="bold">
              🔐 Verify Your Identity
            </Typography>
            
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              We've sent a 6-digit verification code to:
              <br />
              <strong>{email}</strong>
            </Typography>

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

            <FormControlLabel
              control={
                <Checkbox
                  checked={rememberForDay}
                  onChange={(e) => setRememberForDay(e.target.checked)}
                  color="primary"
                />
              }
              label={
                <Typography variant="body2">
                  Remember me for 24 hours (no MFA required on this device)
                </Typography>
              }
              sx={{ mb: 2, display: 'flex', justifyContent: 'center' }}
            />

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

            <Divider sx={{ my: 2 }} />

            <Button
              variant="text"
              color="inherit"
              onClick={handleBack}
              fullWidth
            >
              ← Back to Login
            </Button>

            <Typography variant="caption" color="text.secondary" sx={{ mt: 3, display: 'block' }}>
              Can't find the email? Check your spam folder or ensure {email} is correct.
            </Typography>

            {rememberForDay && (
              <Typography variant="caption" color="info.main" sx={{ mt: 2, display: 'block' }}>
                💡 You won't be asked for MFA again on this device for 24 hours
              </Typography>
            )}
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default MFAVerify;