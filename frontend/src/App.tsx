// frontend/src/App.tsx
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
import LandingPage from './pages/LandingPage';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import ResetPassword from './components/Auth/ResetPassword';
import Dashboard from './components/Dashboard/Dashboard';
import FactCheckPage from './pages/FactCheckPage';
import DirectFactCheckPage from './pages/DirectFactCheckPage';
import LoadingSpinner from './components/common/LoadingSpinner';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2563eb',
    },
    secondary: {
      main: '#64748b',
    },
  },
});

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loading, validateToken } = useAuth();
  const [validating, setValidating] = React.useState(false);
  const [tokenValid, setTokenValid] = React.useState<boolean | null>(null);

  useEffect(() => {
    const checkTokenValidity = async () => {
      // Only validate if authenticated and not loading
      if (isAuthenticated && !loading && tokenValid === null) {
        setValidating(true);
        try {
          const isValid = await validateToken();
          setTokenValid(isValid);
          if (!isValid) {
            console.log('Token invalid, redirecting to login');
          }
        } catch (error) {
          console.error('Token validation error:', error);
          setTokenValid(false);
        } finally {
          setValidating(false);
        }
      }
    };

    checkTokenValidity();
  }, [isAuthenticated, loading, validateToken, tokenValid]);

  if (loading || validating) return <LoadingSpinner />;
  
  // Redirect if token validation failed
  if (tokenValid === false) {
    return <Navigate to="/login" />;
  }
  
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

interface PublicRouteProps {
  children: React.ReactNode;
}

const PublicRoute: React.FC<PublicRouteProps> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) return <LoadingSpinner />;
  return !isAuthenticated ? <>{children}</> : <Navigate to="/dashboard" />;
};

// ✅ MFA Route - handles MFA verification
const MFARoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const [mfaPending, setMfaPending] = React.useState(false);
  const [mfaEmail, setMfaEmail] = React.useState('');
  
  React.useEffect(() => {
    // Check localStorage for MFA state
    const pending = localStorage.getItem('mfa_pending') === 'true';
    const email = localStorage.getItem('mfa_email') || '';
    setMfaPending(pending);
    setMfaEmail(email);
  }, []);

  if (loading) return <LoadingSpinner />;
  
  // Allow MFA route only if:
  // 1. Not already authenticated
  // 2. MFA is pending
  // 3. We have an email for MFA
  if (!isAuthenticated && mfaPending && mfaEmail) {
    return <>{children}</>;
  }
  
  // Otherwise redirect to login
  return <Navigate to="/login" />;
};

const LandingRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) return <LoadingSpinner />;
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <>{children}</>;
};

const AuthAwareRoute: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
  
  // ✅ FIXED: Moved useEffect BEFORE any conditional returns
  React.useEffect(() => {
    // This will run once on mount
    // You can add any side effects here if needed
  }, []);
  
  if (loading) return <LoadingSpinner />;
  
  return <Navigate to={isAuthenticated ? "/dashboard" : "/"} replace />;
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/" element={
              <LandingRoute>
                <LandingPage />
              </LandingRoute>
            } />
            
            {/* Public Routes */}
            <Route path="/login" element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } />
            
            <Route path="/register" element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            } />
            
            {/* ✅ MFA Verification Route */}
            <Route path="/verify-mfa" element={
              <MFARoute>
                <Login /> {/* Login component handles MFA internally */}
              </MFARoute>
            } />
            
            <Route path="/reset-password/:token" element={
              <PublicRoute>
                <ResetPassword />
              </PublicRoute>
            } />
            
            {/* Protected Routes */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            } />
            
            <Route path="/fact-check/:pageId" element={
              <ProtectedRoute>
                <Layout>
                  <FactCheckPage />
                </Layout>
              </ProtectedRoute>
            } />
            
            <Route path="/fact-check-direct" element={
              <ProtectedRoute>
                <Layout>
                  <DirectFactCheckPage />
                </Layout>
              </ProtectedRoute>
            } />
            
            <Route path="*" element={<AuthAwareRoute />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;