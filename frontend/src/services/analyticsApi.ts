// frontend/src/services/analyticsApi.ts
import api from './api';
import { PageHealth, ChangeFrequencyData, FactAlert, CrawlFailure } from '../types/analytics';

export const analyticsApi = {
  // Get health scores for all pages
  getPageHealthScores: async (signal?: AbortSignal): Promise<{ success: boolean; data: PageHealth[] }> => {
    try {
      const response = await api.get('/analytics/page-health', { signal });
      return response.data;
    } catch (error) {
      console.error('Error fetching health scores:', error);
      throw error;
    }
  },

  // Get change frequency from version history
  getChangeFrequency: async (days: number = 30, signal?: AbortSignal): Promise<{ success: boolean; data: ChangeFrequencyData[] }> => {
    try {
      const response = await api.get(`/analytics/change-frequency?days=${days}`, { signal });
      return response.data;
    } catch (error) {
      console.error('Error fetching change frequency:', error);
      throw error;
    }
  },

  // Get fact-check alerts
  getFactAlerts: async (limit: number = 50, signal?: AbortSignal): Promise<{ success: boolean; data: FactAlert[] }> => {
    try {
      const response = await api.get(`/analytics/fact-alerts?limit=${limit}`, { signal });
      return response.data;
    } catch (error) {
      console.error('Error fetching fact-check alerts:', error);
      throw error;
    }
  },

  // Get failed crawls
  getFailedCrawls: async (signal?: AbortSignal): Promise<{ success: boolean; data: CrawlFailure[] }> => {
    try {
      const response = await api.get('/analytics/failed-crawls', { signal });
      return response.data;
    } catch (error) {
      console.error('Error fetching failed crawls:', error);
      throw error;
    }
  },

  // Mark alert as read
  markAlertAsRead: async (alertId: string): Promise<{ success: boolean }> => {
    try {
      const response = await api.patch(`/analytics/alerts/${alertId}/read`);
      return response.data;
    } catch (error) {
      console.error('Error marking alert as read:', error);
      throw error;
    }
  }
};