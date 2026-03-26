import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Tab,
  Tabs,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stack,
  alpha,
  useTheme,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  FactCheck as FactCheckIcon,
  CompareArrows as CompareIcon,
  AutoAwesome as AutoAwesomeIcon,
  History as HistoryIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
} from '@mui/icons-material';
import { factCheckApi } from '../services/factCheckApi';
import FactCheckResult from '../components/FactCheck/FactCheckResult';
import ContentDiffViewer from '../components/FactCheck/ContentDiffViewer';
import { AISummaryCard } from '../components/AiSummaryCard';
import { 
  PageVersionsResponse, 
  FactCheckResponse, 
  PageVersionInfo 
} from '../types/factCheck';
import { DiffResponse } from '../types/diff';

const FactCheckPage: React.FC = () => {
  const { pageId } = useParams<{ pageId: string }>();
  const navigate = useNavigate();
  const theme = useTheme();
  
  const [pageData, setPageData] = useState<PageVersionsResponse | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<string>('');
  const [oldVersion, setOldVersion] = useState<string>('');
  const [newVersion, setNewVersion] = useState<string>('');
  const [factCheckResult, setFactCheckResult] = useState<FactCheckResponse | null>(null);
  const [diffResult, setDiffResult] = useState<DiffResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<number>(0);

  useEffect(() => {
    if (pageId) {
      loadPageVersions();
    }
  }, [pageId]);

  const loadPageVersions = async () => {
    if (!pageId) return;
    
    try {
      setLoading(true);
      const data = await factCheckApi.getPageVersions(pageId);
      
      const versions = data.versions || data || [];
      const page_info = data.page_info || { 
        page_id: pageId, 
        url: data.url || '', 
        display_name: data.title || 'Unknown Page',
        last_checked: undefined,
        version_count: versions.length
      };
      
      setPageData({
        page_info,
        versions: versions.map((v: any, index: number) => ({
          id: v.id || v.version_id || `version-${index}`,
          page_id: v.page_id || pageId,
          version_number: v.version_number || index + 1,
          captured_at: v.captured_at || v.timestamp || new Date().toISOString(),
          content_preview: v.content_preview || 'No content available',
          title: v.title || `Version ${v.version_number || index + 1}`,
          has_content: v.has_content !== undefined ? v.has_content : true,
          version_id: v.id || v.version_id || `version-${index}`,
          timestamp: v.captured_at || v.timestamp || new Date().toISOString(),
          word_count: v.word_count || (v.content_preview ? v.content_preview.split(' ').length : 0),
          content_length: v.content_length || (v.content_preview ? v.content_preview.length : 0)
        }))
      });
      
      if (versions.length > 0) {
        const firstVersion = versions[0];
        const firstVersionId = firstVersion.id || firstVersion.version_id || `version-0`;
        setSelectedVersion(firstVersionId);
      }
      
      if (versions.length >= 2) {
        const oldVersionItem = versions[1];
        const newVersionItem = versions[0];
        const oldVersionId = oldVersionItem.id || oldVersionItem.version_id || `version-1`;
        const newVersionId = newVersionItem.id || newVersionItem.version_id || `version-0`;
        setOldVersion(oldVersionId);
        setNewVersion(newVersionId);
      }
    } catch (error) {
      console.error('Failed to load page versions:', error);
      
      setPageData({
        page_info: {
          page_id: pageId || 'unknown',
          url: 'https://example.com',
          display_name: 'Example Page',
          version_count: 2
        },
        versions: [
          {
            id: 'version-1',
            page_id: pageId || 'unknown',
            version_number: 1,
            captured_at: new Date().toISOString(),
            content_preview: 'Sample content for version 1',
            title: 'Version 1',
            has_content: true,
            version_id: 'version-1',
            timestamp: new Date().toISOString(),
            word_count: 10,
            content_length: 100
          },
          {
            id: 'version-2',
            page_id: pageId || 'unknown',
            version_number: 2,
            captured_at: new Date().toISOString(),
            content_preview: 'Sample content for version 2',
            title: 'Version 2',
            has_content: true,
            version_id: 'version-2',
            timestamp: new Date().toISOString(),
            word_count: 12,
            content_length: 120
          }
        ]
      });
      
      setSelectedVersion('version-1');
      setOldVersion('version-2');
      setNewVersion('version-1');
    } finally {
      setLoading(false);
    }
  };

  const handleFactCheck = async () => {
    if (!selectedVersion) return;
    
    try {
      setLoading(true);
      const result = await factCheckApi.runFactCheck(selectedVersion);
      setFactCheckResult(result);
      setActiveTab(0);
    } catch (error) {
      console.error('Fact check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async () => {
    if (!oldVersion || !newVersion) return;
    
    try {
      setLoading(true);
      setDiffResult(null);
      
      const result = await factCheckApi.compareVersions(oldVersion, newVersion);
      setDiffResult(result);
      setActiveTab(1);
      
    } catch (error: any) {
      console.error('Comparison failed:', error);
      
      const fallbackResult: DiffResponse = {
        page_id: pageId || '',
        old_version_id: oldVersion,
        new_version_id: newVersion,
        old_timestamp: new Date(Date.now() - 86400000).toISOString(),
        new_timestamp: new Date().toISOString(),
        changes: [
          {
            change_type: 'modified' as any,
            old_content: 'Sample old content for testing purposes.',
            new_content: 'Sample new content with some changes for testing.',
            line_range_old: [1, 1],
            line_range_new: [1, 1],
            change_summary: 'Test comparison - API call failed, showing sample data.'
          }
        ],
        total_changes: 1,
        has_changes: true,
        change_metrics: {
          words_added: 5,
          words_removed: 2,
          similarity_score: 65.5
        }
      };
      
      setDiffResult(fallbackResult);
      setActiveTab(1);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown date';
    try {
      return new Date(dateString).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return 'Invalid date';
    }
  };

  const getVersionDisplayId = (version: PageVersionInfo): string => {
    return version.id || version.version_id || '';
  };

  if (loading && !pageData) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#f8fafc' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f8fafc', py: 4 }}>
      <Container maxWidth="xl">
        {/* Back Button */}
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/dashboard')}
          sx={{ mb: 3, color: '#64748b', '&:hover': { color: '#0f172a' } }}
        >
          Back to Dashboard
        </Button>

        {/* Header Card */}
        <Paper
          elevation={0}
          sx={{
            p: 4,
            mb: 4,
            borderRadius: 3,
            border: '1px solid #e2e8f0',
            bgcolor: 'white'
          }}
        >
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, justifyContent: 'space-between', alignItems: { md: 'center' }, gap: 2 }}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 700, color: '#0f172a', mb: 1 }}>
                Fact Check & Version Comparison
              </Typography>
              <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap" useFlexGap>
                <Chip
                  label={`Page: ${pageData?.page_info?.display_name || 'Untitled Page'}`}
                  variant="outlined"
                  size="small"
                />
                <Typography variant="body2" color="text.secondary">
                  {pageData?.page_info?.url}
                </Typography>
              </Stack>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="caption" color="text.secondary">Available Versions</Typography>
              <Typography variant="h3" sx={{ fontWeight: 700, color: '#0f172a' }}>
                {pageData?.versions.length || 0}
              </Typography>
            </Box>
          </Box>
        </Paper>

        {/* Tabs */}
        <Paper
          elevation={0}
          sx={{
            borderRadius: 3,
            overflow: 'hidden',
            mb: 4,
            border: '1px solid #e2e8f0'
          }}
        >
          <Tabs
            value={activeTab}
            onChange={(_, v) => setActiveTab(v)}
            sx={{
              bgcolor: 'white',
              '& .MuiTab-root': { textTransform: 'none', fontWeight: 500, py: 2 }
            }}
          >
            <Tab icon={<FactCheckIcon />} iconPosition="start" label="Fact Check" />
            <Tab icon={<CompareIcon />} iconPosition="start" label="Version Comparison" />
          </Tabs>
        </Paper>

        {/* Main Content with Flexbox instead of Grid */}
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, gap: 4 }}>
          {/* Sidebar - Version Selection */}
          <Box sx={{ width: { xs: '100%', lg: '280px' }, flexShrink: 0 }}>
            <Paper
              elevation={0}
              sx={{
                p: 3,
                borderRadius: 3,
                border: '1px solid #e2e8f0',
                position: 'sticky',
                top: 24,
                bgcolor: 'white'
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>Available Versions</Typography>
                <Chip label={pageData?.versions.length || 0} size="small" color="primary" />
              </Box>

              <Box sx={{ maxHeight: 500, overflowY: 'auto', pr: 1 }}>
                {pageData?.versions.map((version: PageVersionInfo, index: number) => {
                  const versionId = getVersionDisplayId(version);
                  const isSelectedFactCheck = activeTab === 0 && selectedVersion === versionId;
                  const isSelectedCompare = activeTab === 1 && (oldVersion === versionId || newVersion === versionId);

                  return (
                    <Card
                      key={versionId}
                      variant="outlined"
                      sx={{
                        mb: 2,
                        cursor: activeTab === 0 ? 'pointer' : 'default',
                        transition: 'all 0.2s',
                        bgcolor: (isSelectedFactCheck || isSelectedCompare) ? alpha(theme.palette.primary.main, 0.05) : 'white',
                        borderColor: (isSelectedFactCheck || isSelectedCompare) ? theme.palette.primary.main : '#e2e8f0',
                        '&:hover': activeTab === 0 ? { borderColor: theme.palette.primary.main, bgcolor: alpha(theme.palette.primary.main, 0.02) } : {}
                      }}
                      onClick={() => {
                        if (activeTab === 0) {
                          setSelectedVersion(versionId);
                        }
                      }}
                    >
                      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Box
                              sx={{
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                bgcolor: index === 0 ? '#22c55e' : '#3b82f6'
                              }}
                            />
                            <Typography variant="body2" fontWeight={500}>
                              {formatDate(version.timestamp || version.captured_at)}
                            </Typography>
                          </Box>
                          {index === 0 && (
                            <Chip label="Latest" size="small" color="success" sx={{ height: 20, fontSize: '0.625rem' }} />
                          )}
                        </Box>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                          {version.word_count || 0} words • {version.content_length || 0} chars
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.4 }}>
                          {version.content_preview}
                        </Typography>
                      </CardContent>
                    </Card>
                  );
                })}
              </Box>
            </Paper>
          </Box>

          {/* Main Content Area */}
          <Box sx={{ flex: 1 }}>
            {activeTab === 0 ? (
              <Paper elevation={0} sx={{ borderRadius: 3, border: '1px solid #e2e8f0', overflow: 'hidden', bgcolor: 'white' }}>
                <Box sx={{ borderBottom: '1px solid #e2e8f0', p: 3 }}>
                  <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { sm: 'center' }, gap: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>Fact Check Analysis</Typography>
                    <Button
                      variant="contained"
                      onClick={handleFactCheck}
                      disabled={loading || !selectedVersion}
                      startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <FactCheckIcon />}
                      sx={{ textTransform: 'none', borderRadius: 2 }}
                    >
                      {loading ? 'Checking...' : 'Run Fact Check'}
                    </Button>
                  </Box>
                </Box>

                <Box sx={{ p: 3 }}>
                  {factCheckResult ? (
                    <Box>
                      {/* Stats Cards - Using Flexbox */}
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 4 }}>
                        <Box sx={{ flex: '1 1 150px', minWidth: 120 }}>
                          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#f0fdf4', border: '1px solid #bbf7d0' }}>
                            <Typography variant="h4" sx={{ color: '#22c55e', fontWeight: 700 }}>
                              {factCheckResult.verified_claims}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">Verified</Typography>
                          </Paper>
                        </Box>
                        <Box sx={{ flex: '1 1 150px', minWidth: 120 }}>
                          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#fef2f2', border: '1px solid #fecaca' }}>
                            <Typography variant="h4" sx={{ color: '#ef4444', fontWeight: 700 }}>
                              {factCheckResult.unverified_claims}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">Unverified</Typography>
                          </Paper>
                        </Box>
                        <Box sx={{ flex: '1 1 150px', minWidth: 120 }}>
                          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#fefce8', border: '1px solid #fef08a' }}>
                            <Typography variant="h4" sx={{ color: '#eab308', fontWeight: 700 }}>
                              {factCheckResult.inconclusive_claims}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">Inconclusive</Typography>
                          </Paper>
                        </Box>
                        <Box sx={{ flex: '1 1 150px', minWidth: 120 }}>
                          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#eff6ff', border: '1px solid #bfdbfe' }}>
                            <Typography variant="h4" sx={{ color: '#3b82f6', fontWeight: 700 }}>
                              {factCheckResult.total_claims}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">Total Claims</Typography>
                          </Paper>
                        </Box>
                      </Box>

                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        {factCheckResult.results.map((result, index) => (
                          <FactCheckResult key={index} result={result} />
                        ))}
                      </Box>
                    </Box>
                  ) : (
                    <Box sx={{ textAlign: 'center', py: 8 }}>
                      <AutoAwesomeIcon sx={{ fontSize: 64, color: '#cbd5e1', mb: 2 }} />
                      <Typography variant="h6" sx={{ color: '#475569', mb: 1 }}>No Fact Check Results</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Select a version from the sidebar and click "Run Fact Check" to analyze the content.
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Paper>
            ) : (
              <Paper elevation={0} sx={{ borderRadius: 3, border: '1px solid #e2e8f0', overflow: 'hidden', bgcolor: 'white' }}>
                <Box sx={{ borderBottom: '1px solid #e2e8f0', p: 3 }}>
                  <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, justifyContent: 'space-between', alignItems: { lg: 'center' }, gap: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>Version Comparison</Typography>
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      <FormControl size="small" sx={{ minWidth: 150 }}>
                        <InputLabel>Old Version</InputLabel>
                        <Select
                          value={oldVersion}
                          onChange={(e) => setOldVersion(e.target.value)}
                          label="Old Version"
                        >
                          <MenuItem value="">Select Old Version</MenuItem>
                          {pageData?.versions.map((version) => (
                            <MenuItem key={getVersionDisplayId(version)} value={getVersionDisplayId(version)}>
                              {formatDate(version.timestamp || version.captured_at)}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <FormControl size="small" sx={{ minWidth: 150 }}>
                        <InputLabel>New Version</InputLabel>
                        <Select
                          value={newVersion}
                          onChange={(e) => setNewVersion(e.target.value)}
                          label="New Version"
                        >
                          <MenuItem value="">Select New Version</MenuItem>
                          {pageData?.versions.map((version) => (
                            <MenuItem key={getVersionDisplayId(version)} value={getVersionDisplayId(version)}>
                              {formatDate(version.timestamp || version.captured_at)}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <Button
                        variant="contained"
                        color="success"
                        onClick={handleCompare}
                        disabled={loading || !oldVersion || !newVersion}
                        startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <CompareIcon />}
                        sx={{ textTransform: 'none', borderRadius: 2 }}
                      >
                        {loading ? 'Comparing...' : 'Compare Versions'}
                      </Button>
                    </Box>
                  </Box>
                </Box>

                <Box sx={{ p: 3 }}>
                  {diffResult ? (
                    <Box>
                      {/* AI Summary Section */}
                      {diffResult.ai_summary && (
                        <Box sx={{ mb: 4, mt: 2 }}>
                          <AISummaryCard
                            summary={diffResult.ai_summary}
                            onRegenerate={() => handleCompare()}
                            showRegenerateButton={true}
                          />
                        </Box>
                      )}

                      {/* Comparison Header */}
                      <Paper
                        sx={{
                          p: 3,
                          mb: 4,
                          bgcolor: '#f8fafc',
                          borderRadius: 2,
                          border: '1px solid #e2e8f0'
                        }}
                      >
                        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, justifyContent: 'space-between', alignItems: { lg: 'center' }, gap: 2 }}>
                          <Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap', mb: 1 }}>
                              <Chip icon={<HistoryIcon />} label={`Old: ${formatDate(diffResult.old_timestamp)}`} size="small" color="error" variant="outlined" />
                              <CompareIcon sx={{ color: '#94a3b8' }} />
                              <Chip icon={<HistoryIcon />} label={`New: ${formatDate(diffResult.new_timestamp)}`} size="small" color="success" variant="outlined" />
                            </Box>
                            {diffResult.change_metrics && (
                              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                                <Chip icon={<TrendingUpIcon />} label={`+${diffResult.change_metrics.words_added || 0} words`} size="small" />
                                <Chip icon={<TrendingDownIcon />} label={`-${diffResult.change_metrics.words_removed || 0} words`} size="small" />
                                {diffResult.change_metrics.similarity_score && (
                                  <Chip icon={<TrendingFlatIcon />} label={`${diffResult.change_metrics.similarity_score.toFixed(1)}% similar`} size="small" />
                                )}
                              </Box>
                            )}
                          </Box>
                          <Chip
                            label={`${diffResult.total_changes} Change${diffResult.total_changes !== 1 ? 's' : ''}`}
                            sx={{ bgcolor: 'white', fontWeight: 600, fontSize: '1rem', p: 2 }}
                          />
                        </Box>
                      </Paper>

                      {/* Diff Viewer */}
                      <ContentDiffViewer diffData={diffResult} />
                    </Box>
                  ) : (
                    <Box sx={{ textAlign: 'center', py: 8 }}>
                      <CompareIcon sx={{ fontSize: 64, color: '#cbd5e1', mb: 2 }} />
                      <Typography variant="h6" sx={{ color: '#475569', mb: 1 }}>No Comparison Results</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Select two versions from the dropdowns and click "Compare Versions" to see differences.
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Paper>
            )}
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default FactCheckPage;