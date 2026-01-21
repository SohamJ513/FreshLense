// chrome_extension/frontend/src/types/mfa.ts
export interface MFALoginResponse {
  requires_mfa: boolean;
  email: string;
  message: string;
  access_token?: string;
  token_type?: string;
}

export interface MFAVerificationResponse {
  access_token: string;
  token_type: string;
  email: string;
  message: string;
}

export interface MFAStatus {
  mfa_enabled: boolean;
  mfa_email?: string;
  mfa_setup_completed: boolean;
}

export interface MFAVerificationRequest {
  email: string;
  mfa_code: string;
}

export interface MFASetupRequest {
  email: string;
  mfa_email?: string;
  enable_mfa: boolean;
}