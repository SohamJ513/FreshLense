import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  Divider,
  Button,
  Alert,
  CircularProgress,
  TextField,
  Chip,
} from '@mui/material';
import {
  Email as EmailIcon,
  CalendarToday as CalendarIcon,
  Security as SecurityIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { getUserProfile, updateUserProfile } from '../services/userApi';

const ProfilePage: React.FC = () => {
  const { user, token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [profileData, setProfileData] = useState<any>(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const data = await getUserProfile();
      setProfileData(data);
      setDisplayName(data.display_name || '');
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await updateUserProfile({ display_name: displayName });
      setSuccess('Profile updated successfully');
      setIsEditing(false);
      await fetchProfile();
    } catch (err: any) {
      setError(err.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setDisplayName(profileData?.display_name || '');
    setIsEditing(false);
  };

  const getUserInitial = () => {
    if (displayName) return displayName.charAt(0).toUpperCase();
    if (user?.email) return user.email.charAt(0).toUpperCase();
    return 'U';
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
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
        Profile
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
        Manage your personal information and account settings
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

      <Paper sx={{ borderRadius: 2, overflow: 'hidden' }}>
        {/* Header with Avatar */}
        <Box
          sx={{
            bgcolor: 'primary.main',
            p: 4,
            textAlign: 'center',
            color: 'white',
          }}
        >
          <Avatar
            sx={{
              width: 100,
              height: 100,
              mx: 'auto',
              mb: 2,
              bgcolor: 'white',
              color: 'primary.main',
              fontSize: 40,
              fontWeight: 'bold',
            }}
          >
            {getUserInitial()}
          </Avatar>
          {isEditing ? (
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 2 }}>
              <TextField
                size="small"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter display name"
                sx={{ bgcolor: 'white', borderRadius: 1, width: 250 }}
                InputProps={{ sx: { bgcolor: 'white' } }}
              />
            </Box>
          ) : (
            <Typography variant="h5" fontWeight="bold">
              {displayName || user?.email?.split('@')[0] || 'User'}
            </Typography>
          )}
          <Typography variant="body2" sx={{ opacity: 0.8 }}>
            Member since {formatDate(profileData?.created_at)}
          </Typography>
        </Box>

        {/* Profile Details */}
        <Box sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            {isEditing ? (
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<CancelIcon />}
                  onClick={handleCancel}
                  disabled={saving}
                >
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </Button>
              </Box>
            ) : (
              <Button
                variant="outlined"
                startIcon={<EditIcon />}
                onClick={() => setIsEditing(true)}
              >
                Edit Profile
              </Button>
            )}
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Profile Info - Using Flexbox instead of Grid */}
          <Box sx={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: 3,
            '& > *': {
              flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)' },
              minWidth: 0,
            }
          }}>
            {/* Email */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <EmailIcon color="action" />
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Email Address
                </Typography>
                <Typography variant="body1">{user?.email}</Typography>
              </Box>
            </Box>

            {/* Account Created */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <CalendarIcon color="action" />
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Account Created
                </Typography>
                <Typography variant="body1">
                  {formatDate(profileData?.created_at)}
                </Typography>
              </Box>
            </Box>

            {/* MFA Status */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <SecurityIcon color="action" />
              <Box>
                <Typography variant="caption" color="text.secondary">
                  MFA Status
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                  <Chip
                    size="small"
                    label={profileData?.mfa_enabled ? 'Enabled' : 'Disabled'}
                    color={profileData?.mfa_enabled ? 'success' : 'default'}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {profileData?.mfa_enabled
                      ? 'Your account is secure with 2FA'
                      : 'Enable MFA in Settings for extra security'}
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default ProfilePage;