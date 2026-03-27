// frontend/src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI, isMFARequiredError, getMFADataFromError, LoginResponse, tokenUtils, testAPIConnection } from '../services/api';
import { MFALoginResponse } from '../types/mfa';
import { verifyMFACode } from '../services/mfaApi';
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
  loginWithMFA: (email: string, mfaCode: string) => Promise<{ success: boolean; error?: any }>;
  register: (email: string, password: string) => Promise<{ success: boolean; message?: string; redirectToLogin?: boolean; error?: any }>;
  logout: () => void;
  loading: boolean;
  isAuthenticated: boolean;
  mfaEmail: string | null;
  clearMFAEmail: () => void;
  validateToken: () => Promise<boolean>;
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

  // ✅ FIXED: Function to validate token with backend - REMOVED DOUBLE /api/
  const validateTokenWithBackend = async (): Promise<boolean> => {
    const storedToken = localStorage.getItem('token');
    if (!storedToken) {
      console.log('🔍 [Auth] No token to validate');
      return false;
    }

    try {
      console.log('🔍 [Auth] Validating token with backend...');
      // ✅ FIXED: Use authAPI.validateToken() instead of direct api.post()
      const response = await authAPI.validateToken(storedToken);
      return response.data.valid === true;
    } catch (error) {
      console.log('❌ [Auth] Token validation failed:', error);
      return false;
    }
  };

  // ✅ NEW: Function to sync auth state
  const syncAuthState = async () => {
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    const storedMFAEmail = localStorage.getItem('mfa_email');
    const storedMFAPending = localStorage.getItem('mfa_pending') === 'true';
    
    console.log('🔍 [Auth] Syncing auth state:', {
      hasToken: !!storedToken,
      hasUser: !!storedUser,
      mfaEmail: storedMFAEmail,
      mfaPending: storedMFAPending
    });

    // First, validate token if exists
    if (storedToken) {
      const isValid = await validateTokenWithBackend();
      
      if (isValid) {
        console.log('✅ [Auth] Token is valid, setting up auth');
        setToken(storedToken);
        
        if (storedUser) {
          try {
            setUser(JSON.parse(storedUser));
          } catch (error) {
            console.error('Failed to parse stored user:', error);
          }
        }
        
        // Configure axios with token
        tokenUtils.setToken(storedToken);
        
        // Clear any MFA state if we have valid token
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
      // If no token but MFA state exists, restore MFA state
      if (storedMFAEmail) {
        console.log('🔐 [Auth] Restoring MFA state for:', storedMFAEmail);
        setMfaEmail(storedMFAEmail);
      } else {
        // Ensure clean state
        clearAuthState();
      }
    }
    
    setLoading(false);
  };

  // ✅ NEW: Function to clear auth state
  const clearAuthState = () => {
    console.log('🗑️ [Auth] Clearing auth state');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('mfa_pending');
    localStorage.removeItem('mfa_email');
    localStorage.removeItem('temp_user_email');
    
    setToken(null);
    setUser(null);
    setMfaEmail(null);
    
    tokenUtils.clearAuthData();
  };

  useEffect(() => {
    syncAuthState();
  }, []);

  // ✅ NEW: Function to store auth data consistently
  const storeAuthData = (accessToken: string, userEmail: string) => {
    console.log('💾 [Auth] Storing auth data for:', userEmail);
    
    const userData = { email: userEmail };
    
    // Store in localStorage
    localStorage.setItem('token', accessToken);
    localStorage.setItem('user', JSON.stringify(userData));
    
    // Store in state
    setToken(accessToken);
    setUser(userData);
    
    // Configure axios
    tokenUtils.setToken(accessToken);
    
    // Clear MFA state
    localStorage.removeItem('mfa_pending');
    localStorage.removeItem('mfa_email');
    setMfaEmail(null);
    
    console.log('✅ [Auth] Auth data stored and synchronized');
  };

  // ✅ Helper to extract error message
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

  // ✅ Updated login function - ALWAYS expects MFA from backend
  const login = async (email: string, password: string) => {
    try {
      // Clear previous auth state
      clearAuthState();
      
      console.log('🔐 [Auth] Login attempt for:', email);
      
      // Test API connection first
      const apiTest = await testAPIConnection();
      if (!apiTest.success) {
        throw new Error(`Backend is not reachable: ${apiTest.message}`);
      }
      
      const response = await authAPI.login({
        email: email,
        password: password,
      });
      
      console.log('🔐 [Auth] Login response:', response.data);
      
      const responseData = response.data;
      
      // ✅ Backend ALWAYS returns MFA required response
      if (isMFAResponse(responseData)) {
        console.log('🔐 [Auth] MFA required detected - storing state');
        
        // Store MFA state in localStorage for persistence
        const mfaEmailToStore = responseData.email || email;
        localStorage.setItem('mfa_pending', 'true');
        localStorage.setItem('mfa_email', mfaEmailToStore);
        
        // Update state
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
      
      // Fallback for any unexpected response
      if (isLoginResponse(responseData)) {
        console.log('⚠️ [Auth] Unexpected token response (MFA should be required)');
        storeAuthData(responseData.access_token, email);
        return { success: true };
      }
      
      throw new Error('Invalid response from server');
      
    } catch (error: any) {
      console.error('❌ [Auth] Login error:', error);
      
      // Check if error is MFA-related
      if (isMFARequiredError(error)) {
        console.log('🔐 [Auth] MFA error detected via helper');
        const mfaData = getMFADataFromError(error);
        if (mfaData) {
          // Store MFA state
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

  // ✅ Login with MFA verification
  const loginWithMFA = async (email: string, mfaCode: string) => {
    try {
      console.log('🚀 [Auth] MFA verification for:', email);
      
      const mfaResponse = await verifyMFACode(email, mfaCode);
      
      console.log('✅ [Auth] MFA verification API response received');
      
      const accessToken = (mfaResponse as any).access_token;
      
      if (!accessToken) {
        console.error('❌ [Auth] No access token in MFA response');
        throw new Error('No access token received from MFA verification');
      }
      
      console.log('🔑 [Auth] Token received, length:', accessToken.length);
      
      // Store auth data
      storeAuthData(accessToken, email);
      
      // Clear MFA state
      localStorage.removeItem('mfa_pending');
      localStorage.removeItem('mfa_email');
      setMfaEmail(null);
      
      console.log('🎉 [Auth] MFA login completed successfully');
      
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

  // ✅ UPDATED: Registration - no auto-login, redirect to login
  const register = async (email: string, password: string) => {
    try {
      console.log('📝 [Auth] Registration for:', email);
      
      const response = await authAPI.register({ email, password });
      
      console.log('📝 [Auth] Registration response:', response.data);
      
      // ✅ Registration successful - return success with message, redirect to login
      if (response.data.message) {
        console.log('✅ [Auth] Registration successful, redirecting to login');
        return { 
          success: true, 
          message: response.data.message || "Registration successful! Please login to continue.",
          redirectToLogin: true
        };
      }
      
      // Fallback success response
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

  const logout = () => {
    console.log('👋 [Auth] Logging out');
    clearAuthState();
  };

  const clearMFAEmail = () => {
    console.log('🗑️ [Auth] Clearing MFA email state');
    localStorage.removeItem('mfa_email');
    localStorage.removeItem('mfa_pending');
    setMfaEmail(null);
  };

  // ✅ FIXED: Public method to validate token
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
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};