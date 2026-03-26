// frontend/src/components/AiSummaryCard.tsx
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Chip,
  Box,
  Collapse,
  IconButton,
  Tooltip,
  Alert,
  Skeleton,
  Divider,
  Button,
  LinearProgress,
  Avatar,
  Stack,
  alpha,
  useTheme
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Refresh as RefreshIcon,
  Schedule as ScheduleIcon,
  Token as TokenIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  Lightbulb as LightbulbIcon,
  FlashOn as FlashIcon,
  AutoAwesome as AutoAwesomeIcon,
  RocketLaunch as RocketIcon,
  Psychology as PsychologyIcon,
  BarChart as BarChartIcon,
  CheckCircleOutline as CheckIcon,
  ErrorOutline as ErrorIcon,
  InfoOutlined as InfoIconOutlined
} from '@mui/icons-material';
import { AISummary } from '../types/ai';
import { formatDistance } from 'date-fns';

interface AISummaryCardProps {
  summary?: AISummary;
  loading?: boolean;
  error?: string;
  onRegenerate?: () => void;
  isRegenerating?: boolean;
  showRegenerateButton?: boolean;
}

export const AISummaryCard: React.FC<AISummaryCardProps> = ({
  summary,
  loading = false,
  error,
  onRegenerate,
  isRegenerating = false,
  showRegenerateButton = false
}) => {
  const [expanded, setExpanded] = useState(false);
  const theme = useTheme();

  if (loading) {
    return (
      <Card sx={{ 
        mb: 4, 
        borderRadius: 4,
        overflow: 'hidden',
        background: 'linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%)',
      }}>
        <Box sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
            <Skeleton variant="circular" width={48} height={48} />
            <Skeleton variant="text" width={200} height={32} />
          </Box>
          <Skeleton variant="rounded" height={80} sx={{ mb: 2 }} />
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Skeleton variant="rounded" width={100} height={32} />
            <Skeleton variant="rounded" width={100} height={32} />
          </Box>
        </Box>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert 
        severity="error" 
        sx={{ mb: 4, borderRadius: 2 }}
        action={
          onRegenerate && (
            <Button color="inherit" size="small" onClick={onRegenerate}>
              Retry
            </Button>
          )
        }
      >
        {error}
      </Alert>
    );
  }

  if (!summary) {
    return (
      <Box sx={{ 
        mb: 4, 
        p: 4, 
        textAlign: 'center',
        background: 'linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%)',
        borderRadius: 4,
        border: '1px solid #e9d5ff'
      }}>
        <AutoAwesomeIcon sx={{ fontSize: 48, color: '#c084fc', mb: 2, opacity: 0.5 }} />
        <Typography variant="body1" color="text.secondary">
          No AI summary available for this comparison.
        </Typography>
        {showRegenerateButton && onRegenerate && (
          <Button 
            variant="outlined" 
            onClick={onRegenerate} 
            sx={{ mt: 2, borderRadius: 2 }}
            startIcon={<AutoAwesomeIcon />}
          >
            Generate AI Summary
          </Button>
        )}
      </Box>
    );
  }

  if (summary.disabled) {
    return (
      <Alert severity="warning" sx={{ mb: 4, borderRadius: 2 }}>
        {summary.summary || 'AI summaries are disabled. Configure API key to enable.'}
      </Alert>
    );
  }

  const getChangeTypeConfig = (type: string) => {
    switch(type) {
      case 'major':
        return { 
          bg: 'linear-gradient(135deg, #ffebee, #ffcdd2)', 
          color: '#c62828', 
          icon: <TrendingDownIcon sx={{ fontSize: 18 }} />,
          label: 'MAJOR CHANGE'
        };
      case 'minor':
        return { 
          bg: 'linear-gradient(135deg, #fff3e0, #ffe0b2)', 
          color: '#ed6c02', 
          icon: <TrendingFlatIcon sx={{ fontSize: 18 }} />,
          label: 'MINOR CHANGE'
        };
      default:
        return { 
          bg: 'linear-gradient(135deg, #e3f2fd, #bbdef5)', 
          color: '#0288d1', 
          icon: <TrendingUpIcon sx={{ fontSize: 18 }} />,
          label: 'COSMETIC CHANGE'
        };
    }
  };

  const getSentimentConfig = (sentiment: string) => {
    switch(sentiment) {
      case 'positive':
        return { bg: 'linear-gradient(135deg, #e8f5e9, #c8e6c9)', color: '#2e7d32', icon: <CheckIcon sx={{ fontSize: 16 }} /> };
      case 'negative':
        return { bg: 'linear-gradient(135deg, #ffebee, #ffcdd2)', color: '#c62828', icon: <ErrorIcon sx={{ fontSize: 16 }} /> };
      default:
        return { bg: 'linear-gradient(135deg, #f5f5f5, #eeeeee)', color: '#616161', icon: <InfoIconOutlined sx={{ fontSize: 16 }} /> };
    }
  };

  const changeType = getChangeTypeConfig(summary.change_type);
  const sentimentConfig = getSentimentConfig(summary.sentiment);

  return (
    <Card sx={{ 
      mb: 4, 
      borderRadius: 4,
      overflow: 'hidden',
      position: 'relative',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      '&:hover': {
        transform: 'translateY(-4px)',
        boxShadow: '0 20px 40px rgba(0,0,0,0.12)'
      }
    }}>
      {/* Decorative Background */}
      <Box sx={{
        position: 'absolute',
        top: 0,
        right: 0,
        width: 300,
        height: 300,
        background: 'radial-gradient(circle, rgba(156,39,176,0.03) 0%, rgba(156,39,176,0) 70%)',
        pointerEvents: 'none',
        borderRadius: '50%'
      }} />
      
      {/* Header */}
      <Box sx={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        px: 4,
        py: 3,
        position: 'relative'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ 
              bgcolor: 'rgba(255,255,255,0.2)', 
              width: 56, 
              height: 56,
              backdropFilter: 'blur(10px)'
            }}>
              <PsychologyIcon sx={{ color: 'white', fontSize: 32 }} />
            </Avatar>
            <Box>
              <Typography variant="h5" sx={{ color: 'white', fontWeight: 700, letterSpacing: '-0.5px' }}>
                AI Intelligence
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <RocketIcon sx={{ fontSize: 12 }} />
                Powered by Groq Llama 3.3 70B
              </Typography>
            </Box>
          </Box>
          {onRegenerate && showRegenerateButton && (
            <Button
              variant="contained"
              onClick={onRegenerate}
              disabled={isRegenerating}
              startIcon={<RefreshIcon />}
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                backdropFilter: 'blur(10px)',
                borderRadius: 3,
                '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' }
              }}
            >
              {isRegenerating ? 'Regenerating...' : 'Regenerate'}
            </Button>
          )}
        </Box>
      </Box>

      <CardContent sx={{ p: 4 }}>
        {/* Summary Text */}
        <Box sx={{ 
          mb: 4,
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(theme.palette.secondary.light, 0.05)} 100%)`,
          borderRadius: 3,
          p: 3,
          border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`
        }}>
          <Typography 
            variant="body1" 
            sx={{ 
              fontSize: '1.1rem',
              lineHeight: 1.7,
              color: '#1a1a2e',
              fontStyle: 'italic',
              position: 'relative',
              pl: 3,
              '&::before': {
                content: '"“"',
                position: 'absolute',
                left: -4,
                top: -12,
                fontSize: '3rem',
                color: alpha(theme.palette.primary.main, 0.3),
                fontFamily: 'Georgia, serif'
              }
            }}
          >
            {summary.summary}
          </Typography>
        </Box>

        {/* Badges Grid */}
        <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
          <Box sx={{ 
            background: changeType.bg,
            borderRadius: 3,
            px: 2,
            py: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 1
          }}>
            {changeType.icon}
            <Typography variant="caption" sx={{ fontWeight: 600, color: changeType.color }}>
              {changeType.label}
            </Typography>
          </Box>
          
          <Box sx={{ 
            background: sentimentConfig.bg,
            borderRadius: 3,
            px: 2,
            py: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 1
          }}>
            {sentimentConfig.icon}
            <Typography variant="caption" sx={{ fontWeight: 600, color: sentimentConfig.color }}>
              {summary.sentiment.toUpperCase()} SENTIMENT
            </Typography>
          </Box>
        </Box>

        {/* Key Changes */}
        {summary.key_changes && summary.key_changes.length > 0 && (
          <Box sx={{ mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <LightbulbIcon sx={{ color: '#f59e0b' }} />
              <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1.1rem' }}>
                Key Changes
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {summary.key_changes.map((change, index) => (
                <Box key={index} sx={{ 
                  display: 'flex', 
                  alignItems: 'flex-start', 
                  gap: 1.5,
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: alpha(theme.palette.primary.main, 0.03),
                  transition: 'all 0.2s',
                  '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.08) }
                }}>
                  <Box sx={{ 
                    width: 6, 
                    height: 6, 
                    bgcolor: '#9c27b0', 
                    borderRadius: '50%',
                    mt: 0.8
                  }} />
                  <Typography variant="body2" sx={{ color: '#2c3e50', lineHeight: 1.6 }}>
                    {change}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>
        )}

        {/* Expand/Collapse */}
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
          <Button
            onClick={() => setExpanded(!expanded)}
            endIcon={expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            size="small"
            sx={{ 
              color: '#9c27b0',
              textTransform: 'none',
              fontWeight: 500
            }}
          >
            {expanded ? 'Show less' : 'Show more insights'}
          </Button>
        </Box>

        <Collapse in={expanded}>
          <Divider sx={{ my: 3 }} />
          
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
            {/* Technical Impact */}
            {summary.technical_impact && (
              <Box sx={{ 
                bgcolor: alpha(theme.palette.info.main, 0.08),
                borderRadius: 3,
                p: 2.5
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                  <BarChartIcon sx={{ color: '#0288d1' }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#0288d1' }}>
                    Technical Impact
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: '#4a5568', lineHeight: 1.6 }}>
                  {summary.technical_impact}
                </Typography>
              </Box>
            )}

            {/* Recommendation */}
            {summary.recommendation && (
              <Box sx={{ 
                bgcolor: alpha(theme.palette.warning.main, 0.08),
                borderRadius: 3,
                p: 2.5
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                  <RocketIcon sx={{ color: '#ed6c02' }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#ed6c02' }}>
                    Recommendation
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: '#4a5568', lineHeight: 1.6 }}>
                  {summary.recommendation}
                </Typography>
              </Box>
            )}
          </Box>

          {/* Fallback Notice */}
          {summary.is_fallback && (
            <Alert severity="warning" sx={{ mt: 3, borderRadius: 2 }}>
              ⚠️ This is a fallback summary. AI service encountered an error: {summary.error}
            </Alert>
          )}

          {/* Footer Metadata */}
          <Box sx={{ 
            mt: 3, 
            pt: 2, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 2,
            borderTop: `1px solid ${alpha(theme.palette.divider, 0.5)}`
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <FlashIcon sx={{ fontSize: 14, color: '#9c27b0' }} />
                <Typography variant="caption" color="text.secondary">
                  {summary.model_used || 'llama-3.3-70b'}
                </Typography>
              </Box>
              {summary.tokens_used && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <TokenIcon sx={{ fontSize: 14, color: '#9e9e9e' }} />
                  <Typography variant="caption" color="text.secondary">
                    {summary.tokens_used} tokens
                  </Typography>
                </Box>
              )}
              {summary.generated_at && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <ScheduleIcon sx={{ fontSize: 14, color: '#9e9e9e' }} />
                  <Typography variant="caption" color="text.secondary">
                    {formatDistance(new Date(summary.generated_at), new Date(), { addSuffix: true })}
                  </Typography>
                </Box>
              )}
            </Box>
            <Typography variant="caption" color="text.secondary">
              ✨ AI-generated analysis
            </Typography>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};