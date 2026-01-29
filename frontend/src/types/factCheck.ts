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
  user_email?: string;
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

// ✅ UPDATED: PageVersionInfo to support both old and new structures
export interface PageVersionInfo {
  // ✅ NEW FIELDS (from backend)
  id: string;                    // Unique version ID
  page_id: string;              // Page ID this version belongs to
  version_number: number;       // Sequential version number
  captured_at: string;          // When this version was captured
  content_preview: string;      // Preview of content
  title: string;                // Display title for the version
  has_content?: boolean;        // Whether content exists
  
  // ✅ LEGACY FIELDS (for backward compatibility)
  version_id?: string;          // Legacy field - same as id
  timestamp?: string;           // Legacy field - same as captured_at
  word_count?: number;          // Optional word count
  content_length?: number;      // Optional character count
  
  // ✅ ADDITIONAL METADATA (optional)
  metadata?: {
    url?: string;
    content_length?: number;
    word_count?: number;
    html_content_length?: number;
    fetched_at?: string;
  };
}

// ✅ UPDATED: PageInfo for the /pages endpoint response
export interface PageInfo {
  id: string;                    // Page ID
  url: string;                  // Page URL
  title: string;                // Display name or title
  last_checked?: string;        // When last checked
  version_count: number;        // Number of versions available
  is_active: boolean;           // Whether page is actively monitored
  
  // ✅ ADDITIONAL FIELDS (from database)
  display_name?: string;        // Alternative display name
  check_interval_minutes?: number;
  created_at?: string;
  last_change_detected?: string;
  current_version_id?: string;
}

// ✅ UPDATED: PageVersionsResponse to be more flexible
export interface PageVersionsResponse {
  // ✅ MAIN DATA
  versions: PageVersionInfo[];  // List of versions
  
  // ✅ OPTIONAL PAGE INFO (may come from separate endpoint)
  page_info?: {
    page_id: string;
    url: string;
    display_name: string;
    last_checked?: string;
    version_count?: number;
  };
  
  // ✅ FOR DIRECT RESPONSE FROM /pages/{id}/versions
  page_id?: string;             // Page ID from URL param
  url?: string;                 // Page URL
  title?: string;               // Page title
  
  // ✅ PAGINATION INFO
  total?: number;
  skip?: number;
  limit?: number;
}

// ✅ NEW: Response for /pages endpoint
export interface PagesListResponse {
  pages: PageInfo[];
  total: number;
  skip?: number;
  limit?: number;
}

// ✅ NEW: Version detail response
export interface VersionDetailResponse {
  id: string;
  page_id: string;
  timestamp: string;
  text_content: string;
  html_content?: string;
  page_title: string;
  page_url: string;
  metadata?: Record<string, any>;
}

// ✅ EMAIL RELATED TYPES
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

// ✅ NEW: Error response type
export interface ApiErrorResponse {
  error: string;
  detail?: string;
  code?: string;
  timestamp?: string;
}

// ✅ NEW: Comparison request type
export interface VersionComparisonRequest {
  old_version_id: string;
  new_version_id: string;
}

// ✅ NEW: Success response wrapper
export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
  message?: string;
  timestamp: string;
}