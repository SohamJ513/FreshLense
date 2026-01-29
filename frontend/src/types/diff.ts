export enum ChangeType {
  ADDED = "added",
  REMOVED = "removed", 
  MODIFIED = "modified"
}

export interface ContentChange {
  change_type: ChangeType;
  old_content: string;
  new_content: string;
  line_range_old: [number, number];
  line_range_new: [number, number];
  
  // Enhanced visualization
  highlighted_old?: string;
  highlighted_new?: string;
  context_before?: string;
  context_after?: string;
  change_summary?: string;
  
  // Metadata
  word_count_old?: number;
  word_count_new?: number;
  char_count_old?: number;
  char_count_new?: number;
}

export interface SideBySideLine {
  old_line?: string;
  new_line?: string;
  type: string;
  old_line_num?: number;
  new_line_num?: number;
  highlighted_old?: string;
  highlighted_new?: string;
}

export interface DiffRequest {
  old_version_id: string;
  new_version_id: string;
}

export interface DiffResponse {
  page_id: string;
  old_version_id: string;
  new_version_id: string;
  old_timestamp: string;
  new_timestamp: string;
  changes: ContentChange[];
  total_changes: number;
  
  // Optional enhanced data
  change_metrics?: {
    words_added: number;
    words_removed: number;
    total_words_old?: number;
    total_words_new?: number;
    similarity_score: number;
    change_percentage?: number;
    lines_added?: number;
    lines_removed?: number;
  };
  
  html_diff?: string;
  side_by_side_diff?: SideBySideLine[];
  
  has_changes: boolean;
  change_percentage?: number;
  similarity_score?: number;
}

// For API calls
export interface CompareVersionsParams {
  pageId: string;
  version1Id: string;
  version2Id: string;
}

// For component props
export interface DiffViewerProps {
  diffData?: DiffResponse;
  changes?: ContentChange[];
  isLoading?: boolean;
  error?: string;
}

// ✅ ADDED: Version information interface
export interface VersionInfo {
  id: string;
  page_id: string;
  version_number: number;
  captured_at: string;
  content_preview: string;
  title: string;
  has_content: boolean;
  
  // Legacy fields for backward compatibility
  version_id?: string;
  timestamp?: string;
  word_count?: number;
  content_length?: number;
  metadata?: {
    url?: string;
    content_length?: number;
    word_count?: number;
    html_content_length?: number;
    fetched_at?: string;
  };
}

// ✅ ADDED: Page information interface
export interface PageInfo {
  id: string;
  url: string;
  title: string;
  last_checked?: string;
  version_count: number;
  is_active: boolean;
  
  // Additional fields that might come from backend
  display_name?: string;
  check_interval_minutes?: number;
  created_at?: string;
  last_change_detected?: string;
  current_version_id?: string;
}

// ✅ ADDED: Response for /pages endpoint
export interface PageListResponse {
  pages: PageInfo[];
  total?: number;
  skip?: number;
  limit?: number;
}

// ✅ ADDED: Version detail response
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

// ✅ ADDED: For version comparison in UI
export interface VersionComparison {
  version1_id: string;
  version2_id: string;
  version1_content: string;
  version2_content: string;
  version1_timestamp: string;
  version2_timestamp: string;
}

// ✅ ADDED: Change metrics for summary display
export interface ChangeMetrics {
  words_added: number;
  words_removed: number;
  total_words_old: number;
  total_words_new: number;
  similarity_score: number;
  change_percentage: number;
  lines_added: number;
  lines_removed: number;
}

// ✅ ADDED: For filtering/sorting versions
export interface VersionFilterOptions {
  page_id?: string;
  start_date?: string;
  end_date?: string;
  has_content?: boolean;
  limit?: number;
  offset?: number;
  sort_by?: 'captured_at' | 'version_number';
  sort_order?: 'asc' | 'desc';
}