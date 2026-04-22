// frontend/src/components/Dashboard/PageList.tsx
import React, { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Button,
  Chip,
  Tooltip,
  CircularProgress,
  Typography,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  alpha,
  Zoom,
  Fade,
} from "@mui/material";
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  FactCheck as FactCheckIcon,
  TrendingUp as TrendingUpIcon,
  Link as LinkIcon,
} from "@mui/icons-material";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { TrackedPage, updatePage, PageUpdateData, UpdatedPageResponse } from "../../services/api";

interface PageListProps {
  pages: TrackedPage[];
  onPageDeleted: (pageId: string) => void;
  onPageUpdated: (updatedPage: TrackedPage) => void;
  onPageCrawl: (pageId: string) => Promise<void>;
  crawlingPages: Set<string>;
  deletingPages?: Set<string>;
}

const PageList: React.FC<PageListProps> = ({
  pages,
  onPageDeleted,
  onPageUpdated,
  onPageCrawl,
  crawlingPages,
  deletingPages = new Set(),
}) => {
  const navigate = useNavigate();
  const [editingPage, setEditingPage] = useState<TrackedPage | null>(null);
  const [editFormData, setEditFormData] = useState<PageUpdateData>({
    display_name: "",
    check_interval_hours: 24,
  });
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: '2-digit'
    });
  };

  const formatTimeAgo = (dateString: string | null): string => {
    if (!dateString) return 'Never';
    
    const now = new Date();
    const date = new Date(dateString);
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  const getStatusChip = (page: TrackedPage) => {
    if (!page.is_active) {
      return (
        <Chip 
          label="Inactive" 
          size="small" 
          icon={<WarningIcon />}
          sx={{ 
            height: 28, 
            fontSize: '0.75rem',
            fontWeight: 600,
            bgcolor: alpha('#9e9e9e', 0.1),
            color: '#9e9e9e',
            '& .MuiChip-icon': { fontSize: 14, color: '#9e9e9e' }
          }}
        />
      );
    }
    
    if (page.last_change_detected) {
      return (
        <Tooltip title={`Last change: ${formatDate(page.last_change_detected)}`}>
          <Chip 
            label="Changes Detected" 
            size="small" 
            icon={<TrendingUpIcon />}
            sx={{ 
              height: 28, 
              fontSize: '0.75rem',
              fontWeight: 600,
              bgcolor: alpha('#2e7d32', 0.1),
              color: '#2e7d32',
              '& .MuiChip-icon': { fontSize: 14, color: '#2e7d32' }
            }}
          />
        </Tooltip>
      );
    }
    
    if (page.last_checked) {
      return (
        <Chip 
          label="Active" 
          size="small" 
          icon={<CheckCircleIcon />}
          sx={{ 
            height: 28, 
            fontSize: '0.75rem',
            fontWeight: 600,
            bgcolor: alpha('#1976d2', 0.1),
            color: '#1976d2',
            '& .MuiChip-icon': { fontSize: 14, color: '#1976d2' }
          }}
        />
      );
    }
    
    return (
      <Chip 
        label="Pending" 
        size="small" 
        icon={<ScheduleIcon />}
        sx={{ 
          height: 28, 
          fontSize: '0.75rem',
          fontWeight: 600,
          bgcolor: alpha('#ed6c02', 0.1),
          color: '#ed6c02',
          '& .MuiChip-icon': { fontSize: 14, color: '#ed6c02' }
        }}
      />
    );
  };

  const hasVersionsForFactCheck = (page: TrackedPage): boolean => {
    return !!page.current_version_id;
  };

  const handleEditClick = (page: TrackedPage) => {
    setEditingPage(page);
    setEditFormData({
      display_name: page.display_name || "",
      check_interval_hours: Math.round(page.check_interval_minutes / 60),
    });
    setEditError(null);
  };

  const handleEditSubmit = async () => {
    if (!editingPage) return;

    setEditLoading(true);
    setEditError(null);

    try {
      const updatedPageResponse: UpdatedPageResponse = await updatePage(editingPage.id, editFormData);
      
      const updatedPage: TrackedPage = {
        id: updatedPageResponse.id,
        user_id: editingPage.user_id,
        url: updatedPageResponse.url,
        display_name: updatedPageResponse.display_name,
        check_interval_minutes: updatedPageResponse.check_interval_hours * 60,
        is_active: updatedPageResponse.status === 'active',
        created_at: updatedPageResponse.created_at,
        last_checked: updatedPageResponse.last_checked,
        last_change_detected: updatedPageResponse.last_change_detected,
        current_version_id: updatedPageResponse.current_version_id,
      };
      
      onPageUpdated(updatedPage);
      setEditingPage(null);
    } catch (err: any) {
      setEditError(err.response?.data?.detail || 'Failed to update page');
    } finally {
      setEditLoading(false);
    }
  };

  const intervalOptions = [
    { value: 1, label: '1 hour', icon: '⚡' },
    { value: 6, label: '6 hours', icon: '🕐' },
    { value: 12, label: '12 hours', icon: '🕛' },
    { value: 24, label: '24 hours', icon: '📅' },
    { value: 72, label: '3 days', icon: '📆' },
    { value: 168, label: '1 week', icon: '🗓️' },
  ];

  const getShortUrl = (url: string): string => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname.replace('www.', '');
    } catch {
      return url.length > 35 ? url.substring(0, 32) + '...' : url;
    }
  };

  const getUrlPath = (url: string): string => {
    try {
      const urlObj = new URL(url);
      return urlObj.pathname + urlObj.search;
    } catch {
      return '';
    }
  };

  if (pages.length === 0) {
    return (
      <Fade in>
        <Box sx={{ p: 6, textAlign: 'center' }}>
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <Box sx={{ mb: 2 }}>
              <ScheduleIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            </Box>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No pages being monitored
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Add your first page to get started with monitoring!
            </Typography>
          </motion.div>
        </Box>
      </Fade>
    );
  }

  return (
    <>
      <TableContainer 
        component={Paper} 
        elevation={0}
        sx={{ 
          width: '100%',
          overflowX: 'auto',
          borderRadius: 0,
          '& .MuiTable-root': {
            minWidth: 900,
          },
        }}
      >
        <Table>
          <TableHead>
            <TableRow sx={{ bgcolor: '#fafafa' }}>
              <TableCell 
                sx={{ 
                  width: '18%', 
                  py: 2,
                  px: 3,
                  fontWeight: 700,
                  fontSize: '0.8125rem',
                  color: '#1976d2',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  borderBottom: '2px solid',
                  borderColor: '#e0e0e0',
                  whiteSpace: 'nowrap',
                }}
              >
                URL
              </TableCell>
              <TableCell 
                sx={{ 
                  width: '15%', 
                  py: 2,
                  px: 3,
                  fontWeight: 700,
                  fontSize: '0.8125rem',
                  color: '#1976d2',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  borderBottom: '2px solid',
                  borderColor: '#e0e0e0',
                  whiteSpace: 'nowrap',
                }}
              >
                Display Name
              </TableCell>
              <TableCell 
                sx={{ 
                  width: '14%', 
                  py: 2,
                  px: 3,
                  fontWeight: 700,
                  fontSize: '0.8125rem',
                  color: '#1976d2',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  borderBottom: '2px solid',
                  borderColor: '#e0e0e0',
                  textAlign: 'center',
                  whiteSpace: 'nowrap',
                }}
              >
                Status
              </TableCell>
              <TableCell 
                sx={{ 
                  width: '14%', 
                  py: 2,
                  px: 3,
                  fontWeight: 700,
                  fontSize: '0.8125rem',
                  color: '#1976d2',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  borderBottom: '2px solid',
                  borderColor: '#e0e0e0',
                  textAlign: 'center',
                  whiteSpace: 'nowrap',
                }}
              >
                Last Checked
              </TableCell>
              <TableCell 
                sx={{ 
                  width: '9%', 
                  py: 2,
                  px: 3,
                  fontWeight: 700,
                  fontSize: '0.8125rem',
                  color: '#1976d2',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  borderBottom: '2px solid',
                  borderColor: '#e0e0e0',
                  textAlign: 'center',
                  whiteSpace: 'nowrap',
                }}
              >
                Interval
              </TableCell>
              {/* ↓ Actions column now takes remaining space and doesn't wrap */}
              <TableCell 
                sx={{ 
                  width: '30%', 
                  py: 2,
                  px: 3,
                  fontWeight: 700,
                  fontSize: '0.8125rem',
                  color: '#1976d2',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  borderBottom: '2px solid',
                  borderColor: '#e0e0e0',
                  textAlign: 'center',
                  whiteSpace: 'nowrap',
                }}
              >
                Actions
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <AnimatePresence>
              {pages.map((page, index) => (
                <motion.tr
                  key={page.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  onMouseEnter={() => setHoveredRow(page.id)}
                  onMouseLeave={() => setHoveredRow(null)}
                  style={{ display: 'table-row' }}
                >
                  <TableCell 
                    sx={{ 
                      py: 2,
                      px: 3,
                      verticalAlign: 'middle',
                      borderBottom: '1px solid',
                      borderColor: '#f0f0f0',
                      bgcolor: hoveredRow === page.id ? alpha('#1976d2', 0.02) : 'transparent',
                      transition: 'background-color 0.2s ease',
                    }}
                  >
                    <Tooltip title={`${getShortUrl(page.url)}${getUrlPath(page.url)}`} placement="top">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LinkIcon sx={{ fontSize: 14, color: '#9e9e9e', flexShrink: 0 }} />
                        <Typography 
                          variant="body2" 
                          component="a"
                          href={page.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{
                            textDecoration: 'none',
                            color: '#1976d2',
                            fontSize: '0.875rem',
                            fontWeight: 500,
                            '&:hover': {
                              textDecoration: 'underline',
                              color: '#1565c0',
                            },
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {getShortUrl(page.url)}
                        </Typography>
                      </Box>
                    </Tooltip>
                  </TableCell>

                  <TableCell 
                    sx={{ 
                      py: 2,
                      px: 3,
                      verticalAlign: 'middle',
                      borderBottom: '1px solid',
                      borderColor: '#f0f0f0',
                      bgcolor: hoveredRow === page.id ? alpha('#1976d2', 0.02) : 'transparent',
                    }}
                  >
                    <Typography 
                      variant="body2"
                      sx={{
                        fontWeight: 600,
                        fontSize: '0.875rem',
                        color: '#424242',
                      }}
                    >
                      {page.display_name || '—'}
                    </Typography>
                  </TableCell>

                  <TableCell 
                    sx={{ 
                      py: 2,
                      px: 3,
                      verticalAlign: 'middle',
                      textAlign: 'center',
                      borderBottom: '1px solid',
                      borderColor: '#f0f0f0',
                      bgcolor: hoveredRow === page.id ? alpha('#1976d2', 0.02) : 'transparent',
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                      {getStatusChip(page)}
                    </Box>
                  </TableCell>

                  <TableCell 
                    sx={{ 
                      py: 2,
                      px: 3,
                      verticalAlign: 'middle',
                      textAlign: 'center',
                      borderBottom: '1px solid',
                      borderColor: '#f0f0f0',
                      bgcolor: hoveredRow === page.id ? alpha('#1976d2', 0.02) : 'transparent',
                    }}
                  >
                    <Box>
                      <Typography 
                        variant="body2"
                        sx={{
                          fontWeight: 500,
                          fontSize: '0.875rem',
                          color: '#424242',
                        }}
                      >
                        {formatDate(page.last_checked)}
                      </Typography>
                      {page.last_checked && (
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            color: '#9e9e9e',
                            fontSize: '0.75rem',
                          }}
                        >
                          {formatTimeAgo(page.last_checked)}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>

                  <TableCell 
                    sx={{ 
                      py: 2,
                      px: 3,
                      verticalAlign: 'middle',
                      textAlign: 'center',
                      borderBottom: '1px solid',
                      borderColor: '#f0f0f0',
                      bgcolor: hoveredRow === page.id ? alpha('#1976d2', 0.02) : 'transparent',
                    }}
                  >
                    <Chip
                      label={page.check_interval_minutes < 60
                        ? `${page.check_interval_minutes}m`
                        : page.check_interval_minutes < 1440
                        ? `${Math.round(page.check_interval_minutes / 60)}h`
                        : `${Math.round(page.check_interval_minutes / 1440)}d`
                      }
                      size="small"
                      sx={{
                        bgcolor: alpha('#1976d2', 0.1),
                        color: '#1976d2',
                        fontWeight: 600,
                        fontSize: '0.75rem',
                      }}
                    />
                  </TableCell>

                  {/* Actions cell — icons + buttons on one row, no wrapping */}
                  <TableCell 
                    sx={{ 
                      py: 2,
                      px: 2,
                      verticalAlign: 'middle',
                      borderBottom: '1px solid',
                      borderColor: '#f0f0f0',
                      bgcolor: hoveredRow === page.id ? alpha('#1976d2', 0.02) : 'transparent',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                      {/* Edit */}
                      <Tooltip title="Edit page">
                        <IconButton
                          onClick={() => handleEditClick(page)}
                          disabled={!page.is_active}
                          size="small"
                          sx={{
                            color: '#9e9e9e',
                            '&:hover': {
                              color: '#1976d2',
                              bgcolor: alpha('#1976d2', 0.1),
                            },
                          }}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>

                      {/* Delete */}
                      <Tooltip title="Delete page">
                        <IconButton
                          onClick={() => {
                            if (window.confirm(`Delete "${page.display_name || page.url}"?`)) {
                              onPageDeleted(page.id);
                            }
                          }}
                          disabled={deletingPages.has(page.id)}
                          size="small"
                          sx={{
                            color: '#9e9e9e',
                            '&:hover': {
                              color: '#d32f2f',
                              bgcolor: alpha('#d32f2f', 0.1),
                            },
                          }}
                        >
                          {deletingPages.has(page.id) ? (
                            <CircularProgress size={16} />
                          ) : (
                            <DeleteIcon fontSize="small" />
                          )}
                        </IconButton>
                      </Tooltip>

                      {/* Check Now */}
                      <Tooltip title="Check for changes now">
                        <span>
                          <Button
                            variant="contained"
                            size="small"
                            onClick={() => onPageCrawl(page.id)}
                            disabled={crawlingPages.has(page.id) || !page.is_active}
                            startIcon={
                              crawlingPages.has(page.id) ? (
                                <CircularProgress size={13} color="inherit" />
                              ) : (
                                <RefreshIcon sx={{ fontSize: '16px !important' }} />
                              )
                            }
                            sx={{
                              height: 34,
                              px: 1.5,
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              textTransform: 'none',
                              borderRadius: 1.5,
                              background: '#1976d2',
                              boxShadow: 'none',
                              whiteSpace: 'nowrap',
                              minWidth: 'max-content',
                              '& .MuiButton-startIcon': { mr: 0.5 },
                              '&:hover': {
                                background: '#1565c0',
                                transform: 'translateY(-1px)',
                                boxShadow: '0 4px 12px rgba(25, 118, 210, 0.3)',
                              },
                              transition: 'all 0.2s ease',
                            }}
                          >
                            {crawlingPages.has(page.id) ? 'Checking...' : 'Check Now'}
                          </Button>
                        </span>
                      </Tooltip>

                      {/* Fact Check */}
                      <Tooltip 
                        title={
                          hasVersionsForFactCheck(page) 
                            ? "Analyze content with AI fact checking" 
                            : "Check the page first to enable fact checking"
                        }
                      >
                        <span>
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={() => navigate(`/fact-check/${page.id}`)}
                            disabled={!hasVersionsForFactCheck(page)}
                            startIcon={<FactCheckIcon sx={{ fontSize: '16px !important' }} />}
                            sx={{
                              height: 34,
                              px: 1.5,
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              textTransform: 'none',
                              borderRadius: 1.5,
                              whiteSpace: 'nowrap',
                              minWidth: 'max-content',
                              '& .MuiButton-startIcon': { mr: 0.5 },
                              borderColor: hasVersionsForFactCheck(page) ? '#1976d2' : '#e0e0e0',
                              color: hasVersionsForFactCheck(page) ? '#1976d2' : '#bdbdbd',
                              '&:hover': {
                                borderColor: hasVersionsForFactCheck(page) ? '#1565c0' : '#bdbdbd',
                                backgroundColor: hasVersionsForFactCheck(page) ? alpha('#1976d2', 0.05) : 'transparent',
                              },
                            }}
                          >
                            Fact Check
                          </Button>
                        </span>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </motion.tr>
              ))}
            </AnimatePresence>
          </TableBody>
        </Table>
      </TableContainer>

      {/* Edit Dialog */}
      <Dialog 
        open={!!editingPage} 
        onClose={() => setEditingPage(null)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: { 
            borderRadius: 2,
            overflow: 'hidden',
          }
        }}
      >
        <Box sx={{ 
          background: '#1976d2',
          p: 3,
          color: 'white',
        }}>
          <DialogTitle sx={{ p: 0, mb: 1, fontSize: '1.5rem', fontWeight: 'bold' }}>
            Edit Page
          </DialogTitle>
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            Update monitoring settings for your tracked page
          </Typography>
        </Box>
        
        <DialogContent sx={{ pt: 3 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1 }}>
            <TextField
              label="Display Name"
              value={editFormData.display_name}
              onChange={(e) => setEditFormData({
                ...editFormData,
                display_name: e.target.value
              })}
              fullWidth
              disabled={editLoading}
              size="medium"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  '&:hover fieldset': { borderColor: '#1976d2' },
                  '&.Mui-focused fieldset': { borderColor: '#1976d2' },
                },
              }}
            />

            <TextField
              label="URL"
              value={editingPage?.url || ''}
              fullWidth
              disabled
              size="medium"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  bgcolor: alpha('#000', 0.02),
                },
              }}
            />

            <TextField
              select
              label="Check Interval"
              value={editFormData.check_interval_hours}
              onChange={(e) => setEditFormData({
                ...editFormData,
                check_interval_hours: parseInt(e.target.value)
              })}
              fullWidth
              disabled={editLoading}
              size="medium"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  '&:hover fieldset': { borderColor: '#1976d2' },
                  '&.Mui-focused fieldset': { borderColor: '#1976d2' },
                },
              }}
            >
              {intervalOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body1">{option.icon}</Typography>
                    <Typography>{option.label}</Typography>
                  </Box>
                </MenuItem>
              ))}
            </TextField>

            {editError && (
              <Fade in>
                <Box sx={{ 
                  p: 2, 
                  borderRadius: 2, 
                  bgcolor: alpha('#d32f2f', 0.1),
                  border: `1px solid ${alpha('#d32f2f', 0.3)}`,
                }}>
                  <Typography color="error" variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <WarningIcon fontSize="small" />
                    {editError}
                  </Typography>
                </Box>
              </Fade>
            )}
          </Box>
        </DialogContent>
        
        <DialogActions sx={{ px: 3, py: 2, borderTop: 1, borderColor: '#e0e0e0', gap: 1 }}>
          <Button 
            onClick={() => setEditingPage(null)} 
            disabled={editLoading}
            sx={{ 
              borderRadius: 2,
              px: 3,
              color: '#757575',
              '&:hover': { bgcolor: alpha('#757575', 0.05) },
            }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleEditSubmit} 
            disabled={editLoading}
            variant="contained"
            sx={{ 
              borderRadius: 2,
              px: 4,
              background: '#1976d2',
              '&:hover': {
                background: '#1565c0',
                transform: 'translateY(-1px)',
                boxShadow: '0 4px 12px rgba(25, 118, 210, 0.4)',
              },
              transition: 'all 0.2s ease',
            }}
          >
            {editLoading ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Updating...
              </>
            ) : (
              'Update Page'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default PageList;