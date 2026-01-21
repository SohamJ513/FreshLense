// frontend/src/components/Layout/Navbar.tsx
import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
} from '@mui/material';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/'); // Redirect to landing page after logout
  };

  return (
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
          {/* Navigation Links */}
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
            Dashboard
          </Button>
          
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
            Direct Fact Check
          </Button>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" sx={{ color: 'white' }}>
            Welcome, {user?.email}
          </Typography>
          <Button 
            color="inherit" 
            onClick={handleLogout}
            variant="outlined"
            sx={{ borderColor: 'white', color: 'white' }}
          >
            Logout
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;