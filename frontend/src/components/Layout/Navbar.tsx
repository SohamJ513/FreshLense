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
  alpha,
  useScrollTrigger,
  Slide,
  Avatar,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  Dashboard as DashboardIcon,
  FactCheck as FactCheckIcon,
  Logout as LogoutIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
} from '@mui/icons-material';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

// Hide navbar on scroll down, show on scroll up
interface HideOnScrollProps {
  children: React.ReactElement;
}

function HideOnScroll(props: HideOnScrollProps) {
  const trigger = useScrollTrigger();
  return (
    <Slide appear={false} direction="down" in={!trigger}>
      {props.children}
    </Slide>
  );
}

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const userMenuOpen = Boolean(anchorEl);

  const handleUserMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogoutClick = () => {
    handleUserMenuClose();
    setLogoutDialogOpen(true);
  };

  const handleConfirmLogout = () => {
    setLogoutDialogOpen(false);
    logout();
    navigate('/');
  };

  const handleCancelLogout = () => {
    setLogoutDialogOpen(false);
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: <DashboardIcon sx={{ mr: 0.5, fontSize: 18 }} /> },
    { path: '/analytics', label: 'Analytics', icon: <AnalyticsIcon sx={{ mr: 0.5, fontSize: 18 }} /> },
    { path: '/fact-check-direct', label: 'Direct Fact Check', icon: <FactCheckIcon sx={{ mr: 0.5, fontSize: 18 }} /> },
  ];

  // Get user's initial for avatar
  const userInitial = user?.email ? user.email.charAt(0).toUpperCase() : 'U';

  return (
    <>
      <HideOnScroll>
        <AppBar 
          position="sticky" 
          elevation={0}
          sx={{
            bgcolor: '#1976d2',
            borderBottom: '1px solid',
            borderColor: alpha('#ffffff', 0.1),
            backdropFilter: 'blur(0px)',
          }}
        >
          <Toolbar sx={{ px: { xs: 2, sm: 3 } }}>
            {/* Logo/Brand */}
            <Typography 
              variant="h6" 
              component={Link}
              to="/"
              sx={{ 
                flexGrow: 1, 
                textDecoration: 'none', 
                color: 'white',
                fontWeight: 700,
                letterSpacing: '-0.5px',
                fontSize: '1.25rem',
                '&:hover': {
                  opacity: 0.9,
                },
                transition: 'opacity 0.2s ease',
              }}
            >
              FreshLense
            </Typography>
            
            {/* Navigation Links */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mr: 2 }}>
              {navItems.map((item) => (
                <Button 
                  key={item.path}
                  color="inherit" 
                  component={Link}
                  to={item.path}
                  variant={location.pathname === item.path ? 'contained' : 'text'}
                  startIcon={item.icon}
                  sx={{ 
                    backgroundColor: location.pathname === item.path ? alpha('#ffffff', 0.15) : 'transparent',
                    border: 'none',
                    color: 'white',
                    borderRadius: 2,
                    px: 2,
                    py: 0.75,
                    fontWeight: location.pathname === item.path ? 600 : 500,
                    '&:hover': {
                      backgroundColor: alpha('#ffffff', 0.1),
                    },
                    transition: 'all 0.2s ease',
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Box>

            {/* User Section */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Button
                onClick={handleUserMenuClick}
                sx={{
                  color: 'white',
                  textTransform: 'none',
                  borderRadius: 2,
                  px: 1.5,
                  py: 0.5,
                  '&:hover': {
                    backgroundColor: alpha('#ffffff', 0.1),
                  },
                }}
              >
                <Avatar
                  sx={{
                    width: 32,
                    height: 32,
                    bgcolor: alpha('#ffffff', 0.2),
                    color: 'white',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    mr: 1,
                  }}
                >
                  {userInitial}
                </Avatar>
                <Typography variant="body2" sx={{ fontWeight: 500, mr: 0.5 }}>
                  {user?.email?.split('@')[0]}
                </Typography>
                <KeyboardArrowDownIcon sx={{ fontSize: 18, opacity: 0.7 }} />
              </Button>
            </Box>
          </Toolbar>
        </AppBar>
      </HideOnScroll>

      {/* User Menu Dropdown */}
      <Menu
        anchorEl={anchorEl}
        open={userMenuOpen}
        onClose={handleUserMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        PaperProps={{
          elevation: 4,
          sx: {
            mt: 1,
            minWidth: 220,
            borderRadius: 2,
            overflow: 'hidden',
            border: '1px solid',
            borderColor: '#e0e0e0',
            boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
          },
        }}
      >
        <Box sx={{ px: 2, py: 1.5, bgcolor: '#fafafa' }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#1976d2' }}>
            {user?.email}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Account
          </Typography>
        </Box>
        <Divider />
        <MenuItem onClick={handleUserMenuClose} sx={{ py: 1 }}>
          <ListItemIcon>
            <PersonIcon fontSize="small" color="primary" />
          </ListItemIcon>
          <ListItemText primary="Profile" />
        </MenuItem>
        <MenuItem onClick={handleUserMenuClose} sx={{ py: 1 }}>
          <ListItemIcon>
            <SettingsIcon fontSize="small" color="primary" />
          </ListItemIcon>
          <ListItemText primary="Settings" />
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogoutClick} sx={{ py: 1, color: '#d32f2f' }}>
          <ListItemIcon>
            <LogoutIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText primary="Logout" />
        </MenuItem>
      </Menu>

      {/* Logout Confirmation Dialog - Modern Design */}
      <Dialog
        open={logoutDialogOpen}
        onClose={handleCancelLogout}
        aria-labelledby="logout-dialog-title"
        PaperProps={{
          sx: {
            borderRadius: 2,
            minWidth: 380,
            overflow: 'hidden',
          }
        }}
      >
        <Box sx={{ bgcolor: '#d32f2f', p: 2, textAlign: 'center' }}>
          <LogoutIcon sx={{ fontSize: 48, color: 'white', mb: 1 }} />
          <DialogTitle id="logout-dialog-title" sx={{ p: 0, color: 'white', fontWeight: 'bold' }}>
            Confirm Logout
          </DialogTitle>
        </Box>
        <DialogContent sx={{ pt: 3, pb: 2 }}>
          <DialogContentText textAlign="center">
            Are you sure you want to log out? You will need to log in again to access your dashboard and monitored pages.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 3, gap: 2, justifyContent: 'center' }}>
          <Button 
            onClick={handleCancelLogout} 
            variant="outlined"
            sx={{ 
              textTransform: 'none',
              borderRadius: 2,
              px: 3,
              borderColor: '#e0e0e0',
              color: '#757575',
              '&:hover': {
                borderColor: '#1976d2',
                backgroundColor: alpha('#1976d2', 0.02),
              },
            }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleConfirmLogout} 
            variant="contained" 
            color="error"
            sx={{ 
              textTransform: 'none',
              borderRadius: 2,
              px: 3,
              '&:hover': {
                backgroundColor: '#c62828',
                transform: 'translateY(-1px)',
                boxShadow: '0 4px 12px rgba(211, 47, 47, 0.3)',
              },
              transition: 'all 0.2s ease',
            }}
          >
            Logout
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default Navbar;