// frontend/src/components/Dashboard/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  Alert, 
  CircularProgress, 
  Snackbar,
  Paper,
  Card,
  CardContent,
  Button
} from '@mui/material';
import { pagesAPI, TrackedPage, crawlAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import AddPageForm from './AddPageForm';
import PageList from './PageList';

const Dashboard: React.FC = () => {
  const [pages, setPages] = useState<TrackedPage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [crawling, setCrawling] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState<Set<string>>(new Set());
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  // Get authentication state
  const { isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const fetchPages = async () => {
    try {
      const response = await pagesAPI.getAll();
      setPages(response.data);
      setError('');
    } catch (err: any) {
      console.error('Fetch pages error:', err);
      
      if (err.response?.status === 401) {
        setError('Please login again. Your session may have expired.');
        // Clear auth data and redirect
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        setError(err.response?.data?.detail || 'Failed to fetch pages');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch pages if user is authenticated and auth is done loading
    if (!authLoading && isAuthenticated) {
      fetchPages();
    } else if (!authLoading && !isAuthenticated) {
      // If not authenticated, set loading to false
      setLoading(false);
      setError('Please login to view your pages.');
    }
  }, [authLoading, isAuthenticated, navigate]);

  const handlePageAdded = (newPage: TrackedPage) => {
    setPages((prev) => [newPage, ...prev]);
    setSnackbar({
      open: true,
      message: 'Page added successfully!',
      severity: 'success',
    });
  };

  const handlePageDeleted = async (pageId: string) => {
    if (deleting.has(pageId)) return;
    
    setDeleting(prev => new Set(prev).add(pageId));
    
    try {
      await pagesAPI.delete(pageId);
      setPages((prev) => prev.filter((page) => page.id !== pageId));
      
      setSnackbar({
        open: true,
        message: 'Page deleted successfully!',
        severity: 'info',
      });
    } catch (err: any) {
      console.error('Delete page error:', err);
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Failed to delete page',
        severity: 'error',
      });
    } finally {
      setDeleting(prev => {
        const newSet = new Set(prev);
        newSet.delete(pageId);
        return newSet;
      });
    }
  };

  const handlePageUpdated = (updatedPage: TrackedPage) => {
    setPages((prev) =>
      prev.map((page) => (page.id === updatedPage.id ? updatedPage : page))
    );
  };

  const handleCrawl = async (pageId: string) => {
    if (crawling.has(pageId)) {
      return;
    }

    setCrawling(prev => new Set(prev).add(pageId));
    
    try {
      const response = await crawlAPI.crawlPage(pageId);
      const result = response.data;

      const changeStatus = result.change_detected ? 'Change detected!' : 'No changes';
      setSnackbar({
        open: true,
        message: `Crawl completed! ${changeStatus}`,
        severity: result.change_detected ? 'success' : 'info',
      });

      await fetchPages();
      
    } catch (err: any) {
      console.error('Crawl error:', err);
      const errorMessage = err.response?.data?.detail || 'Crawl failed';
      setSnackbar({
        open: true,
        message: errorMessage,
        severity: 'error',
      });
    } finally {
      setCrawling(prev => {
        const newSet = new Set(prev);
        newSet.delete(pageId);
        return newSet;
      });
    }
  };

  const closeSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  // Calculate statistics
  const activePages = pages.filter(p => p.is_active).length;
  const pagesWithChanges = pages.filter(p => p.last_change_detected).length;
  const pendingPages = pages.filter(p => !p.last_checked).length;

  // Show loading while auth is checking
  if (authLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Box textAlign="center">
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2, color: 'text.secondary' }}>
            Checking authentication...
          </Typography>
        </Box>
      </Box>
    );
  }

  // Show message if not authenticated
  if (!isAuthenticated) {
    return (
      <Box sx={{ p: 3, textAlign: 'center', mt: 8 }}>
        <Alert severity="warning" sx={{ maxWidth: 600, margin: '0 auto' }}>
          <Typography variant="h6" gutterBottom>
            Authentication Required
          </Typography>
          <Typography variant="body1">
            Please login to access the dashboard and view your monitored pages.
          </Typography>
          <Button 
            variant="contained" 
            sx={{ mt: 2 }}
            onClick={() => navigate('/login')}
          >
            Go to Login
          </Button>
        </Alert>
      </Box>
    );
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Box textAlign="center">
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2, color: 'text.secondary' }}>
            Loading your monitored pages...
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom fontWeight="bold">
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor and track changes to your web pages
        </Typography>
      </Box>

      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }} 
          onClose={() => setError('')}
        >
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      {pages.length > 0 && (
        <Box 
          sx={{ 
            display: 'flex', 
            gap: 3, 
            mb: 4, 
            flexWrap: 'wrap',
            justifyContent: { xs: 'center', sm: 'flex-start' }
          }}
        >
          <Card elevation={2} sx={{ minWidth: 150, flex: '1 1 150px' }}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Total Pages
              </Typography>
              <Typography variant="h4" component="div" color="primary.main">
                {pages.length}
              </Typography>
            </CardContent>
          </Card>
          
          <Card elevation={2} sx={{ minWidth: 150, flex: '1 1 150px' }}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Active
              </Typography>
              <Typography variant="h4" component="div" color="success.main">
                {activePages}
              </Typography>
            </CardContent>
          </Card>
          
          <Card elevation={2} sx={{ minWidth: 150, flex: '1 1 150px' }}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                With Changes
              </Typography>
              <Typography variant="h4" component="div" color="warning.main">
                {pagesWithChanges}
              </Typography>
            </CardContent>
          </Card>
          
          <Card elevation={2} sx={{ minWidth: 150, flex: '1 1 150px' }}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Pending
              </Typography>
              <Typography variant="h4" component="div" color="info.main">
                {pendingPages}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Add Page Form */}
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Add New Page to Monitor
        </Typography>
        <AddPageForm onPageAdded={handlePageAdded} />
      </Paper>

      {/* Pages List Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: { xs: 'flex-start', sm: 'center' }, 
          mb: 3,
          flexDirection: { xs: 'column', sm: 'row' },
          gap: { xs: 2, sm: 0 }
        }}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Monitored Pages
            </Typography>
            {pages.length > 0 && (
              <Typography variant="body2" color="text.secondary">
                {activePages} active • {pagesWithChanges} with changes • {pendingPages} pending
              </Typography>
            )}
          </Box>
          
          {pages.length > 0 && (
            <Typography variant="body2" color="text.secondary">
              Last updated: {new Date().toLocaleTimeString()}
            </Typography>
          )}
        </Box>

        {pages.length === 0 ? (
          <Alert severity="info">
            <Typography variant="body1" gutterBottom>
              No pages being monitored yet
            </Typography>
            <Typography variant="body2">
              Add your first page above to start monitoring web page changes and track content updates.
            </Typography>
          </Alert>
        ) : (
          <PageList
            pages={pages}
            onPageDeleted={handlePageDeleted}
            onPageUpdated={handlePageUpdated}
            onPageCrawl={handleCrawl}
            crawlingPages={crawling}
            deletingPages={deleting}
          />
        )}
      </Paper>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={closeSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          severity={snackbar.severity}
          sx={{ width: '100%' }}
          onClose={closeSnackbar}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Dashboard;