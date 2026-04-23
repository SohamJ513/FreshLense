import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Divider,
  Button,
  Alert,
  CircularProgress,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  VpnKey as PasswordIcon,
  Security as SecurityIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import {
  updateNotificationSettings,
  changePassword,
  deleteAccount,
  getSettings,
  NotificationSettings,
} from '../services/userApi';

type AlertFrequency = 'immediately' | 'daily' | 'weekly';

const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Settings state with proper typing
  const [settings, setSettings] = useState<NotificationSettings & { mfa_enabled: boolean }>({
    email_alerts: true,
    alert_frequency: 'immediately',
    default_check_interval: 1440,
    mfa_enabled: false,
  });

  // Password change state
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // Delete account dialog
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [confirmEmail, setConfirmEmail] = useState('');
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await getSettings();
      setSettings({
        email_alerts: data.email_alerts ?? true,
        alert_frequency: (data.alert_frequency as AlertFrequency) ?? 'immediately',
        default_check_interval: data.default_check_interval ?? 1440,
        mfa_enabled: data.mfa_enabled ?? false,
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleAlertFrequencyChange = (value: string) => {
    setSettings({ 
      ...settings, 
      alert_frequency: value as AlertFrequency 
    });
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await updateNotificationSettings({
        email_alerts: settings.email_alerts,
        alert_frequency: settings.alert_frequency,
        default_check_interval: settings.default_check_interval,
      });
      setSuccess('Settings saved successfully');
    } catch (err: any) {
      setError(err.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      setPasswordError('Password must be at least 6 characters');
      return;
    }

    setSaving(true);
    setPasswordError('');

    try {
      await changePassword(currentPassword, newPassword);
      setSuccess('Password changed successfully');
      setShowPasswordDialog(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setPasswordError(err.message || 'Failed to change password');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (confirmEmail !== user?.email) {
      setError('Email confirmation does not match');
      return;
    }

    setDeleting(true);
    setError('');

    try {
      await deleteAccount();
      logout();
    } catch (err: any) {
      setError(err.message || 'Failed to delete account');
      setDeleting(false);
      setShowDeleteDialog(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
        Manage your account preferences and security settings
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {/* Notification Settings */}
      <Paper sx={{ borderRadius: 2, mb: 3 }}>
        <Box sx={{ p: 3, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <NotificationsIcon color="primary" />
            <Typography variant="h6" fontWeight="bold">
              Notifications
            </Typography>
          </Box>
        </Box>

        <Box sx={{ p: 3 }}>
          <FormControlLabel
            control={
              <Switch
                checked={settings.email_alerts}
                onChange={(e) =>
                  setSettings({ ...settings, email_alerts: e.target.checked })
                }
                color="primary"
              />
            }
            label="Email Alerts"
          />
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
            Receive email notifications when changes are detected on your monitored pages
          </Typography>

          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" fontWeight="500" gutterBottom>
              Alert Frequency
            </Typography>
            <Select
              size="small"
              value={settings.alert_frequency}
              onChange={(e) => handleAlertFrequencyChange(e.target.value)}
              sx={{ minWidth: 150 }}
            >
              <MenuItem value="immediately">Immediately</MenuItem>
              <MenuItem value="daily">Daily Digest</MenuItem>
              <MenuItem value="weekly">Weekly Digest</MenuItem>
            </Select>
          </Box>

          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" fontWeight="500" gutterBottom>
              Default Check Interval for New Pages
            </Typography>
            <Select
              size="small"
              value={settings.default_check_interval}
              onChange={(e) =>
                setSettings({ ...settings, default_check_interval: Number(e.target.value) })
              }
              sx={{ minWidth: 150 }}
            >
              <MenuItem value={60}>1 hour</MenuItem>
              <MenuItem value={360}>6 hours</MenuItem>
              <MenuItem value={720}>12 hours</MenuItem>
              <MenuItem value={1440}>24 hours</MenuItem>
              <MenuItem value={4320}>3 days</MenuItem>
              <MenuItem value={10080}>1 week</MenuItem>
            </Select>
          </Box>

          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSaveSettings}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Security Settings */}
      <Paper sx={{ borderRadius: 2, mb: 3 }}>
        <Box sx={{ p: 3, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SecurityIcon color="primary" />
            <Typography variant="h6" fontWeight="bold">
              Security
            </Typography>
          </Box>
        </Box>

        <Box sx={{ p: 3 }}>
          <List sx={{ p: 0 }}>
            <ListItem
              component="div"
              onClick={() => setShowPasswordDialog(true)}
              sx={{ 
                borderRadius: 2, 
                mb: 1, 
                cursor: 'pointer',
                '&:hover': { bgcolor: 'action.hover' }
              }}
            >
              <ListItemIcon>
                <PasswordIcon color="action" />
              </ListItemIcon>
              <ListItemText
                primary="Change Password"
                secondary="Update your account password"
              />
            </ListItem>

            <ListItem 
              component="div"
              sx={{ 
                borderRadius: 2, 
                cursor: 'pointer',
                '&:hover': { bgcolor: 'action.hover' }
              }}
            >
              <ListItemIcon>
                <SecurityIcon color="action" />
              </ListItemIcon>
              <ListItemText
                primary="Two-Factor Authentication"
                secondary={settings.mfa_enabled ? 'Enabled' : 'Disabled - Add extra security'}
              />
            </ListItem>
          </List>
        </Box>
      </Paper>

      {/* Danger Zone */}
      <Paper sx={{ borderRadius: 2, border: '1px solid', borderColor: 'error.main' }}>
        <Box sx={{ p: 3, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" fontWeight="bold" color="error">
            Danger Zone
          </Typography>
        </Box>

        <Box sx={{ p: 3 }}>
          <List sx={{ p: 0 }}>
            <ListItem
              component="div"
              onClick={() => setShowDeleteDialog(true)}
              sx={{ 
                borderRadius: 2, 
                cursor: 'pointer',
                color: 'error.main',
                '&:hover': { bgcolor: 'rgba(211, 47, 47, 0.04)' }
              }}
            >
              <ListItemIcon>
                <DeleteIcon color="error" />
              </ListItemIcon>
              <ListItemText
                primary="Delete Account"
                secondary="Permanently delete your account and all data"
              />
            </ListItem>
          </List>
        </Box>
      </Paper>

      {/* Change Password Dialog */}
      <Dialog open={showPasswordDialog} onClose={() => setShowPasswordDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            type="password"
            label="Current Password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            margin="normal"
          />
          <TextField
            fullWidth
            type="password"
            label="New Password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            margin="normal"
          />
          <TextField
            fullWidth
            type="password"
            label="Confirm New Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            margin="normal"
            error={!!passwordError}
            helperText={passwordError}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPasswordDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleChangePassword}
            disabled={saving}
          >
            {saving ? 'Changing...' : 'Change Password'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Account Dialog */}
      <Dialog open={showDeleteDialog} onClose={() => setShowDeleteDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle color="error">Delete Account</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            This action <strong>cannot be undone</strong>. This will permanently delete:
          </Typography>
          <Box component="ul" sx={{ mt: 1, mb: 2, pl: 2 }}>
            <li>Your account and profile information</li>
            <li>All monitored pages and their history</li>
            <li>All change logs and versions</li>
          </Box>
          <Typography variant="body2" color="error" sx={{ mb: 2 }}>
            Type <strong>{user?.email}</strong> to confirm:
          </Typography>
          <TextField
            fullWidth
            placeholder={user?.email}
            value={confirmEmail}
            onChange={(e) => setConfirmEmail(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDeleteDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDeleteAccount}
            disabled={deleting || confirmEmail !== user?.email}
          >
            {deleting ? 'Deleting...' : 'Permanently Delete Account'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SettingsPage;