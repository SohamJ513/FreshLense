// frontend/src/services/factCheckApi.ts
import api from './api';
import { 
  FactCheckRequest, 
  FactCheckResponse, 
  PageVersionsResponse,
  DirectFactCheckRequest 
} from '../types/factCheck';
import { DiffRequest, DiffResponse } from '../types/diff';

export const factCheckApi = {
  // ✅ FIXED: Get all tracked pages for user
  getPages: async (): Promise<any[]> => {
    const response = await api.get('/fact-check/pages');
    return response.data;
  },

  // ✅ FIXED: Get page versions - corrected endpoint path
  getPageVersions: async (pageId: string, limit: number = 20): Promise<PageVersionsResponse> => {
    const response = await api.get(`/fact-check/pages/${pageId}/versions?limit=${limit}`);
    return response.data;
  },

  // Get specific version by ID
  getVersionById: async (versionId: string): Promise<any> => {
    const response = await api.get(`/fact-check/versions/${versionId}`);
    return response.data;
  },

  // Run fact check on a specific version
  runFactCheck: async (versionId: string): Promise<FactCheckResponse> => {
    const response = await api.post('/fact-check/check', { version_id: versionId });
    return response.data;
  },

  // Run fact check on direct text content
  checkDirectContent: async (request: DirectFactCheckRequest): Promise<FactCheckResponse> => {
    const response = await api.post('/fact-check/check-direct', request);
    return response.data;
  },

  // Compare two versions
  compareVersions: async (oldVersionId: string, newVersionId: string): Promise<DiffResponse> => {
    const response = await api.post('/fact-check/compare', {
      old_version_id: oldVersionId,
      new_version_id: newVersionId
    });
    return response.data;
  }
};