import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { factCheckApi } from '../services/factCheckApi';
import FactCheckResult from '../components/FactCheck/FactCheckResult';
import ContentDiffViewer from '../components/FactCheck/ContentDiffViewer';
import { 
  PageVersionsResponse, 
  FactCheckResponse, 
  PageVersionInfo 
} from '../types/factCheck';
import { DiffResponse } from '../types/diff';

const FactCheckPage: React.FC = () => {
  const { pageId } = useParams<{ pageId: string }>();
  const navigate = useNavigate();
  
  const [pageData, setPageData] = useState<PageVersionsResponse | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<string>('');
  const [oldVersion, setOldVersion] = useState<string>('');
  const [newVersion, setNewVersion] = useState<string>('');
  const [factCheckResult, setFactCheckResult] = useState<FactCheckResponse | null>(null);
  const [diffResult, setDiffResult] = useState<DiffResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'factcheck' | 'compare'>('factcheck');

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
      
      // Handle both response structures
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
          // New fields from updated API
          id: v.id || v.version_id || `version-${index}`,
          page_id: v.page_id || pageId,
          version_number: v.version_number || index + 1,
          captured_at: v.captured_at || v.timestamp || new Date().toISOString(),
          content_preview: v.content_preview || 'No content available',
          title: v.title || `Version ${v.version_number || index + 1}`,
          has_content: v.has_content !== undefined ? v.has_content : true,
          
          // Legacy fields for backward compatibility with existing components
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
      
      // Set fallback data for testing
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
      setActiveTab('factcheck');
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
      
      // Clear previous results
      setDiffResult(null);
      
      // Call the compare API
      console.log('Comparing versions:', { oldVersion, newVersion });
      const result = await factCheckApi.compareVersions(oldVersion, newVersion);
      
      // Debug log to see what we're getting
      console.log('Diff result received:', {
        hasEnhancedData: !!(result.html_diff || result.change_metrics || result.side_by_side_diff),
        totalChanges: result.total_changes,
        hasChanges: result.changes.length > 0,
        changeMetrics: result.change_metrics,
        hasHtmlDiff: !!result.html_diff,
        hasSideBySide: !!result.side_by_side_diff,
        rawData: result
      });
      
      setDiffResult(result);
      setActiveTab('compare');
      
    } catch (error: any) {
      console.error('Comparison failed:', error);
      console.error('Error details:', error.response?.data || error.message);
      
      // Fallback: Create a basic diff result if API fails
      const fallbackResult: DiffResponse = {
        page_id: pageId || '',
        old_version_id: oldVersion,
        new_version_id: newVersion,
        old_timestamp: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
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
      setActiveTab('compare');
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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
          <p className="text-gray-600 text-sm">Loading page data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      {/* Global image constraints */}
      <style>
        {`
          .fact-check-content img,
          .diff-viewer-content img {
            max-width: 100%;
            height: auto;
            border-radius: 0.5rem;
            border: 1px solid #e5e7eb;
          }
          
          .fact-check-content video,
          .diff-viewer-content video {
            max-width: 100%;
            height: auto;
            border-radius: 0.5rem;
          }
          
          .fact-check-content .evidence-media,
          .diff-viewer-content .comparison-media {
            max-width: 100%;
            overflow: hidden;
          }

          .fact-check-result-item,
          .diff-viewer-wrapper {
            max-width: 100%;
            overflow: hidden;
          }
        `}
      </style>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center text-sm text-gray-600 hover:text-gray-900 mb-6 transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Dashboard
          </button>
          
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-start justify-between">
              <div className="space-y-3">
                <h1 className="text-2xl font-bold text-gray-900">Fact Check & Version Comparison</h1>
                <div className="space-y-2">
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-700 w-16">Page:</span>
                    <span className="text-sm text-gray-900 bg-gray-100 px-3 py-1 rounded-md">
                      {pageData?.page_info?.display_name || 'Untitled Page'}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-700 w-16">URL:</span>
                    <a 
                      href={pageData?.page_info?.url || '#'} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-800 underline truncate max-w-md"
                    >
                      {pageData?.page_info?.url || 'No URL available'}
                    </a>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-600">Available Versions</div>
                <div className="text-2xl font-bold text-gray-900">{pageData?.versions.length || 0}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
            <button
              onClick={() => setActiveTab('factcheck')}
              className={`px-6 py-2.5 text-sm font-medium rounded-md transition-all ${
                activeTab === 'factcheck'
                  ? 'bg-white text-gray-900 shadow-sm border border-gray-200'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Fact Check
            </button>
            <button
              onClick={() => setActiveTab('compare')}
              className={`px-6 py-2.5 text-sm font-medium rounded-md transition-all ${
                activeTab === 'compare'
                  ? 'bg-white text-gray-900 shadow-sm border border-gray-200'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Version Comparison
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Version Selection */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg border border-gray-200 p-5 sticky top-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-gray-900">Available Versions</h3>
                <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded text-sm font-medium">
                  {pageData?.versions.length || 0}
                </span>
              </div>
              
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                {pageData?.versions.map((version: PageVersionInfo, index: number) => {
                  const versionId = getVersionDisplayId(version);
                  const isSelectedFactCheck = activeTab === 'factcheck' && selectedVersion === versionId;
                  const isSelectedCompare = activeTab === 'compare' && (oldVersion === versionId || newVersion === versionId);
                  
                  return (
                    <div
                      key={versionId}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        isSelectedFactCheck || isSelectedCompare
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                      onClick={() => {
                        if (activeTab === 'factcheck') {
                          setSelectedVersion(versionId);
                        }
                      }}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${
                            index === 0 ? 'bg-green-500' : 'bg-blue-500'
                          }`}></div>
                          <div className="text-sm font-medium text-gray-900">
                            {formatDate(version.timestamp || version.captured_at)}
                          </div>
                        </div>
                        {index === 0 && (
                          <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full font-medium">
                            Latest
                          </span>
                        )}
                      </div>
                      
                      <div className="text-xs text-gray-500 mb-2">
                        {version.word_count || 0} words • {version.content_length || 0} chars
                      </div>
                      
                      <div className="text-sm text-gray-600 line-clamp-2">
                        {version.content_preview}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {activeTab === 'factcheck' ? (
              <div className="bg-white rounded-lg border border-gray-200">
                <div className="border-b border-gray-200 px-6 py-4">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
                    <h2 className="text-lg font-semibold text-gray-900">Fact Check Analysis</h2>
                    <button
                      onClick={handleFactCheck}
                      disabled={loading || !selectedVersion}
                      className="bg-blue-600 text-white px-5 py-2.5 text-sm font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors flex items-center space-x-2"
                    >
                      {loading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Checking...</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span>Run Fact Check</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                <div className="p-6 fact-check-content">
                  {factCheckResult ? (
                    <div>
                      {/* Stats Cards */}
                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-green-600 mb-1">
                            {factCheckResult.verified_claims}
                          </div>
                          <div className="text-sm font-medium text-green-800">Verified</div>
                          <div className="text-xs text-green-600 mt-1">
                            {factCheckResult.total_claims > 0 ? 
                              ((factCheckResult.verified_claims / factCheckResult.total_claims) * 100).toFixed(1) : 0}%
                          </div>
                        </div>
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-red-600 mb-1">
                            {factCheckResult.unverified_claims}
                          </div>
                          <div className="text-sm font-medium text-red-800">Unverified</div>
                          <div className="text-xs text-red-600 mt-1">
                            {factCheckResult.total_claims > 0 ? 
                              ((factCheckResult.unverified_claims / factCheckResult.total_claims) * 100).toFixed(1) : 0}%
                          </div>
                        </div>
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-yellow-600 mb-1">
                            {factCheckResult.inconclusive_claims}
                          </div>
                          <div className="text-sm font-medium text-yellow-800">Inconclusive</div>
                          <div className="text-xs text-yellow-600 mt-1">
                            {factCheckResult.total_claims > 0 ? 
                              ((factCheckResult.inconclusive_claims / factCheckResult.total_claims) * 100).toFixed(1) : 0}%
                          </div>
                        </div>
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-blue-600 mb-1">
                            {factCheckResult.total_claims}
                          </div>
                          <div className="text-sm font-medium text-blue-800">Total Claims</div>
                          <div className="text-xs text-blue-600 mt-1">100%</div>
                        </div>
                      </div>

                      {/* Results with image constraints */}
                      <div className="space-y-4">
                        {factCheckResult.results.map((result, index) => (
                          <div key={index} className="fact-check-result-item">
                            <FactCheckResult result={result} />
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="w-16 h-16 mx-auto mb-4 text-gray-300">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <h3 className="text-base font-medium text-gray-900 mb-2">No Fact Check Results</h3>
                      <p className="text-sm text-gray-500 max-w-sm mx-auto">
                        Select a version from the sidebar and click "Run Fact Check" to analyze the content.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200">
                <div className="border-b border-gray-200 px-6 py-4">
                  <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
                    <h2 className="text-lg font-semibold text-gray-900">Version Comparison</h2>
                    <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4">
                      <div className="flex space-x-3">
                        <select
                          value={oldVersion}
                          onChange={(e) => setOldVersion(e.target.value)}
                          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="">Select Old Version</option>
                          {pageData?.versions.map((version) => (
                            <option key={getVersionDisplayId(version)} value={getVersionDisplayId(version)}>
                              {formatDate(version.timestamp || version.captured_at)}
                            </option>
                          ))}
                        </select>
                        <select
                          value={newVersion}
                          onChange={(e) => setNewVersion(e.target.value)}
                          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="">Select New Version</option>
                          {pageData?.versions.map((version) => (
                            <option key={getVersionDisplayId(version)} value={getVersionDisplayId(version)}>
                              {formatDate(version.timestamp || version.captured_at)}
                            </option>
                          ))}
                        </select>
                      </div>
                      <button
                        onClick={handleCompare}
                        disabled={loading || !oldVersion || !newVersion}
                        className="bg-green-600 text-white px-5 py-2.5 text-sm font-medium rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors flex items-center space-x-2"
                      >
                        {loading ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            <span>Comparing...</span>
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                            </svg>
                            <span>Compare Versions</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="p-6 diff-viewer-content">
                  {diffResult ? (
                    <div>
                      {/* Enhanced Comparison Header */}
                      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                        <div className="space-y-2 mb-4 lg:mb-0">
                          <div className="flex items-center space-x-4">
                            <div className="bg-red-50 text-red-800 px-3 py-1 rounded text-sm font-medium">
                              <strong>Old Version:</strong> {formatDate(diffResult.old_timestamp)}
                            </div>
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                            </svg>
                            <div className="bg-green-50 text-green-800 px-3 py-1 rounded text-sm font-medium">
                              <strong>New Version:</strong> {formatDate(diffResult.new_timestamp)}
                            </div>
                          </div>
                          
                          {/* Show change metrics if available */}
                          {diffResult.change_metrics && (
                            <div className="flex flex-wrap gap-3 mt-2">
                              <div className="flex items-center space-x-1">
                                <span className="text-xs text-gray-600">Words Added:</span>
                                <span className="text-sm font-medium text-green-600">
                                  +{diffResult.change_metrics.words_added || 0}
                                </span>
                              </div>
                              <div className="flex items-center space-x-1">
                                <span className="text-xs text-gray-600">Words Removed:</span>
                                <span className="text-sm font-medium text-red-600">
                                  -{diffResult.change_metrics.words_removed || 0}
                                </span>
                              </div>
                              {diffResult.change_metrics.similarity_score && (
                                <div className="flex items-center space-x-1">
                                  <span className="text-xs text-gray-600">Similarity:</span>
                                  <span className="text-sm font-medium text-blue-600">
                                    {diffResult.change_metrics.similarity_score.toFixed(1)}%
                                  </span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                        
                        <div className="bg-white border border-gray-300 px-3 py-2 rounded shadow-sm">
                          <div className="text-base font-semibold text-gray-900">
                            {diffResult.total_changes} Change{diffResult.total_changes !== 1 ? 's' : ''}
                          </div>
                          {diffResult.change_metrics && (
                            <div className="text-xs text-gray-500 text-center mt-1">
                              {diffResult.has_changes ? 'Changes detected' : 'No changes'}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Diff Viewer with image constraints */}
                      <div className="diff-viewer-wrapper">
                        <ContentDiffViewer diffData={diffResult} />
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="w-16 h-16 mx-auto mb-4 text-gray-300">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                        </svg>
                      </div>
                      <h3 className="text-base font-medium text-gray-900 mb-2">No Comparison Results</h3>
                      <p className="text-sm text-gray-500 max-w-sm mx-auto">
                        Select two versions from the dropdowns and click "Compare Versions" to see differences.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FactCheckPage;
