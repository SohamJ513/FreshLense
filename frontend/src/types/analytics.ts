// frontend/src/types/analytics.ts

export interface PageHealth {
  pageId: string;
  pageUrl: string;
  pageTitle: string;
  avgConfidence: number;
  totalVersions: number;
  significantChanges: number;
  lastChecked: string;
  healthScore: number;
  healthStatus: 'healthy' | 'warning' | 'critical';
  metrics: {
    avgChangeSignificance: number;
    totalFactChecks: number;
    verifiedCount: number;
    debunkedCount: number;
  };
}

export interface ChangeFrequencyData {
  date: string;
  count: number;
  significantCount: number;
  pages: Array<{
    pageId: string;
    pageTitle: string;
    changeCount: number;
    significanceScore: number;
  }>;
}

export interface FactAlert {
  id: string;
  pageId: string;
  pageTitle: string;
  pageUrl: string;
  type: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string;
  confidence: number;
  oldFact?: string;
  newFact?: string;
  read: boolean;
  changeSignificanceScore?: number;
}

export interface CrawlFailure {
  pageId: string;
  pageUrl: string;
  pageTitle: string;
  failedAttempts: number;
  lastAttempt: string;
  errorMessage?: string;
}