// frontend/src/components/Dashboard/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  Alert, 
  CircularProgress, 
  Snackbar,
  Paper,
  Button,
  Fade,
  Zoom,
  alpha,
  Card,
  CardContent,
} from '@mui/material';
import {
  Add as AddIcon,
  Schedule as ScheduleIcon,
  Dashboard as DashboardIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon,
  FactCheck as FactCheckIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { pagesAPI, TrackedPage, crawlAPI, UpdatedPageResponse } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import AddPageForm from './AddPageForm';
import PageList from './PageList';

// Quick Action Card Component - Fixed height
const QuickActionCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
  onClick: () => void;
  delay?: number;
}> = ({ icon, title, description, color, onClick, delay = 0 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      whileHover={{ y: -5, transition: { duration: 0.2 } }}
      style={{ height: '100%', flex: 1, minWidth: 200 }}
    >
      <Card
        elevation={0}
        sx={{
          height: '100%',
          cursor: 'pointer',
          borderRadius: 2,
          border: '1px solid',
          borderColor: '#e0e0e0',
          transition: 'all 0.3s ease',
          display: 'flex',
          flexDirection: 'column',
          '&:hover': {
            boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
            '& .action-icon': {
              transform: 'scale(1.1)',
              backgroundColor: alpha(color, 0.15),
            },
          },
        }}
        onClick={onClick}
      >
        <CardContent sx={{ p: 3, textAlign: 'center', flex: 1, display: 'flex', flexDirection: 'column' }}>
          <Box
            className="action-icon"
            sx={{
              width: 56,
              height: 56,
              borderRadius: 2,
              backgroundColor: alpha(color, 0.1),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
              transition: 'all 0.3s ease',
              color: color,
            }}
          >
            {icon}
          </Box>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 1 }}>
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ 
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
          }}>
            {description}
          </Typography>
        </CardContent>
      </Card>
    </motion.div>
  );
};

const Dashboard: React.FC = () => {
  const [pages, setPages] = useState<TrackedPage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [crawling, setCrawling] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState<Set<string>>(new Set());
  const [showAddForm, setShowAddForm] = useState(false);
  const [checkingAllPages, setCheckingAllPages] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

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
    if (!authLoading && isAuthenticated) {
      fetchPages();
    } else if (!authLoading && !isAuthenticated) {
      setLoading(false);
      setError('Please login to view your pages.');
    }
  }, [authLoading, isAuthenticated, navigate]);

  const handlePageAdded = (newPage: TrackedPage) => {
    setPages((prev) => [newPage, ...prev]);
    setShowAddForm(false);
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

  const handlePageUpdated = (updatedPage: TrackedPage | UpdatedPageResponse) => {
    const convertedPage: TrackedPage = 'check_interval_hours' in updatedPage 
      ? {
          id: updatedPage.id,
          user_id: '',
          url: updatedPage.url,
          display_name: updatedPage.display_name,
          check_interval_minutes: updatedPage.check_interval_hours * 60,
          is_active: updatedPage.status === 'active',
          created_at: updatedPage.created_at,
          last_checked: updatedPage.last_checked,
          last_change_detected: updatedPage.last_change_detected,
          current_version_id: updatedPage.current_version_id,
        }
      : updatedPage;
    
    setPages((prev) =>
      prev.map((page) => {
        if (page.id === convertedPage.id) {
          return {
            ...page,
            display_name: convertedPage.display_name,
            check_interval_minutes: convertedPage.check_interval_minutes,
            last_checked: convertedPage.last_checked || page.last_checked,
            last_change_detected: convertedPage.last_change_detected || page.last_change_detected,
            current_version_id: convertedPage.current_version_id || page.current_version_id,
          };
        }
        return page;
      })
    );
    
    setSnackbar({
      open: true,
      message: 'Page updated successfully!',
      severity: 'success',
    });
  };

  const handleCrawl = async (pageId: string) => {
    if (crawling.has(pageId)) return;

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

  const handleCheckAllPages = async () => {
    if (checkingAllPages || pages.length === 0) return;
    
    setCheckingAllPages(true);
    let successCount = 0;
    let changeCount = 0;
    
    setSnackbar({
      open: true,
      message: `Checking ${pages.length} pages...`,
      severity: 'info',
    });
    
    for (const page of pages) {
      if (page.is_active) {
        try {
          const response = await crawlAPI.crawlPage(page.id);
          if (response.data.change_detected) {
            changeCount++;
          }
          successCount++;
        } catch (err) {
          console.error(`Failed to check ${page.url}:`, err);
        }
      }
    }
    
    await fetchPages();
    
    setSnackbar({
      open: true,
      message: `Checked ${successCount} pages. ${changeCount} changes detected!`,
      severity: changeCount > 0 ? 'success' : 'info',
    });
    setCheckingAllPages(false);
  };

  const closeSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const activePages = pages.filter(p => p.is_active).length;
  const pagesWithChanges = pages.filter(p => p.last_change_detected).length;
  const pendingPages = pages.filter(p => !p.last_checked).length;

  if (authLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <Fade in timeout={1000}>
          <Box textAlign="center">
            <CircularProgress size={60} thickness={4} sx={{ color: '#1976d2' }} />
            <Typography variant="h6" sx={{ mt: 3, color: 'text.secondary', fontWeight: 500 }}>
              Loading your dashboard...
            </Typography>
          </Box>
        </Fade>
      </Box>
    );
  }

  if (!isAuthenticated) {
    return (
      <Fade in>
        <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#1976d2' }}>
          <Paper elevation={0} sx={{ p: 6, maxWidth: 500, textAlign: 'center', borderRadius: 2 }}>
            <SecurityIcon sx={{ fontSize: 80, color: '#1976d2', mb: 2 }} />
            <Typography variant="h5" gutterBottom fontWeight="bold">
              Authentication Required
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Please login to access your dashboard and monitor your web pages.
            </Typography>
            <Button 
              variant="contained" 
              size="large"
              onClick={() => navigate('/login')}
              sx={{ 
                background: '#1976d2',
                px: 4,
                '&:hover': {
                  background: '#1565c0',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 10px 20px rgba(25, 118, 210, 0.3)',
                },
                transition: 'all 0.3s ease',
              }}
            >
              Go to Login
            </Button>
          </Paper>
        </Box>
      </Fade>
    );
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" sx={{ bgcolor: '#f5f5f5' }}>
        <Fade in timeout={1000}>
          <Box textAlign="center">
            <CircularProgress size={60} thickness={4} sx={{ color: '#1976d2' }} />
            <Typography variant="h6" sx={{ mt: 3, color: 'text.secondary', fontWeight: 500 }}>
              Loading your monitored pages...
            </Typography>
          </Box>
        </Fade>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f5f5f5' }}>
      {/* Hero Section */}
      <Box
        sx={{
          background: '#1976d2',
          color: 'white',
          pt: 4,
          pb: 4,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Box sx={{ maxWidth: 1200, mx: 'auto', px: 3, position: 'relative', zIndex: 1 }}>
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <Typography variant="h4" gutterBottom fontWeight="bold" sx={{ fontSize: { xs: '1.75rem', md: '2rem' } }}>
              Dashboard
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
              Monitor and track changes to your web pages in real-time
            </Typography>
          </motion.div>
        </Box>
      </Box>

      {/* Main Content */}
      <Box sx={{ maxWidth: 1200, mx: 'auto', px: 3, mt: 4 }}>
        {error && (
          <Fade in>
            <Alert 
              severity="error" 
              sx={{ mb: 3, borderRadius: 2 }}
              onClose={() => setError('')}
            >
              {error}
            </Alert>
          </Fade>
        )}

        {/* Add New Page Section */}
        <Fade in timeout={800}>
          <Paper
            elevation={0}
            sx={{
              mb: 4,
              borderRadius: 2,
              overflow: 'visible',
              border: '1px solid',
              borderColor: '#e0e0e0',
              bgcolor: 'white',
            }}
          >
            <Box
              sx={{
                p: 3,
                bgcolor: '#fafafa',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexDirection: { xs: 'column', sm: 'row' },
                gap: 3,
              }}
            >
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <AddIcon sx={{ color: '#1976d2' }} />
                  Add New Page to Monitor
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Start tracking any web page for content changes
                </Typography>
              </Box>
              {!showAddForm && (
                <Button
                  variant="contained"
                  onClick={() => setShowAddForm(true)}
                  startIcon={<AddIcon />}
                  sx={{
                    background: '#1976d2',
                    borderRadius: 2,
                    px: 4,
                    py: 1,
                    minWidth: 130,
                    whiteSpace: 'nowrap',
                    '&:hover': {
                      background: '#1565c0',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 10px 20px rgba(25, 118, 210, 0.3)',
                    },
                    transition: 'all 0.3s ease',
                  }}
                >
                  Add Page
                </Button>
              )}
            </Box>
            <AnimatePresence>
              {showAddForm && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <Box sx={{ p: 3, borderTop: '1px solid', borderColor: '#e0e0e0', bgcolor: 'white' }}>
                    <AddPageForm onPageAdded={handlePageAdded} onCancel={() => setShowAddForm(false)} />
                  </Box>
                </motion.div>
              )}
            </AnimatePresence>
          </Paper>
        </Fade>

        {/* Summary Stats Row */}
        {pages.length > 0 && (
          <Box sx={{ 
            display: 'flex', 
            gap: 3, 
            mb: 4, 
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'center',
            p: 3,
            bgcolor: 'white',
            borderRadius: 2,
            border: '1px solid',
            borderColor: '#e0e0e0',
          }}>
            <Box sx={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              <Box sx={{ minWidth: '90px' }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  Total Pages
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="#1976d2">{pages.length}</Typography>
              </Box>
              <Box sx={{ minWidth: '90px' }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  Active
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="#2e7d32">{activePages}</Typography>
              </Box>
              <Box sx={{ minWidth: '90px' }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  Changes
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="#ed6c02">{pagesWithChanges}</Typography>
              </Box>
              <Box sx={{ minWidth: '90px' }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  Pending
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="#9c27b0">{pendingPages}</Typography>
              </Box>
            </Box>
            <Button
              size="small"
              startIcon={<RefreshIcon />}
              onClick={fetchPages}
              sx={{ color: '#757575' }}
            >
              Refresh
            </Button>
          </Box>
        )}

        {/* Quick Actions Panel - Equal height cards */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2.5, color: '#424242' }}>
            Quick Actions
          </Typography>
          <Box sx={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: 3,
            alignItems: 'stretch',
            '& > *': {
              flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 12px)', md: '1 1 calc(33.33% - 16px)' },
              minWidth: 200,
            }
          }}>
            <QuickActionCard
              icon={<FactCheckIcon sx={{ fontSize: 28 }} />}
              title="Direct Fact Check"
              description="Verify content without crawling"
              color="#2e7d32"
              onClick={() => navigate('/fact-check-direct')}
              delay={0.1}
            />
            <QuickActionCard
              icon={checkingAllPages ? <CircularProgress size={24} /> : <PlayArrowIcon sx={{ fontSize: 28 }} />}
              title="Check All Pages"
              description={`Check all ${pages.length} monitored pages`}
              color="#ed6c02"
              onClick={handleCheckAllPages}
              delay={0.2}
            />
            <QuickActionCard
              icon={<ScheduleIcon sx={{ fontSize: 28 }} />}
              title="View Analytics"
              description="See detailed trends & history"
              color="#1976d2"
              onClick={() => navigate('/analytics')}
              delay={0.3}
            />
          </Box>
        </Box>

        {/* Pages List Section */}
        <Fade in timeout={1000}>
          <Paper
            elevation={0}
            sx={{
              borderRadius: 2,
              overflow: 'hidden',
              border: '1px solid',
              borderColor: '#e0e0e0',
              bgcolor: 'white',
            }}
          >
            <Box
              sx={{
                p: 3,
                bgcolor: '#fafafa',
                borderBottom: '1px solid',
                borderColor: '#e0e0e0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: { xs: 'flex-start', sm: 'center' },
                flexDirection: { xs: 'column', sm: 'row' },
                gap: { xs: 2, sm: 0 },
              }}
            >
              <Box>
                <Typography variant="h6" fontWeight="bold">
                  Monitored Pages
                </Typography>
                {pages.length > 0 && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    {activePages} active • {pagesWithChanges} with changes • {pendingPages} pending
                  </Typography>
                )}
              </Box>
              
              {pages.length > 0 && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <RefreshIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                  <Typography variant="caption" color="text.secondary">
                    Last updated: {new Date().toLocaleTimeString()}
                  </Typography>
                </Box>
              )}
            </Box>

            {pages.length === 0 ? (
              <Box sx={{ p: 8, textAlign: 'center' }}>
                <Zoom in>
                  <Box>
                    <DashboardIcon sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="h6" gutterBottom color="text.secondary">
                      No pages being monitored yet
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                      Start by adding your first page to track content changes
                    </Typography>
                    <Button
                      variant="contained"
                      onClick={() => setShowAddForm(true)}
                      startIcon={<AddIcon />}
                      sx={{
                        background: '#1976d2',
                        borderRadius: 2,
                        '&:hover': {
                          background: '#1565c0',
                        },
                      }}
                    >
                      Add Your First Page
                    </Button>
                  </Box>
                </Zoom>
              </Box>
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
        </Fade>
      </Box>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={closeSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          severity={snackbar.severity}
          sx={{ 
            width: '100%',
            borderRadius: 2,
            boxShadow: '0 10px 20px rgba(0,0,0,0.1)',
          }}
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