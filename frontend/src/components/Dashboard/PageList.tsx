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
} from "@mui/material";
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  FactCheck as FactCheckIcon,
} from "@mui/icons-material";
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
          color="default"
          icon={<WarningIcon />}
          sx={{ height: 28, fontSize: '0.875rem' }}
        />
      );
    }
    
    if (page.last_change_detected) {
      return (
        <Tooltip title={`Last change: ${formatDate(page.last_change_detected)}`}>
          <Chip 
            label="Changed" 
            size="small" 
            color="success"
            icon={<CheckCircleIcon />}
            sx={{ height: 28, fontSize: '0.875rem' }}
          />
        </Tooltip>
      );
    }
    
    if (page.last_checked) {
      return (
        <Chip 
          label="Monitored" 
          size="small" 
          color="primary"
          icon={<ScheduleIcon />}
          sx={{ height: 28, fontSize: '0.875rem' }}
        />
      );
    }
    
    return (
      <Chip 
        label="Pending" 
        size="small" 
        color="warning"
        icon={<ScheduleIcon />}
        sx={{ height: 28, fontSize: '0.875rem' }}
      />
    );
  };

  // Check if a page has versions available for fact checking
  const hasVersionsForFactCheck = (page: TrackedPage): boolean => {
    return !!page.current_version_id;
  };

  // Handle edit button click
  const handleEditClick = (page: TrackedPage) => {
    setEditingPage(page);
    setEditFormData({
      display_name: page.display_name || "",
      check_interval_hours: Math.round(page.check_interval_minutes / 60),
    });
    setEditError(null);
  };

  // Handle edit form submission
  const handleEditSubmit = async () => {
    if (!editingPage) return;

    setEditLoading(true);
    setEditError(null);

    try {
      const updatedPageResponse: UpdatedPageResponse = await updatePage(editingPage.id, editFormData);
      
      // Convert UpdatedPageResponse to TrackedPage format
      const updatedPage: TrackedPage = {
        id: updatedPageResponse.id,
        user_id: editingPage.user_id, // Preserve from original
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

  // Interval options for the select
  const intervalOptions = [
    { value: 1, label: '1 hour' },
    { value: 6, label: '6 hours' },
    { value: 12, label: '12 hours' },
    { value: 24, label: '1 day' },
    { value: 72, label: '3 days' },
    { value: 168, label: '1 week' },
  ];

  // Get domain for shorter display
  const getShortUrl = (url: string): string => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname.replace('www.', '');
    } catch {
      return url.length > 35 ? url.substring(0, 32) + '...' : url;
    }
  };

  // Get path for tooltip
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
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          No pages being monitored
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Add your first page to get started with monitoring!
        </Typography>
      </Paper>
    );
  }

  return (
    <>
      <TableContainer 
        component={Paper} 
        elevation={2}
        sx={{ 
          width: '100%',
          overflowX: 'auto',
          borderRadius: 1,
        }}
      >
        <Table sx={{ 
          width: '100%',
          tableLayout: 'fixed',
        }}>
          <TableHead>
            <TableRow sx={{ backgroundColor: 'grey.50' }}>
              <TableCell 
                sx={{ 
                  width: '22%', 
                  py: 2,
                  px: 3,
                  fontWeight: 600,
                  fontSize: '0.9375rem',
                  borderBottom: '2px solid',
                  borderColor: 'divider'
                }}
              >
                URL
              </TableCell>
              <TableCell 
                sx={{ 
                  width: '18%', 
                  py: 2,
                  px: 3,
                  fontWeight: 600,
                  fontSize: '0.9375rem',
                  borderBottom: '2px solid',
                  borderColor: 'divider'
                }}
              >
                Display Name
              </TableCell>
              <TableCell 
                sx={{ 
                  width: '12%', 
                  py: 2,
                  px: 3,
                  fontWeight: 600,
                  fontSize: '0.9375rem',
                  borderBottom: '2px solid',
                  borderColor: 'divider',
                  textAlign: 'center'
                }}
              >
                Status
              </TableCell>
              <TableCell 
                sx={{ 
                  width: '16%', 
                  py: 2,
                  px: 3,
                  fontWeight: 600,
                  fontSize: '0.9375rem',
                  borderBottom: '2px solid',
                  borderColor: 'divider',
                  textAlign: 'center'
                }}
              >
                Last Checked
              </TableCell>
              <TableCell 
                sx={{ 
                  width: '10%', 
                  py: 2,
                  px: 3,
                  fontWeight: 600,
                  fontSize: '0.9375rem',
                  borderBottom: '2px solid',
                  borderColor: 'divider',
                  textAlign: 'center'
                }}
              >
                Interval
              </TableCell>
              <TableCell 
                sx={{ 
                  width: '22%', 
                  py: 2,
                  px: 3,
                  fontWeight: 600,
                  fontSize: '0.9375rem',
                  borderBottom: '2px solid',
                  borderColor: 'divider',
                  textAlign: 'center'
                }}
              >
                Actions
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {pages.map((page) => (
              <TableRow 
                key={page.id}
                sx={{
                  '&:hover': {
                    backgroundColor: 'action.hover',
                  },
                  opacity: page.is_active ? 1 : 0.6,
                  height: 64,
                }}
              >
                {/* URL Column */}
                <TableCell 
                  sx={{ 
                    py: 1.75,
                    px: 3,
                    verticalAlign: 'middle'
                  }}
                >
                  <Tooltip title={`${getShortUrl(page.url)}${getUrlPath(page.url)}`}>
                    <Typography 
                      variant="body2" 
                      component="a"
                      href={page.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      sx={{
                        textDecoration: 'none',
                        color: 'primary.main',
                        fontSize: '0.875rem',
                        '&:hover': {
                          textDecoration: 'underline',
                        },
                        display: 'block',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        fontWeight: 500,
                        lineHeight: '1.4'
                      }}
                    >
                      {getShortUrl(page.url)}
                    </Typography>
                  </Tooltip>
                </TableCell>

                {/* Display Name Column */}
                <TableCell 
                  sx={{ 
                    py: 1.75,
                    px: 3,
                    verticalAlign: 'middle'
                  }}
                >
                  <Typography 
                    variant="body2"
                    sx={{
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      fontWeight: 500,
                      fontSize: '0.875rem',
                      lineHeight: '1.4'
                    }}
                  >
                    {page.display_name || '-'}
                  </Typography>
                </TableCell>

                {/* Status Column */}
                <TableCell 
                  sx={{ 
                    py: 1.75,
                    px: 3,
                    verticalAlign: 'middle',
                    textAlign: 'center'
                  }}
                >
                  <Box sx={{ 
                    display: 'flex', 
                    justifyContent: 'center',
                    alignItems: 'center'
                  }}>
                    {getStatusChip(page)}
                  </Box>
                </TableCell>

                {/* Last Checked Column */}
                <TableCell 
                  sx={{ 
                    py: 1.75,
                    px: 3,
                    verticalAlign: 'middle',
                    textAlign: 'center'
                  }}
                >
                  <Box sx={{ 
                    display: 'flex', 
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '100%'
                  }}>
                    <Typography 
                      variant="body2"
                      sx={{
                        fontWeight: 500,
                        fontSize: '0.875rem',
                        lineHeight: '1.3'
                      }}
                    >
                      {formatDate(page.last_checked)}
                    </Typography>
                    {page.last_checked && (
                      <Typography 
                        variant="caption" 
                        color="text.secondary"
                        sx={{ 
                          mt: 0.25,
                          lineHeight: '1.2',
                          fontSize: '0.8125rem'
                        }}
                      >
                        {formatTimeAgo(page.last_checked)}
                      </Typography>
                    )}
                  </Box>
                </TableCell>

                {/* Interval Column */}
                <TableCell 
                  sx={{ 
                    py: 1.75,
                    px: 3,
                    verticalAlign: 'middle',
                    textAlign: 'center'
                  }}
                >
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      fontWeight: 500,
                      fontSize: '0.875rem',
                      lineHeight: '1.4'
                    }}
                  >
                    {page.check_interval_minutes < 60
                      ? `${page.check_interval_minutes}m`
                      : page.check_interval_minutes < 1440
                      ? `${Math.round(page.check_interval_minutes / 60)}h`
                      : `${Math.round(page.check_interval_minutes / 1440)}d`
                    }
                  </Typography>
                </TableCell>

                {/* Actions Column */}
                <TableCell 
                  sx={{ 
                    py: 1.75,
                    px: 3,
                    verticalAlign: 'middle',
                    textAlign: 'center'
                  }}
                >
                  <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 2.5,
                    width: '100%'
                  }}>
                    {/* Icon Buttons - Stacked vertically */}
                    <Box sx={{ 
                      display: 'flex', 
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: 0.75
                    }}>
                      <Tooltip title="Edit page">
                        <span>
                          <IconButton
                            color="primary"
                            size="small"
                            onClick={() => handleEditClick(page)}
                            disabled={!page.is_active}
                            sx={{ 
                              width: 34,
                              height: 34,
                              color: 'primary.main',
                              '&:hover': {
                                backgroundColor: 'primary.50',
                              }
                            }}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>

                      <Tooltip title="Delete page">
                        <span>
                          <IconButton
                            color="error"
                            size="small"
                            onClick={() => {
                              if (window.confirm(`Delete "${page.display_name || page.url}"?`)) {
                                onPageDeleted(page.id);
                              }
                            }}
                            disabled={deletingPages.has(page.id)}
                            sx={{ 
                              width: 34,
                              height: 34,
                              '&:hover': {
                                backgroundColor: 'error.50',
                              }
                            }}
                          >
                            {deletingPages.has(page.id) ? (
                              <CircularProgress size={16} />
                            ) : (
                              <DeleteIcon fontSize="small" />
                            )}
                          </IconButton>
                        </span>
                      </Tooltip>
                    </Box>

                    {/* Text Buttons - Side by Side */}
                    <Box sx={{ 
                      display: 'flex', 
                      flexDirection: 'column',
                      gap: 0.75,
                      width: 130
                    }}>
                      {/* Check Now Button */}
                      <Tooltip title="Check for changes now">
                        <span>
                          <Button
                            variant="contained"
                            size="small"
                            onClick={() => onPageCrawl(page.id)}
                            disabled={crawlingPages.has(page.id) || !page.is_active}
                            startIcon={
                              crawlingPages.has(page.id) ? (
                                <CircularProgress size={14} color="inherit" />
                              ) : (
                                <RefreshIcon />
                              )
                            }
                            sx={{ 
                              width: '100%',
                              height: 32,
                              fontSize: '0.875rem',
                              textTransform: 'none',
                              borderRadius: 1.25,
                              boxShadow: 'none',
                              px: 1.5,
                              minWidth: 'auto',
                              whiteSpace: 'nowrap',
                              '&:hover': {
                                boxShadow: '0 1px 4px rgba(37, 99, 235, 0.2)',
                              }
                            }}
                          >
                            {crawlingPages.has(page.id) ? 'Checking...' : 'Check Now'}
                          </Button>
                        </span>
                      </Tooltip>

                      {/* Fact Check Button */}
                      <Tooltip 
                        title={
                          hasVersionsForFactCheck(page) 
                            ? "Analyze content with fact checking" 
                            : "Check the page first to enable fact checking"
                        }
                      >
                        <span>
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={() => navigate(`/fact-check/${page.id}`)}
                            disabled={!hasVersionsForFactCheck(page)}
                            startIcon={<FactCheckIcon />}
                            sx={{ 
                              width: '100%',
                              height: 32,
                              fontSize: '0.875rem',
                              textTransform: 'none',
                              borderRadius: 1.25,
                              px: 1.5,
                              minWidth: 'auto',
                              whiteSpace: 'nowrap',
                              borderColor: hasVersionsForFactCheck(page) ? 'primary.main' : 'grey.300',
                              color: hasVersionsForFactCheck(page) ? 'primary.main' : 'grey.500',
                              '&:hover': {
                                borderColor: hasVersionsForFactCheck(page) ? 'primary.dark' : 'grey.400',
                                backgroundColor: hasVersionsForFactCheck(page) ? 'primary.50' : 'transparent',
                              }
                            }}
                          >
                            Fact Check
                          </Button>
                        </span>
                      </Tooltip>
                    </Box>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
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
          sx: { borderRadius: 2 }
        }}
      >
        <DialogTitle sx={{ borderBottom: 1, borderColor: 'divider', pb: 2 }}>
          Edit Page
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            {/* Display Name Field */}
            <TextField
              label="Display Name"
              value={editFormData.display_name}
              onChange={(e) => setEditFormData({
                ...editFormData,
                display_name: e.target.value
              })}
              fullWidth
              required
              disabled={editLoading}
              size="medium"
            />

            {/* URL Field (read-only) */}
            <TextField
              label="URL"
              value={editingPage?.url || ''}
              fullWidth
              disabled
              size="medium"
              InputProps={{
                readOnly: true,
              }}
            />

            {/* Check Interval Field */}
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
            >
              {intervalOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>

            {/* Error Display */}
            {editError && (
              <Typography 
                color="error" 
                variant="body2"
                sx={{ 
                  p: 1.5, 
                  borderRadius: 1, 
                  backgroundColor: 'error.light',
                  border: '1px solid',
                  borderColor: 'error.main'
                }}
              >
                {editError}
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, borderTop: 1, borderColor: 'divider' }}>
          <Button 
            onClick={() => setEditingPage(null)} 
            disabled={editLoading}
            color="inherit"
            sx={{ minWidth: 90 }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleEditSubmit} 
            disabled={editLoading}
            variant="contained"
            color="primary"
            sx={{ minWidth: 120 }}
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