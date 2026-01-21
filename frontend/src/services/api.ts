// frontend/src/services/api.ts
import axios, { AxiosError, AxiosHeaders } from 'axios';
import { MFALoginResponse } from '../types/mfa';

const API_BASE_URL = 'http://localhost:8000/api';

// Custom error type for MFA
class MFARequiredError extends Error {
  response?: {
    data: MFALoginResponse;
    status: number;
    statusText: string;
  };

  constructor(message: string, responseData?: MFALoginResponse, status?: number, statusText?: string) {
    super(message);
    this.name = 'MFARequiredError';
    if (responseData && status !== undefined) {
      this.response = {
        data: responseData,
        status,
        statusText: statusText || 'MFA Required'
      };
    }
  }
}

// Define the structure for error response data
interface ErrorResponseData {
  requires_mfa?: boolean;
  detail?: any;
  [key: string]: any; // Allow other properties
}

// Define the structure for axios error response
interface AxiosErrorResponse<T = ErrorResponseData> {
  data: T;
  status: number;
  statusText: string;
  headers: any;
}

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper function to safely get Authorization header as string
const getAuthorizationHeader = (): string | null => {
  const authHeader = api.defaults.headers.common['Authorization'];
  
  if (!authHeader) {
    return null;
  }
  
  // Handle different possible types
  if (typeof authHeader === 'string') {
    return authHeader;
  }
  
  if (Array.isArray(authHeader)) {
    return authHeader[0] as string;
  }
  
  // For AxiosHeaders or other types, convert to string
  return String(authHeader);
};

// Helper function to safely get substring of Authorization header
const getAuthHeaderSubstring = (start: number, end: number): string => {
  const authHeader = getAuthorizationHeader();
  if (!authHeader || typeof authHeader !== 'string') {
    return 'NOT SET';
  }
  return authHeader.substring(start, end) + '...';
};

// ✅ Request interceptor for auth token - WITH DEBUG LOGGING
api.interceptors.request.use(
  (config) => {
    // Check token in localStorage AND in axios defaults for debugging
    const tokenFromStorage = localStorage.getItem('token');
    const tokenFromAxios = getAuthorizationHeader();
    
    console.log(`🔍 [API] Request to ${config.url}:`);
    console.log(`  - Token in localStorage: ${tokenFromStorage ? `Present (${tokenFromStorage.length} chars)` : 'MISSING'}`);
    console.log(`  - Token in axios defaults: ${tokenFromAxios ? 'Set' : 'NOT SET'}`);
    
    // Always use token from storage
    if (tokenFromStorage) {
      config.headers.Authorization = `Bearer ${tokenFromStorage}`;
      console.log(`✅ [API] Authorization header set for ${config.url}`);
      
      // Also ensure axios defaults are synchronized
      if (!tokenFromAxios) {
        api.defaults.headers.common['Authorization'] = `Bearer ${tokenFromStorage}`;
        console.log(`🔄 [API] Fixed: Updated axios defaults with token from storage`);
      }
    } else {
      console.log(`❌ [API] No token found for ${config.url}`);
    }
    return config;
  },
  (error) => {
    console.error(`❌ [API] Request interceptor error:`, error);
    return Promise.reject(error);
  }
);

// ✅ Response interceptor with MFA and 401 handling - TEMPORARILY DISABLED AUTO-LOGOUT
api.interceptors.response.use(
  (response) => {
    console.log(`✅ [API] Response from ${response.config.url}: ${response.status}`);
    return response;
  },
  (error: AxiosError<ErrorResponseData>) => {
    const url = error.config?.url || 'unknown';
    const method = error.config?.method?.toUpperCase() || 'UNKNOWN';
    console.log(`❌ [API] ${method} ${url}: ${error.response?.status || 'No status'}`);
    
    // Check if error response indicates MFA is required
    if (error.response?.data?.requires_mfa) {
      console.log(`🔐 [API] MFA required detected for ${url}`);
      // Create a custom error that indicates MFA is required
      throw new MFARequiredError(
        'MFA_REQUIRED',
        error.response.data as MFALoginResponse,
        error.response.status,
        error.response.statusText
      );
    }

    // Handle 401 Unauthorized errors - TEMPORARILY DISABLED FOR DEBUGGING
    if (error.response?.status === 401) {
      console.log(`⚠️ [API] 401 Unauthorized for ${url}`);
      console.log(`🔍 [API] Debug information for 401:`);
      console.log(`  - URL: ${url}`);
      console.log(`  - Method: ${method}`);
      
      // Safely get token from localStorage
      const storedToken = localStorage.getItem('token');
      console.log(`  - Token in localStorage:`, storedToken ? `${storedToken.substring(0, 30)}...` : 'Missing');
      
      // Safely get axios Authorization header
      const axiosHeader = getAuthorizationHeader();
      console.log(`  - Axios defaults Authorization:`, axiosHeader ? `${axiosHeader.substring(0, 50)}...` : 'NOT SET');
      
      console.log(`  - Request headers sent:`, JSON.stringify(error.config?.headers, null, 2));
      console.log(`  - Error detail:`, error.response?.data);
      
      // Check if there's a mismatch between localStorage and axios
      if (storedToken && !axiosHeader) {
        console.log(`🔄 [API] FIX ATTEMPT: Token exists in localStorage but not in axios defaults!`);
        console.log(`🔄 [API] Attempting to fix by setting axios defaults...`);
        api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
        console.log(`✅ [API] Axios defaults updated. Retry the request.`);
      }
      
      if (!storedToken && axiosHeader) {
        console.log(`🔄 [API] FIX ATTEMPT: Token in axios defaults but not in localStorage!`);
        console.log(`🔄 [API] Clearing invalid axios header...`);
        delete api.defaults.headers.common['Authorization'];
      }
      
      // ✅ TEMPORARILY COMMENTED OUT - Don't auto-clear or redirect while debugging
      /*
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // Only redirect if not on login page
      if (!window.location.pathname.includes('/login')) {
        setTimeout(() => {
          window.location.href = '/login';
        }, 100);
      }
      */
    }

    // Normal error normalization
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (Array.isArray(detail)) {
        error.response.data.detail = detail
          .map((err: any) => err.msg || JSON.stringify(err))
          .join(', ');
      } else if (typeof detail === 'object') {
        error.response.data.detail = JSON.stringify(detail);
      }
    }
    
    console.error(`[API] Error details:`, error.response?.data);
    return Promise.reject(error);
  }
);

// ---------------- Types ----------------
export interface User {
  id: string;
  email: string;
  created_at: string;
  mfa_enabled?: boolean;
  mfa_email?: string;
}

export interface TrackedPage {
  id: string;
  user_id: string;
  url: string;
  display_name: string | null;
  check_interval_minutes: number;
  is_active: boolean;
  created_at: string;
  last_checked: string | null;
  last_change_detected: string | null;
  current_version_id: string | null;
}

export interface PageVersion {
  id: string;
  page_id: string;
  timestamp: string;
  text_content: string;
  metadata: {
    url: string;
    content_length: number;
    word_count: number;
    fetched_at: string;
  };
}

export interface ChangeLog {
  id: string;
  page_id: string;
  user_id: string;
  type: string;
  timestamp: string;
  description: string | null;
  semantic_similarity_score: number | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  email?: string;
  message?: string;
}

export interface CrawlResponse {
  status: string;
  url: string;
  content_length: number;
  content_preview: string | null;
  full_content: string;
}

export interface CrawlPageResponse {
  status: string;
  page_id: string;
  url: string;
  version_id: string;
  change_detected: boolean;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  scheduler_running: boolean;
}

export interface DeleteResponse {
  status: string;
  message: string;
}

// Forgot Password Types
export interface ForgotPasswordResponse {
  message: string;
  status: string;
}

export interface ResetPasswordResponse {
  message: string;
  status: string;
}

// MFA Types
export interface MFAVerifyResponse {
  access_token: string;
  token_type: string;
  email: string;
  message: string;
}

export interface MFASendCodeResponse {
  message: string;
}

export interface MFAStatusResponse {
  mfa_enabled: boolean;
  mfa_email?: string;
  mfa_setup_completed: boolean;
}

// ---------------- Auth API ----------------
export const authAPI = {
  register: (userData: { email: string; password: string }) =>
    api.post<User>('/auth/register', userData),

  // ✅ FIXED: Changed to 'email' field and sends as JSON
  login: (credentials: { email: string; password: string }) => {
    console.log('[Auth] Sending login request for:', credentials.email);
    return api.post<LoginResponse | MFALoginResponse>('/auth/login', {
      email: credentials.email,
      password: credentials.password
    });
  },

  // Forgot Password endpoints
  forgotPassword: (email: string) =>
    api.post<ForgotPasswordResponse>('/auth/forgot-password', { email }),

  resetPassword: (token: string, newPassword: string) =>
    api.post<ResetPasswordResponse>('/auth/reset-password', { 
      token, 
      new_password: newPassword 
    }),

  // ✅ MFA Endpoints
  verifyMFA: (email: string, mfaCode: string) => {
    console.log('[Auth] Verifying MFA for:', email);
    console.log('[Auth] Current axios Authorization before MFA:', getAuthorizationHeader());
    return api.post<MFAVerifyResponse>('/auth/verify-mfa', { 
      email, 
      mfa_code: mfaCode 
    });
  },

  sendMFACode: (email: string) =>
    api.post<MFASendCodeResponse>('/auth/send-mfa-code', { email }),

  getMFAStatus: (email: string) =>
    api.get<MFAStatusResponse>('/auth/mfa-status', { params: { email } }),

  setupMFA: (email: string, mfaEmail?: string) =>
    api.post<{ message: string }>('/auth/setup-mfa', { 
      email, 
      mfa_email: mfaEmail,
      enable_mfa: true 
    }),

  disableMFA: (email: string) =>
    api.post<{ message: string }>('/auth/disable-mfa', { email }),

  // ✅ New: Test endpoint to verify token is working
  testAuth: () => api.get<{ message: string; user: string }>('/auth/test', {
    validateStatus: (status) => status < 500 // Don't throw on 401/403
  }),
};

// ---------------- Pages API ----------------
export const pagesAPI = {
  getAll: () => {
    console.log('[Pages] Fetching all pages');
    console.log('[Pages] Current axios Authorization:', getAuthorizationHeader());
    return api.get<TrackedPage[]>('/pages');
  },
  
  getOne: (id: string) => api.get<TrackedPage>(`/pages/${id}`),
  
  create: (pageData: { 
    url: string; 
    display_name?: string; 
    check_interval_minutes?: number 
  }) => api.post<TrackedPage>('/pages', pageData),
  
  delete: (id: string) => api.delete<DeleteResponse>(`/pages/${id}`),
  
  getVersions: (pageId: string) => api.get<PageVersion[]>(`/pages/${pageId}/versions`),
  
  getByUrl: (url: string) => api.get<TrackedPage>(`/pages/by-url?url=${encodeURIComponent(url)}`),
};

// ---------------- Change Logs API ----------------
export const changesAPI = {
  getAll: () => api.get<ChangeLog[]>('/changes'),
};

// ---------------- Crawl API ----------------
export const crawlAPI = {
  crawlUrl: (url: string) => 
    api.post<CrawlResponse>('/crawl', null, { 
      params: { url } 
    }),
  
  crawlPage: (pageId: string) => 
    api.post<CrawlPageResponse>(`/crawl/${pageId}`),
};

// ---------------- Health API ----------------
export const healthAPI = {
  check: () => api.get<HealthResponse>('/health'),
};

// ---------------- MFA API Functions (for backward compatibility) ----------------
export const mfaAPI = {
  verify: authAPI.verifyMFA,
  sendCode: authAPI.sendMFACode,
  getStatus: authAPI.getMFAStatus,
  setup: authAPI.setupMFA,
  disable: authAPI.disableMFA,
};

// ---------------- Utility Functions ----------------
export const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'Never';
  return new Date(dateString).toLocaleString();
};

export const formatTimeAgo = (dateString: string | null): string => {
  if (!dateString) return 'Never';
  
  const now = new Date();
  const date = new Date(dateString);
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  return `${Math.floor(diffInSeconds / 86400)} days ago`;
};

export const getStatusColor = (page: TrackedPage): string => {
  if (!page.is_active) return 'gray';
  if (page.last_change_detected) return 'green';
  if (page.last_checked) return 'blue';
  return 'yellow';
};

export const getStatusText = (page: TrackedPage): string => {
  if (!page.is_active) return 'Inactive';
  if (page.last_change_detected) return 'Changed';
  if (page.last_checked) return 'Monitored';
  return 'Pending';
};

// ✅ Token management utilities - UPDATED
export const tokenUtils = {
  getToken: (): string | null => {
    const token = localStorage.getItem('token');
    console.log(`[Token] Get token: ${token ? `Present (${token.length} chars)` : 'Missing'}`);
    return token;
  },
  
  setToken: (token: string): void => {
    console.log(`[Token] Setting token: ${token.substring(0, 20)}...`);
    localStorage.setItem('token', token);
    
    // Update axios defaults
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    console.log(`[Token] Axios defaults updated`);
    
    const authHeader = getAuthorizationHeader();
    console.log(`[Token] New axios Authorization:`, authHeader ? `${authHeader.substring(0, 50)}...` : 'NOT SET');
  },
  
  removeToken: (): void => {
    console.log(`[Token] Removing token`);
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
    console.log(`[Token] Axios Authorization cleared`);
  },
  
  isTokenValid: (): boolean => {
    const token = localStorage.getItem('token');
    if (!token) {
      console.log(`[Token] No token found`);
      return false;
    }
    
    try {
      // Basic JWT structure check (doesn't verify signature)
      const parts = token.split('.');
      if (parts.length !== 3) {
        console.log(`[Token] Invalid token structure`);
        return false;
      }
      
      const payload = JSON.parse(atob(parts[1]));
      const isValid = payload.exp * 1000 > Date.now();
      console.log(`[Token] Token valid: ${isValid}, expires: ${new Date(payload.exp * 1000).toISOString()}`);
      return isValid;
    } catch (error) {
      console.error(`[Token] Token validation error:`, error);
      return false;
    }
  },
  
  // ✅ MFA Token Handling
  setMFAToken: (tokenData: { access_token: string; token_type: string }): void => {
    console.log(`[Token] Setting MFA token`);
    localStorage.setItem('token', tokenData.access_token);
    localStorage.setItem('token_type', tokenData.token_type);
    api.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access_token}`;
    console.log(`[Token] MFA token set and axios configured`);
  },
  
  clearAuthData: (): void => {
    console.log(`[Token] Clearing all auth data`);
    localStorage.removeItem('token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('user');
    delete api.defaults.headers.common['Authorization'];
  },
  
  // ✅ NEW: Debug function to check token status
  debugToken: (): void => {
    console.log(`🔍 [Token Debug] === START ===`);
    const token = localStorage.getItem('token');
    console.log(`  - Token in localStorage:`, token ? `Present (${token.length} chars)` : 'Missing');
    console.log(`  - Token preview:`, token ? `${token.substring(0, 50)}...` : 'Missing');
    
    const authHeader = getAuthorizationHeader();
    console.log(`  - Axios Authorization header:`, authHeader ? `${authHeader.substring(0, 50)}...` : 'NOT SET');
    
    if (token) {
      try {
        const parts = token.split('.');
        console.log(`  - Token parts:`, parts.length);
        if (parts.length === 3) {
          const payload = JSON.parse(atob(parts[1]));
          console.log(`  - Token payload:`, payload);
          if (payload.exp) {
            const remaining = (payload.exp * 1000) - Date.now();
            console.log(`  - Time remaining:`, Math.floor(remaining / 1000), 'seconds');
          }
        }
      } catch (e) {
        console.error(`  - Token parse error:`, e);
      }
    }
    console.log(`🔍 [Token Debug] === END ===`);
  },
};

// ✅ Helper function to check if error is MFA-related
export const isMFARequiredError = (error: any): boolean => {
  const isMFA = (
    error?.message === 'MFA_REQUIRED' ||
    error?.name === 'MFARequiredError' ||
    error?.response?.data?.requires_mfa ||
    error?.requires_mfa
  );
  console.log(`[MFA] isMFARequiredError check: ${isMFA}`);
  return isMFA;
};

// ✅ Helper function to extract MFA data from error
export const getMFADataFromError = (error: any): MFALoginResponse | null => {
  if (isMFARequiredError(error)) {
    console.log(`[MFA] Extracting MFA data from error`);
    return {
      requires_mfa: true,
      email: error.response?.data?.email || error.email || '',
      message: error.response?.data?.message || error.message || 'MFA verification required',
      access_token: error.response?.data?.access_token,
      token_type: error.response?.data?.token_type,
    };
  }
  return null;
};

// ✅ NEW: Test function to verify API connectivity
export const testAPIConnection = async (): Promise<{ success: boolean; message: string }> => {
  try {
    console.log(`🧪 [API Test] Testing connection to ${API_BASE_URL}`);
    const response = await api.get('/health', {
      timeout: 5000,
      validateStatus: (status) => status < 500
    });
    console.log(`✅ [API Test] Connection successful:`, response.status);
    return { success: true, message: `API is reachable (${response.status})` };
  } catch (error: any) {
    console.error(`❌ [API Test] Connection failed:`, error.message);
    return { 
      success: false, 
      message: `API connection failed: ${error.message}` 
    };
  }
};

// Export custom error type
export { MFARequiredError };

export default api;