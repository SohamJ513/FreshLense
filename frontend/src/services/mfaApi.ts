// frontend/src/services/mfaApi.ts
import { authAPI } from './api';
import type { 
  MFALoginResponse,
  MFAStatus
} from '../types/mfa';

/**
 * MFA Verification Response with optional session token for "Remember Me" feature
 */
export interface MFAVerificationResponse {
  access_token: string;
  token_type: string;
  email: string;
  message: string;
  mfa_session_token?: string;  // For "Remember Me" feature - stores session token
  expires_in?: number;          // Expiry in seconds (86400 = 24 hours)
}

/**
 * Verify MFA code with optional "Remember Me" feature
 * @param email - User's email address
 * @param mfaCode - 6-digit MFA code
 * @param rememberForDay - If true, MFA session will be remembered for 24 hours
 */
export const verifyMFACode = async (
  email: string, 
  mfaCode: string, 
  rememberForDay: boolean = false
): Promise<MFAVerificationResponse> => {
  try {
    const response = await authAPI.verifyMFA(email, mfaCode, rememberForDay);
    return response.data;
  } catch (error: any) {
    console.error('MFA verification error:', error);
    throw new Error(
      error.response?.data?.detail || 
      error.response?.data?.message || 
      'Failed to verify MFA code. Please try again.'
    );
  }
};

/**
 * Alias for verifyMFACode - keeps compatibility with existing code
 */
export const verifyMFA = verifyMFACode;

/**
 * Send MFA code to user's email
 */
export const resendMFACode = async (email: string): Promise<{ message: string }> => {
  try {
    const response = await authAPI.sendMFACode(email);
    return response.data;
  } catch (error: any) {
    console.error('Resend MFA code error:', error);
    throw new Error(
      error.response?.data?.detail || 
      'Failed to send new verification code. Please try again.'
    );
  }
};

/**
 * Get MFA status for a user
 */
export const getMFAStatus = async (email: string): Promise<MFAStatus> => {
  try {
    const response = await authAPI.getMFAStatus(email);
    return response.data;
  } catch (error: any) {
    console.error('Get MFA status error:', error);
    throw error;
  }
};

/**
 * Enable MFA for user
 */
export const setupMFA = async (email: string, mfaEmail?: string): Promise<{ message: string }> => {
  try {
    const response = await authAPI.setupMFA(email, mfaEmail);
    return response.data;
  } catch (error: any) {
    console.error('Setup MFA error:', error);
    throw new Error(
      error.response?.data?.detail || 
      'Failed to enable MFA. Please try again.'
    );
  }
};

/**
 * Disable MFA for user
 */
export const disableMFA = async (email: string): Promise<{ message: string }> => {
  try {
    const response = await authAPI.disableMFA(email);
    return response.data;
  } catch (error: any) {
    console.error('Disable MFA error:', error);
    throw new Error(
      error.response?.data?.detail || 
      'Failed to disable MFA. Please try again.'
    );
  }
};

/**
 * Check if MFA session is still valid (for "Remember Me" feature)
 * @param email - User's email address
 * @param mfaSessionToken - Optional session token for validation
 */
export const checkMFASession = async (
  email: string, 
  mfaSessionToken?: string
): Promise<{ mfa_required: boolean; mfa_valid: boolean; session_exists?: boolean }> => {
  try {
    const response = await authAPI.checkMFASession(email, mfaSessionToken);
    return response.data;
  } catch (error: any) {
    console.error('Check MFA session error:', error);
    return { mfa_required: true, mfa_valid: false };
  }
};

/**
 * Clear MFA session on logout
 */
export const clearMFASession = (): void => {
  localStorage.removeItem('mfa_session_token');
  localStorage.removeItem('mfa_verified_at');
  console.log('✅ MFA session cleared');
};

/**
 * Get stored MFA session token
 */
export const getStoredMFASessionToken = (): string | null => {
  return localStorage.getItem('mfa_session_token');
};

/**
 * Check if stored MFA session is still valid (based on timestamp)
 */
export const isStoredMFASessionValid = (): boolean => {
  const mfaVerifiedAt = localStorage.getItem('mfa_verified_at');
  if (!mfaVerifiedAt) return false;
  
  try {
    const verifiedTime = new Date(mfaVerifiedAt);
    const now = new Date();
    const hoursElapsed = (now.getTime() - verifiedTime.getTime()) / (1000 * 60 * 60);
    return hoursElapsed < 24;
  } catch {
    return false;
  }
};

// Export types - REMOVED MFAVerificationResponse since it's already exported as an interface
export type { 
  MFALoginResponse,
  MFAStatus
};