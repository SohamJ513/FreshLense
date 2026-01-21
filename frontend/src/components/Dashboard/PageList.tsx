import React from "react";
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
import { TrackedPage } from "../../services/api";

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

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
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
        />
      );
    }
    
    return (
      <Chip 
        label="Pending" 
        size="small" 
        color="warning"
        icon={<ScheduleIcon />}
      />
    );
  };

  // Check if a page has versions available for fact checking
  const hasVersionsForFactCheck = (page: TrackedPage): boolean => {
    return !!page.current_version_id;
  };

  if (pages.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
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
    <TableContainer 
      component={Paper} 
      elevation={2}
      sx={{ 
        maxWidth: '100%',
        overflow: 'auto'
      }}
    >
      <Table sx={{ 
        tableLayout: 'fixed',
        minWidth: 1000 // Ensures proper minimum width
      }}>
        <TableHead>
          <TableRow>
            {/* ✅ Optimized column distribution */}
            <TableCell sx={{ width: '35%', minWidth: 250 }}><strong>URL</strong></TableCell>
            <TableCell sx={{ width: '15%', minWidth: 120 }}><strong>Display Name</strong></TableCell>
            <TableCell sx={{ width: '12%', minWidth: 100 }}><strong>Status</strong></TableCell>
            <TableCell sx={{ width: '15%', minWidth: 140 }}><strong>Last Checked</strong></TableCell>
            <TableCell sx={{ width: '8%', minWidth: 80 }}><strong>Interval</strong></TableCell>
            <TableCell align="right" sx={{ width: '15%', minWidth: 180 }}><strong>Actions</strong></TableCell>
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
              }}
            >
              {/* ✅ URL Column - More space for long URLs */}
              <TableCell 
                sx={{ 
                  width: '35%',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  py: 2
                }}
              >
                <Tooltip title={page.url}>
                  <Typography 
                    variant="body2" 
                    component="a"
                    href={page.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{
                      textDecoration: 'none',
                      color: 'primary.main',
                      '&:hover': {
                        textDecoration: 'underline',
                      },
                      display: 'block',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {page.url}
                  </Typography>
                </Tooltip>
              </TableCell>

              {/* ✅ Display Name Column */}
              <TableCell sx={{ width: '15%', py: 2 }}>
                <Typography 
                  variant="body2"
                  sx={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {page.display_name || 'Untitled'}
                </Typography>
              </TableCell>

              {/* ✅ Status Column */}
              <TableCell sx={{ width: '12%', py: 2 }}>
                {getStatusChip(page)}
              </TableCell>

              {/* ✅ Last Checked Column */}
              <TableCell sx={{ width: '15%', py: 2 }}>
                <Box>
                  <Typography 
                    variant="body2"
                    sx={{
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      fontSize: '0.875rem'
                    }}
                  >
                    {formatDate(page.last_checked)}
                  </Typography>
                  {page.last_checked && (
                    <Typography 
                      variant="caption" 
                      color="text.secondary"
                      sx={{ display: 'block', mt: 0.5 }}
                    >
                      {formatTimeAgo(page.last_checked)}
                    </Typography>
                  )}
                </Box>
              </TableCell>

              {/* ✅ Interval Column */}
              <TableCell sx={{ width: '8%', py: 2 }}>
                <Typography variant="body2">
                  {page.check_interval_minutes < 60
                    ? `${page.check_interval_minutes}m`
                    : page.check_interval_minutes < 1440
                    ? `${Math.round(page.check_interval_minutes / 60)}h`
                    : `${Math.round(page.check_interval_minutes / 1440)}d`
                  }
                </Typography>
              </TableCell>

              {/* ✅ Actions Column - Compact layout */}
              <TableCell align="right" sx={{ width: '15%', py: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, flexWrap: 'wrap' }}>
                  {/* Check Now Button */}
                  <Tooltip title="Check for changes now">
                    <span>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => onPageCrawl(page.id)}
                        disabled={crawlingPages.has(page.id) || !page.is_active}
                        startIcon={
                          crawlingPages.has(page.id) ? (
                            <CircularProgress size={16} />
                          ) : (
                            <RefreshIcon />
                          )
                        }
                        sx={{ minWidth: 'auto', px: 1 }}
                      >
                        {crawlingPages.has(page.id) ? '...' : 'Check'}
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
                          minWidth: 'auto',
                          px: 1,
                          borderColor: hasVersionsForFactCheck(page) ? 'primary.main' : 'grey.400',
                          color: hasVersionsForFactCheck(page) ? 'primary.main' : 'grey.400',
                        }}
                      >
                        Fact Check
                      </Button>
                    </span>
                  </Tooltip>

                  {/* Delete Button */}
                  <Tooltip title="Delete this page">
                    <span>
                      <IconButton
                        color="error"
                        size="small"
                        onClick={() => {
                          if (window.confirm(`Are you sure you want to delete monitoring for "${page.display_name || page.url}"?`)) {
                            onPageDeleted(page.id);
                          }
                        }}
                        disabled={deletingPages.has(page.id)}
                      >
                        {deletingPages.has(page.id) ? (
                          <CircularProgress size={20} />
                        ) : (
                          <DeleteIcon />
                        )}
                      </IconButton>
                    </span>
                  </Tooltip>
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default PageList;