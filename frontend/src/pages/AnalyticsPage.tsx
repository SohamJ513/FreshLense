// frontend/src/pages/AnalyticsPage.tsx
import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Alert,
  Skeleton,
  Chip,
  Button,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  TextField,
  MenuItem,
  InputAdornment,
  Badge,
  Tooltip,
  LinearProgress,
  Tab,
  Tabs
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  ContentCopy as CopyIcon,
  CheckCircle as CheckCircleIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Timeline as TimelineIcon,
  NotificationsActive as AlertIcon,
  Web as WebIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { formatDistance } from 'date-fns';
import { analyticsApi } from '../services/analyticsApi';
import { PageHealth, ChangeFrequencyData, FactAlert, CrawlFailure } from '../types/analytics';

export const AnalyticsPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pageHealth, setPageHealth] = useState<PageHealth[]>([]);
  const [changeFrequency, setChangeFrequency] = useState<ChangeFrequencyData[]>([]);
  const [alerts, setAlerts] = useState<FactAlert[]>([]);
  const [failedCrawls, setFailedCrawls] = useState<CrawlFailure[]>([]);
  
  // UI state
  const [alertFilter, setAlertFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTab, setSelectedTab] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  
  // Abort controller to cancel duplicate requests
  const abortControllerRef = useRef<AbortController | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Define fetchAnalyticsData with useCallback to prevent recreation
  const fetchAnalyticsData = useCallback(async (isRetry = false) => {
    try {
      setLoading(true);
      setError(null); // Clear any previous errors
      
      const signal = abortControllerRef.current?.signal;
      
      const [healthRes, frequencyRes, alertsRes, failuresRes] = await Promise.all([
        analyticsApi.getPageHealthScores(signal),
        analyticsApi.getChangeFrequency(30, signal),
        analyticsApi.getFactAlerts(50, signal),
        analyticsApi.getFailedCrawls(signal)
      ]);
      
      // Log the responses for debugging
      console.log('✅ Health data:', healthRes);
      console.log('✅ Frequency data:', frequencyRes);
      console.log('✅ Alerts data:', alertsRes);
      console.log('✅ Failures data:', failuresRes);
      
      let hasData = false;
      
      if (healthRes?.success) {
        setPageHealth(healthRes.data || []);
        if (healthRes.data?.length > 0) hasData = true;
      }
      if (frequencyRes?.success) {
        setChangeFrequency(frequencyRes.data || []);
        if (frequencyRes.data?.length > 0) hasData = true;
      }
      if (alertsRes?.success) setAlerts(alertsRes.data || []);
      if (failuresRes?.success) setFailedCrawls(failuresRes.data || []);
      
      // If this was a retry and we got data, reset retry count
      if (hasData) {
        setRetryCount(0);
      }
      
    } catch (err: any) {
      // Don't show error if request was aborted
      if (err.name === 'CanceledError' || 
          err.code === 'ERR_CANCELED' || 
          err.message?.includes('aborted') ||
          err.message?.includes('canceled')) {
        console.log('Request was cancelled');
        return;
      }
      
      // Handle timeout errors with retry
      if (err.message?.includes('timeout') || err.code === 'ECONNABORTED') {
        console.log(`Request timed out (attempt ${retryCount + 1}/3)`);
        
        if (retryCount < 2) { // Retry up to 2 times (total 3 attempts)
          setRetryCount(prev => prev + 1);
          
          // Clear any existing retry timeout
          if (retryTimeoutRef.current) {
            clearTimeout(retryTimeoutRef.current);
          }
          
          // Retry after 1 second
          retryTimeoutRef.current = setTimeout(() => {
            if (abortControllerRef.current) {
              // Create new abort controller for retry
              abortControllerRef.current.abort();
              abortControllerRef.current = new AbortController();
            }
            fetchAnalyticsData(true);
          }, 1000);
          
          return;
        } else {
          setError('Request timed out. Please click Refresh to try again.');
        }
      } else {
        console.error('❌ Analytics error:', err);
        setError('Failed to load analytics data');
      }
    } finally {
      setLoading(false);
    }
  }, [retryCount]);

  useEffect(() => {
    // Cancel previous requests if component re-renders
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Clear any pending retry timeouts
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }
    
    // Create new abort controller
    abortControllerRef.current = new AbortController();
    
    fetchAnalyticsData();
    
    // Cleanup on unmount
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [fetchAnalyticsData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null); // Clear any previous errors
    setRetryCount(0); // Reset retry count
    
    // Cancel any ongoing requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Clear any pending retry timeouts
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }
    
    // Create new abort controller
    abortControllerRef.current = new AbortController();
    
    await fetchAnalyticsData();
    setRefreshing(false);
  };

  const handleMarkAlertRead = async (alertId: string) => {
    try {
      await analyticsApi.markAlertAsRead(alertId);
      setAlerts(prev => 
        prev.map(alert => 
          alert.id === alertId ? { ...alert, read: true } : alert
        )
      );
    } catch (error) {
      console.error('Failed to mark alert as read:', error);
    }
  };

  const handleViewPage = (pageId: string) => {
    navigate(`/pages/${pageId}`);
  };

  const handleManualPaste = (pageId: string) => {
    navigate(`/manual-paste/${pageId}`);
  };

  // Helper functions
  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircleIcon sx={{ color: '#4caf50' }} />;
      case 'warning': return <WarningIcon sx={{ color: '#ff9800' }} />;
      case 'critical': return <ErrorIcon sx={{ color: '#f44336' }} />;
      default: return <InfoIcon sx={{ color: '#9e9e9e' }} />;
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical': return <ErrorIcon sx={{ color: '#f44336' }} />;
      case 'warning': return <WarningIcon sx={{ color: '#ff9800' }} />;
      default: return <InfoIcon sx={{ color: '#2196f3' }} />;
    }
  };

  const unreadAlertsCount = alerts.filter(a => !a.read).length;
  const criticalAlertsCount = alerts.filter(a => a.type === 'critical' && !a.read).length;

  // Filter alerts
  const filteredAlerts = alerts.filter(alert => {
    if (alertFilter !== 'all' && alert.type !== alertFilter) return false;
    if (searchTerm && !alert.pageTitle.toLowerCase().includes(searchTerm.toLowerCase()) && 
        !alert.message.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert 
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={handleRefresh}>
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Analytics Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor page health, track changes, and review critical alerts
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={loading || refreshing}
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </Button>
      </Box>

      {/* Stats Cards */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
        {/* Total Pages Card */}
        <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
          <Paper sx={{ p: 3, bgcolor: '#f5f5f5' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="body2" color="text.secondary">Total Pages</Typography>
                <Typography variant="h4">{loading ? '...' : pageHealth.length}</Typography>
              </Box>
              <WebIcon sx={{ fontSize: 40, color: '#1976d2', opacity: 0.7 }} />
            </Box>
          </Paper>
        </Box>
        
        {/* Critical Pages Card */}
        <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
          <Paper sx={{ p: 3, bgcolor: '#f5f5f5' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="body2" color="text.secondary">Critical Pages</Typography>
                <Typography variant="h4" color="error">
                  {loading ? '...' : pageHealth.filter(p => p.healthStatus === 'critical').length}
                </Typography>
              </Box>
              <ErrorIcon sx={{ fontSize: 40, color: '#f44336', opacity: 0.7 }} />
            </Box>
          </Paper>
        </Box>
        
        {/* Unread Alerts Card */}
        <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
          <Paper sx={{ p: 3, bgcolor: '#f5f5f5' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="body2" color="text.secondary">Unread Alerts</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="h4">{loading ? '...' : unreadAlertsCount}</Typography>
                  {criticalAlertsCount > 0 && (
                    <Chip 
                      label={`${criticalAlertsCount} critical`} 
                      color="error" 
                      size="small" 
                      sx={{ ml: 1 }}
                    />
                  )}
                </Box>
              </Box>
              <Badge badgeContent={criticalAlertsCount} color="error">
                <AlertIcon sx={{ fontSize: 40, color: '#ff9800', opacity: 0.7 }} />
              </Badge>
            </Box>
          </Paper>
        </Box>
        
        {/* Failed Crawls Card */}
        <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
          <Paper sx={{ p: 3, bgcolor: '#f5f5f5' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="body2" color="text.secondary">Failed Crawls</Typography>
                <Typography variant="h4" color="warning.main">
                  {loading ? '...' : failedCrawls.length}
                </Typography>
              </Box>
              <WarningIcon sx={{ fontSize: 40, color: '#ff9800', opacity: 0.7 }} />
            </Box>
          </Paper>
        </Box>
      </Box>

      {/* Loading Progress Bar */}
      {loading && (
        <Box sx={{ width: '100%', mb: 2 }}>
          <LinearProgress />
          <Typography variant="caption" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
            {retryCount > 0 ? `Retrying... (Attempt ${retryCount + 1}/3)` : 'Loading analytics data...'}
          </Typography>
        </Box>
      )}

      {/* Failed Crawls Banner */}
      {!loading && failedCrawls.length > 0 && (
        <Paper sx={{ p: 2, mb: 4, bgcolor: '#fff3e0', border: '1px solid #ffb74d' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <WarningIcon sx={{ color: '#f57c00' }} />
            <Typography variant="subtitle1" fontWeight="bold">
              {failedCrawls.length} page{failedCrawls.length > 1 ? 's' : ''} need manual review:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', flex: 1 }}>
              {failedCrawls.slice(0, 5).map((failure) => (
                <Chip
                  key={failure.pageId}
                  label={failure.pageTitle || failure.pageUrl}
                  onClick={() => handleManualPaste(failure.pageId)}
                  onDelete={() => handleManualPaste(failure.pageId)}
                  deleteIcon={<CopyIcon />}
                  color="warning"
                  variant="filled"
                  size="medium"
                />
              ))}
              {failedCrawls.length > 5 && (
                <Chip
                  label={`+${failedCrawls.length - 5} more`}
                  variant="outlined"
                  color="warning"
                />
              )}
            </Box>
          </Box>
        </Paper>
      )}

      {/* Change Frequency Graph */}
      <Box sx={{ mb: 4 }}>
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <TimelineIcon sx={{ mr: 1, color: '#1976d2' }} />
            <Typography variant="h6">Page Change Frequency (Last 30 Days)</Typography>
          </Box>
          
          {loading ? (
            <Skeleton variant="rectangular" height={300} />
          ) : changeFrequency.length === 0 ? (
            <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography color="text.secondary">No change data available</Typography>
            </Box>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={changeFrequency}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <RechartsTooltip 
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="subtitle2">{label}</Typography>
                          <Typography variant="body2">
                            Total Changes: {data.count}
                          </Typography>
                          <Typography variant="body2" color="error">
                            Significant: {data.significantCount}
                          </Typography>
                          {data.pages && data.pages.length > 0 && (
                            <>
                              <Divider sx={{ my: 1 }} />
                              <Typography variant="caption" display="block" fontWeight="bold">
                                Pages updated:
                              </Typography>
                              {data.pages.slice(0, 3).map((p: any, i: number) => (
                                <Typography key={i} variant="caption" display="block">
                                  • {p.pageTitle} ({p.changeCount} changes)
                                </Typography>
                              ))}
                            </>
                          )}
                        </Paper>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="count" fill="#8884d8" name="Total Changes">
                  {changeFrequency.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`}
                      fill={entry.significantCount > 0 ? '#f44336' : '#4caf50'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Paper>
      </Box>

      {/* Main Content Tabs */}
      <Paper sx={{ width: '100%', mb: 4 }}>
        <Tabs value={selectedTab} onChange={(_, v) => setSelectedTab(v)}>
          <Tab label="Page Health Scores" />
          <Tab 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                Fact-Check Alerts
                {unreadAlertsCount > 0 && (
                  <Chip 
                    label={unreadAlertsCount} 
                    size="small" 
                    color="error" 
                    sx={{ ml: 1, height: 20 }}
                  />
                )}
              </Box>
            } 
          />
        </Tabs>
      </Paper>

      {/* Tab 1: Page Health Scores */}
      {selectedTab === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Page Health Scores
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Average confidence level for each monitored page
          </Typography>

          {loading ? (
            <Skeleton variant="rectangular" height={400} />
          ) : pageHealth.length === 0 ? (
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">No pages found</Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Page</TableCell>
                    <TableCell>Health Score</TableCell>
                    <TableCell>Avg Confidence</TableCell>
                    <TableCell>Versions</TableCell>
                    <TableCell>Significant Changes</TableCell>
                    <TableCell>Last Checked</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {pageHealth.map((page) => (
                    <TableRow key={page.pageId} hover>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {page.pageTitle}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {page.pageUrl}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {getHealthIcon(page.healthStatus)}
                          <Box sx={{ ml: 1, width: 100 }}>
                            <LinearProgress 
                              variant="determinate" 
                              value={page.healthScore} 
                              color={
                                page.healthStatus === 'healthy' ? 'success' :
                                page.healthStatus === 'warning' ? 'warning' : 'error'
                              }
                              sx={{ height: 8, borderRadius: 4 }}
                            />
                          </Box>
                          <Typography variant="body2" sx={{ ml: 1, minWidth: 40 }}>
                            {page.healthScore}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={`${page.avgConfidence.toFixed(1)}%`}
                          size="small"
                          color={page.avgConfidence >= 80 ? 'success' : page.avgConfidence >= 60 ? 'warning' : 'error'}
                        />
                      </TableCell>
                      <TableCell>{page.totalVersions}</TableCell>
                      <TableCell>
                        {page.significantChanges > 0 ? (
                          <Chip 
                            label={page.significantChanges}
                            size="small"
                            color="warning"
                            icon={<WarningIcon />}
                          />
                        ) : (
                          page.significantChanges
                        )}
                      </TableCell>
                      <TableCell>
                        {page.lastChecked ? (
                          <Tooltip title={new Date(page.lastChecked).toLocaleString()}>
                            <span>{formatDistance(new Date(page.lastChecked), new Date(), { addSuffix: true })}</span>
                          </Tooltip>
                        ) : 'Never'}
                      </TableCell>
                      <TableCell>
                        <IconButton size="small" onClick={() => handleViewPage(page.pageId)}>
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}

      {/* Tab 2: Fact-Check Alerts */}
      {selectedTab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Recent Fact-Check Alerts
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                size="small"
                placeholder="Search alerts..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  )
                }}
              />
              
              <TextField
                select
                size="small"
                value={alertFilter}
                onChange={(e) => setAlertFilter(e.target.value)}
                sx={{ width: 150 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <FilterIcon fontSize="small" />
                    </InputAdornment>
                  )
                }}
              >
                <MenuItem value="all">All Alerts</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
                <MenuItem value="warning">Warning</MenuItem>
                <MenuItem value="info">Info</MenuItem>
              </TextField>
            </Box>
          </Box>

          {loading ? (
            <Skeleton variant="rectangular" height={400} />
          ) : filteredAlerts.length === 0 ? (
            <Box sx={{ py: 8, textAlign: 'center' }}>
              <AlertIcon sx={{ fontSize: 48, color: '#9e9e9e', mb: 2 }} />
              <Typography color="text.secondary">No alerts found</Typography>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {filteredAlerts.map((alert) => (
                <Paper
                  key={alert.id}
                  variant="outlined"
                  sx={{
                    p: 2,
                    bgcolor: alert.read ? 'transparent' : 
                             alert.type === 'critical' ? '#ffebee' :
                             alert.type === 'warning' ? '#fff3e0' : '#e3f2fd'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                    <Box sx={{ mt: 0.5 }}>
                      {getAlertIcon(alert.type)}
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5, flexWrap: 'wrap' }}>
                        <Typography variant="subtitle2">
                          {alert.pageTitle}
                        </Typography>
                        {!alert.read && (
                          <Chip label="New" size="small" color="primary" />
                        )}
                        {alert.type === 'critical' && (
                          <Chip label="Critical" size="small" color="error" />
                        )}
                      </Box>
                      <Typography variant="body2" sx={{ mb: 0.5 }}>
                        {alert.message}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                        <Typography variant="caption" color="text.secondary">
                          {formatDistance(new Date(alert.timestamp), new Date(), { addSuffix: true })}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Confidence: {alert.confidence.toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleViewPage(alert.pageId)}
                      >
                        View
                      </Button>
                      {!alert.read && (
                        <Button
                          size="small"
                          onClick={() => handleMarkAlertRead(alert.id)}
                        >
                          Dismiss
                        </Button>
                      )}
                    </Box>
                  </Box>
                </Paper>
              ))}
            </Box>
          )}
        </Paper>
      )}
    </Container>
  );
};