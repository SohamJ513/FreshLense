export enum ClaimType {
  VERSION_INFO = "version_info",
  PERFORMANCE = "performance",
  SECURITY = "security",
  COMPATIBILITY = "compatibility",
  API_REFERENCE = "api_reference",
  CODE_EXAMPLE = "code_example",
  OTHER = "other"
}

export enum Verdict {
  TRUE = "true",
  FALSE = "false",
  UNVERIFIED = "unverified",
  INCONCLUSIVE = "inconclusive"
}

export interface FactCheckItem {
  claim: string;
  claim_type: ClaimType;
  context: string;
  verdict: Verdict;
  confidence: number;
  sources: string[];
  explanation: string;
}

export interface FactCheckRequest {
  version_id: string;
}

export interface DirectFactCheckRequest {
  content: string;
  page_url?: string;
  page_title?: string;
  user_email?: string; // ✅ ADD THIS FIELD
}

export interface FactCheckResponse {
  page_id: string;
  version_id: string;
  page_url: string;
  page_title: string;
  checked_at: string;
  results: FactCheckItem[];
  total_claims: number;
  verified_claims: number;
  unverified_claims: number;
  inconclusive_claims: number;
}

export interface PageVersionInfo {
  version_id: string;
  timestamp: string;
  content_preview: string;
  word_count: number;
  content_length: number;
}

export interface PageVersionsResponse {
  page_info: {
    page_id: string;
    url: string;
    display_name: string;
  };
  versions: PageVersionInfo[];
}

// ✅ OPTIONAL: You can also add these email-related types
export interface EmailNotificationSettings {
  enabled: boolean;
  email: string;
  sendImmediateResults: boolean;
  sendDailyDigest: boolean;
}

export interface EmailResultConfirmation {
  emailSent: boolean;
  recipientEmail: string;
  sentAt?: string;
  message?: string;
}