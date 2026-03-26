// frontend/src/services/aiApi.ts
import api from './api';
import { AISummary, AISummaryResponse, AIStatusResponse, RegenerateSummaryResponse } from '../types/ai';

export const aiApi = {
  /**
   * Get AI summary for a specific version
   */
  getVersionSummary: async (pageId: string, versionId: string): Promise<AISummaryResponse> => {
    try {
      const response = await api.get(`/pages/${pageId}/versions/${versionId}/summary`);
      return response.data;
    } catch (error) {
      console.error('Error fetching AI summary:', error);
      throw error;
    }
  },

  /**
   * Regenerate AI summary for a version
   */
  regenerateSummary: async (pageId: string, versionId: string): Promise<RegenerateSummaryResponse> => {
    try {
      const response = await api.post(`/pages/${pageId}/versions/${versionId}/regenerate-summary`);
      return response.data;
    } catch (error) {
      console.error('Error regenerating AI summary:', error);
      throw error;
    }
  },

  /**
   * Get AI service status
   */
  getAIStatus: async (): Promise<AIStatusResponse> => {
    try {
      const response = await api.get('/ai/status');
      return response.data;
    } catch (error) {
      console.error('Error fetching AI status:', error);
      throw error;
    }
  },

  /**
   * Compare two versions with AI summary
   */
  compareVersions: async (pageId: string, version1Id: string, version2Id: string): Promise<any> => {
    try {
      const response = await api.get(`/pages/${pageId}/versions/compare/${version1Id}/${version2Id}`);
      return response.data;
    } catch (error) {
      console.error('Error comparing versions:', error);
      throw error;
    }
  }
};