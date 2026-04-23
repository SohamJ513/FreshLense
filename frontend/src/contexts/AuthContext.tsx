// frontend/src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI, isMFARequiredError, getMFADataFromError, LoginResponse, tokenUtils, testAPIConnection } from '../services/api';
import { MFALoginResponse } from '../types/mfa';
import { verifyMFACode, checkMFASession, clearMFASession, isStoredMFASessionValid, getStoredMFASessionToken } from '../services/mfaApi';
import api from '../services/api';

interface User {
  email: string;
  id?: string;
  mfa_enabled?: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: any }>;
  loginWithMFA: (email: string, mfaCode: string, rememberForDay?: boolean) => Promise<{ success: boolean; error?: any }>;
  register: (email: string, password: string) => Promise<{ success: boolean; message?: string; redirectToLogin?: boolean; error?: any }>;
  logout: () => void;
  logoutWithConfirmation?: () => Promise<boolean>;
  loading: boolean;
  isAuthenticated: boolean;
  mfaEmail: string | null;
  clearMFAEmail: () => void;
  validateToken: () => Promise<boolean>;
  skipMFAForSession: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

// Type guard functions
const isMFAResponse = (data: any): data is MFALoginResponse => {
  return 'requires_mfa' in data && data.requires_mfa === true;
};

const isLoginResponse = (data: any): data is LoginResponse => {
  return 'access_token' in data && data.access_token;
};

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [mfaEmail, setMfaEmail] = useState<string | null>(null);
  const [skipMFAForSession, setSkipMFAForSession] = useState<boolean>(false);

  // Function to validate token with backend
  const validateTokenWithBackend = async (): Promise<boolean> => {
    const storedToken = localStorage.getItem('token');
    if (!storedToken) {
      console.log('🔍 [Auth] No token to validate');
      return false;
    }

    try {
      console.log('🔍 [Auth] Validating token with backend...');
      const response = await authAPI.validateToken(storedToken);
      return response.data.valid === true;
    } catch (error) {
      console.log('❌ [Auth] Token validation failed:', error);
      return false;
    }
  };

  // Function to check MFA session validity
  const checkMFASessionValidity = async (email: string): Promise<boolean> => {
    const mfaSessionToken = getStoredMFASessionToken();
    
    if (!mfaSessionToken || !isStoredMFASessionValid()) {
      console.log('🔐 [Auth] No valid MFA session found in storage');
      return false;
    }
    
    try {
      console.log('🔐 [Auth] Checking MFA session with backend...');
      const result = await checkMFASession(email, mfaSessionToken);
      
      if (!result.mfa_required && result.mfa_valid) {
        console.log('✅ [Auth] Valid MFA session found, skipping MFA');
        return true;
      } else {
        console.log('❌ [Auth] MFA session invalid, clearing');
        clearMFASession();
        return false;
      }
    } catch (error) {
      console.error('❌ [Auth] MFA session check failed:', error);
      clearMFASession();
      return false;
    }
  };

  // Function to sync auth state
  const syncAuthState = async () => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    const storedMFAEmail = localStorage.getItem('mfa_email');
    const storedMFAPending = localStorage.getItem('mfa_pending') === 'true';
    const storedSkipMFA = localStorage.getItem('skip_mfa_session') === 'true';
    
    console.log('🔍 [Auth] Syncing auth state:', {
      hasToken: !!storedToken,
      hasUser: !!storedUser,
      mfaEmail: storedMFAEmail,
      mfaPending: storedMFAPending,
      skipMFA: storedSkipMFA
    });

    if (storedToken) {
      const isValid = await validateTokenWithBackend();
      
      if (isValid) {
        console.log('✅ [Auth] Token is valid, setting up auth');
        setToken(storedToken);
        
        if (storedUser) {
          try {
            const parsedUser = JSON.parse(storedUser);
            setUser(parsedUser);
            
            if (storedSkipMFA && parsedUser.email) {
              const hasValidMFASession = await checkMFASessionValidity(parsedUser.email);
              setSkipMFAForSession(hasValidMFASession);
              if (hasValidMFASession) {
                console.log('✅ [Auth] User has valid MFA session, will skip MFA on next login');
              }
            }
          } catch (error) {
            console.error('Failed to parse stored user:', error);
          }
        }
        
        tokenUtils.setToken(storedToken);
        
        if (storedMFAPending || storedMFAEmail) {
          localStorage.removeItem('mfa_pending');
          localStorage.removeItem('mfa_email');
          setMfaEmail(null);
        }
      } else {
        console.log('❌ [Auth] Token invalid, clearing auth');
        clearAuthState();
      }
    } else {
      if (storedMFAEmail) {
        console.log('🔐 [Auth] Restoring MFA state for:', storedMFAEmail);
        setMfaEmail(storedMFAEmail);
      } else {
        clearAuthState();
      }
    }
    
    setLoading(false);
  };

  // Function to clear auth state
  const clearAuthState = () => {
    console.log('🗑️ [Auth] Clearing auth state');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('mfa_pending');
    localStorage.removeItem('mfa_email');
    localStorage.removeItem('temp_user_email');
    localStorage.removeItem('skip_mfa_session');
    
    setToken(null);
    setUser(null);
    setMfaEmail(null);
    setSkipMFAForSession(false);
    
    tokenUtils.clearAuthData();
    clearMFASession();
  };

  useEffect(() => {
    syncAuthState();
  }, []);

  // Function to store auth data consistently
  const storeAuthData = (accessToken: string, userEmail: string, mfaSessionToken?: string) => {
    console.log('💾 [Auth] Storing auth data for:', userEmail);
    
    const userData = { email: userEmail };
    
    localStorage.setItem('token', accessToken);
    localStorage.setItem('user', JSON.stringify(userData));
    
    if (mfaSessionToken) {
      localStorage.setItem('mfa_session_token', mfaSessionToken);
      localStorage.setItem('mfa_verified_at', new Date().toISOString());
      localStorage.setItem('skip_mfa_session', 'true');
      setSkipMFAForSession(true);
      console.log('✅ [Auth] MFA session token stored (valid for 24 hours)');
    }
    
    setToken(accessToken);
    setUser(userData);
    tokenUtils.setToken(accessToken);
    localStorage.removeItem('mfa_pending');
    localStorage.removeItem('mfa_email');
    setMfaEmail(null);
    
    console.log('✅ [Auth] Auth data stored and synchronized');
  };

  // Helper to extract error message
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
    return 'An error occurred';
  };

  // Login function
  const login = async (email: string, password: string) => {
    try {
      clearAuthState();
      
      console.log('🔐 [Auth] Login attempt for:', email);
      
      const hasValidMFASession = await checkMFASessionValidity(email);
      if (hasValidMFASession) {
        console.log('✅ [Auth] Valid MFA session found, attempting auto-login');
        
        const response = await authAPI.login({ email, password });
        const responseData = response.data;
        
        if (isLoginResponse(responseData)) {
          console.log('✅ [Auth] Auto-login successful via MFA session');
          storeAuthData(responseData.access_token, email, getStoredMFASessionToken() || undefined);
          return { success: true };
        }
      }
      
      const apiTest = await testAPIConnection();
      if (!apiTest.success) {
        throw new Error(`Backend is not reachable: ${apiTest.message}`);
      }
      
      const response = await authAPI.login({ email, password });
      const responseData = response.data;
      
      if (isMFAResponse(responseData)) {
        console.log('🔐 [Auth] MFA required detected - storing state');
        
        const mfaEmailToStore = responseData.email || email;
        localStorage.setItem('mfa_pending', 'true');
        localStorage.setItem('mfa_email', mfaEmailToStore);
        setMfaEmail(mfaEmailToStore);
        
        return { 
          success: false, 
          error: {
            requires_mfa: true,
            email: mfaEmailToStore,
            message: responseData.message || 'MFA verification required'
          }
        };
      }
      
      if (isLoginResponse(responseData)) {
        console.log('⚠️ [Auth] Unexpected token response (MFA should be required)');
        storeAuthData(responseData.access_token, email);
        return { success: true };
      }
      
      throw new Error('Invalid response from server');
      
    } catch (error: any) {
      console.error('❌ [Auth] Login error:', error);
      
      if (isMFARequiredError(error)) {
        console.log('🔐 [Auth] MFA error detected via helper');
        const mfaData = getMFADataFromError(error);
        if (mfaData) {
          const mfaEmailToStore = mfaData.email || email;
          localStorage.setItem('mfa_pending', 'true');
          localStorage.setItem('mfa_email', mfaEmailToStore);
          setMfaEmail(mfaEmailToStore);
          
          return { 
            success: false, 
            error: {
              requires_mfa: true,
              email: mfaEmailToStore,
              message: mfaData.message || 'MFA verification required'
            }
          };
        }
      }
      
      return { 
        success: false, 
        error: {
          message: getErrorMessage(error),
          requires_mfa: false
        }
      };
    }
  };

  // ✅ FIXED: Login with MFA - ensures proper navigation
  const loginWithMFA = async (email: string, mfaCode: string, rememberForDay: boolean = true) => {
    try {
      console.log('🚀 [Auth] MFA verification for:', email);
      console.log('💾 [Auth] Remember for 24 hours:', rememberForDay);
      
      const mfaResponse = await verifyMFACode(email, mfaCode, rememberForDay);
      
      console.log('✅ [Auth] MFA verification API response received');
      
      const accessToken = mfaResponse.access_token;
      const mfaSessionToken = (mfaResponse as any).mfa_session_token;
      
      if (!accessToken) {
        console.error('❌ [Auth] No access token in MFA response');
        throw new Error('No access token received from MFA verification');
      }
      
      console.log('🔑 [Auth] Token received, length:', accessToken.length);
      
      // Store auth data
      storeAuthData(accessToken, email, mfaSessionToken);
      
      // Clear all MFA state
      localStorage.removeItem('mfa_pending');
      localStorage.removeItem('mfa_email');
      localStorage.removeItem('temp_user_email');
      localStorage.removeItem('temp_user_password');
      setMfaEmail(null);
      
      console.log('🎉 [Auth] MFA login completed successfully');
      
      // ✅ CRITICAL: Return success so MFAVerify component can navigate to dashboard
      return { success: true };
    } catch (error: any) {
      console.error('❌ [Auth] MFA verification error:', error);
      
      return { 
        success: false, 
        error: {
          message: getErrorMessage(error),
          requires_mfa: false
        }
      };
    }
  };

  // Registration
  const register = async (email: string, password: string) => {
    try {
      console.log('📝 [Auth] Registration for:', email);
      
      const response = await authAPI.register({ email, password });
      
      console.log('📝 [Auth] Registration response:', response.data);
      
      if (response.data.message) {
        console.log('✅ [Auth] Registration successful, redirecting to login');
        return { 
          success: true, 
          message: response.data.message || "Registration successful! Please login to continue.",
          redirectToLogin: true
        };
      }
      
      return { 
        success: true, 
        message: "Registration successful! Please login to continue.",
        redirectToLogin: true
      };
      
    } catch (error: any) {
      console.error('❌ [Auth] Registration error:', error);
      return { 
        success: false, 
        error: {
          message: getErrorMessage(error),
          requires_mfa: false
        }
      };
    }
  };

  // Logout
  const logout = () => {
    console.log('👋 [Auth] Logging out');
    
    const performLogout = async () => {
      try {
        const currentToken = localStorage.getItem('token');
        if (currentToken) {
          await authAPI.logout();
          console.log('✅ [Auth] Backend logout successful');
        }
      } catch (error) {
        console.error('⚠️ [Auth] Backend logout error (non-critical):', error);
      } finally {
        clearAuthState();
      }
    };
    
    performLogout();
  };

  const clearMFAEmail = () => {
    console.log('🗑️ [Auth] Clearing MFA email state');
    localStorage.removeItem('mfa_email');
    localStorage.removeItem('mfa_pending');
    setMfaEmail(null);
  };

  const validateToken = async (): Promise<boolean> => {
    return await validateTokenWithBackend();
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    loginWithMFA,
    register,
    logout,
    loading,
    isAuthenticated: !!token && !!user,
    mfaEmail,
    clearMFAEmail,
    validateToken,
    skipMFAForSession,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};