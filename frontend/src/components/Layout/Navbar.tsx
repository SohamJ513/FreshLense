// frontend/src/components/Layout/Navbar.tsx
import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  Dashboard as DashboardIcon,
  FactCheck as FactCheckIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);

  const handleLogoutClick = () => {
    setLogoutDialogOpen(true);
  };

  const handleConfirmLogout = () => {
    setLogoutDialogOpen(false);
    logout();
    navigate('/'); // Redirect to landing page after logout
  };

  const handleCancelLogout = () => {
    setLogoutDialogOpen(false);
  };

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          {/* Logo/Brand with link to landing page */}
          <Typography 
            variant="h6" 
            component={Link}
            to="/"
            sx={{ 
              flexGrow: 1, 
              textDecoration: 'none', 
              color: 'white',
              '&:hover': {
                opacity: 0.8
              }
            }}
          >
            FreshLense
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mr: 2 }}>
            {/* Dashboard Link */}
            <Button 
              color="inherit" 
              component={Link}
              to="/dashboard"
              variant={location.pathname === '/dashboard' ? 'outlined' : 'text'}
              sx={{ 
                border: location.pathname === '/dashboard' ? '1px solid white' : 'none',
                color: 'white'
              }}
            >
              <DashboardIcon sx={{ mr: 0.5, fontSize: 18 }} />
              Dashboard
            </Button>
            
            {/* Analytics Link - NEW */}
            <Button 
              color="inherit" 
              component={Link}
              to="/analytics"
              variant={location.pathname === '/analytics' ? 'outlined' : 'text'}
              sx={{ 
                border: location.pathname === '/analytics' ? '1px solid white' : 'none',
                color: 'white'
              }}
            >
              <AnalyticsIcon sx={{ mr: 0.5, fontSize: 18 }} />
              Analytics
            </Button>
            
            {/* Direct Fact Check Link */}
            <Button 
              color="inherit" 
              component={Link}
              to="/fact-check-direct"
              variant={location.pathname === '/fact-check-direct' ? 'outlined' : 'text'}
              sx={{ 
                border: location.pathname === '/fact-check-direct' ? '1px solid white' : 'none',
                color: 'white'
              }}
            >
              <FactCheckIcon sx={{ mr: 0.5, fontSize: 18 }} />
              Direct Fact Check
            </Button>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" sx={{ color: 'white' }}>
              Welcome, {user?.email}
            </Typography>
            <Button 
              color="inherit" 
              onClick={handleLogoutClick}
              variant="outlined"
              startIcon={<LogoutIcon />}
              sx={{ borderColor: 'white', color: 'white' }}
            >
              Logout
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Logout Confirmation Dialog */}
      <Dialog
        open={logoutDialogOpen}
        onClose={handleCancelLogout}
        aria-labelledby="logout-dialog-title"
        aria-describedby="logout-dialog-description"
        PaperProps={{
          sx: {
            borderRadius: 2,
            minWidth: 320,
          }
        }}
      >
        <DialogTitle id="logout-dialog-title" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <LogoutIcon color="error" />
          Confirm Logout
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="logout-dialog-description">
            Are you sure you want to log out? You will need to log in again to access your dashboard and monitored pages.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ padding: 2, gap: 1 }}>
          <Button 
            onClick={handleCancelLogout} 
            variant="outlined"
            sx={{ textTransform: 'none' }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleConfirmLogout} 
            variant="contained" 
            color="error"
            autoFocus
            sx={{ textTransform: 'none' }}
          >
            Logout
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default Navbar;