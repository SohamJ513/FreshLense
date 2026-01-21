// chrome_extension/frontend/src/services/mfaApi.ts
import { authAPI } from './api';
import type { 
  MFALoginResponse,
  MFAVerificationResponse,
  MFAStatus  // Changed from MFAStatusResponse to MFAStatus
} from '../types/mfa';

/**
 * Verify MFA code
 */
export const verifyMFACode = async (email: string, mfaCode: string): Promise<MFAVerificationResponse> => {
  try {
    const response = await authAPI.verifyMFA(email, mfaCode);
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
export const getMFAStatus = async (email: string): Promise<MFAStatus> => {  // Changed to MFAStatus
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

// Export types
export type { 
  MFALoginResponse,
  MFAVerificationResponse,
  MFAStatus  // Changed from MFAStatusResponse to MFAStatus
};