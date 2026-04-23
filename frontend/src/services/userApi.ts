import api from './api';

export interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  created_at: string;
  mfa_enabled: boolean;
}

export interface NotificationSettings {
  email_alerts: boolean;
  alert_frequency: 'immediately' | 'daily' | 'weekly';
  default_check_interval: number;
}

export const getUserProfile = async (): Promise<UserProfile> => {
  const response = await api.get('/user/profile');
  return response.data;
};

export const updateUserProfile = async (data: { display_name: string }): Promise<UserProfile> => {
  const response = await api.put('/user/profile', data);
  return response.data;
};

export const getSettings = async (): Promise<NotificationSettings & { mfa_enabled: boolean }> => {
  const response = await api.get('/user/settings');
  return response.data;
};

export const updateNotificationSettings = async (settings: NotificationSettings): Promise<void> => {
  await api.put('/user/settings/notifications', settings);
};

export const changePassword = async (current_password: string, new_password: string): Promise<void> => {
  await api.put('/user/password', { current_password, new_password });
};

export const deleteAccount = async (): Promise<void> => {
  await api.delete('/user/account');
};