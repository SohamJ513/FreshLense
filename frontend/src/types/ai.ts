// frontend/src/types/ai.ts

export interface AISummary {
  summary: string;
  key_changes: string[];
  change_type: 'major' | 'minor' | 'cosmetic';
  technical_impact: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  recommendation: string;
  tokens_used?: number;
  generated_at?: string;
  model_used?: string;
  error?: string;
  is_fallback?: boolean;
  disabled?: boolean;
}

export interface AISummaryResponse {
  success: boolean;
  data: {
    has_summary: boolean;
    summary?: AISummary;
    generated_at?: string;
    model_used?: string;
    message?: string;
  };
}

export interface AIStatusResponse {
  enabled: boolean;
  model: string;
  summaries_enabled: boolean;
  api_key_configured: boolean;
}

export interface VersionWithAISummary {
  id: string;
  page_id: string;
  timestamp: string;
  change_significance_score: number;
  has_ai_summary: boolean;
  ai_summary?: AISummary;
  text_content?: string;
  metadata?: any;
}

export interface RegenerateSummaryResponse {
  success: boolean;
  data: {
    summary: AISummary;
    message: string;
  };
}