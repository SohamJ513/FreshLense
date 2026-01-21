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
      setPageData(data);
      
      if (data.versions.length > 0) {
        setSelectedVersion(data.versions[0].version_id);
      }
      
      if (data.versions.length >= 2) {
        setOldVersion(data.versions[1].version_id);
        setNewVersion(data.versions[0].version_id);
      }
    } catch (error) {
      console.error('Failed to load page versions:', error);
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
      const result = await factCheckApi.compareVersions(oldVersion, newVersion);
      setDiffResult(result);
      setActiveTab('compare');
    } catch (error) {
      console.error('Comparison failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
      {/* Global image constraints - using a style tag without jsx prop */}
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
                      {pageData?.page_info.display_name || '8th page'}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-700 w-16">URL:</span>
                    <a 
                      href={pageData?.page_info.url || 'https://legacy.reactjs.org/blog/2017/09/26/react-v16.0.html'} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-800 underline truncate max-w-md"
                    >
                      {pageData?.page_info.url || 'https://legacy.reactjs.org/blog/2017/09/26/react-v16.0.html'}
                    </a>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-600">Available Versions</div>
                <div className="text-2xl font-bold text-gray-900">{pageData?.versions.length || 2}</div>
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
                  {pageData?.versions.length || 2}
                </span>
              </div>
              
              <div className="space-y-3">
                {pageData?.versions.map((version: PageVersionInfo, index: number) => (
                  <div
                    key={version.version_id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      (activeTab === 'factcheck' && selectedVersion === version.version_id) ||
                      (activeTab === 'compare' && (oldVersion === version.version_id || newVersion === version.version_id))
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    onClick={() => {
                      if (activeTab === 'factcheck') {
                        setSelectedVersion(version.version_id);
                      }
                    }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <div className={`w-2 h-2 rounded-full ${
                          index === 0 ? 'bg-green-500' : 'bg-blue-500'
                        }`}></div>
                        <div className="text-sm font-medium text-gray-900">
                          {formatDate(version.timestamp)}
                        </div>
                      </div>
                      {index === 0 && (
                        <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full font-medium">
                          Latest
                        </span>
                      )}
                    </div>
                    
                    <div className="text-xs text-gray-500 mb-2">
                      {version.word_count} words • {version.content_length} chars
                    </div>
                    
                    <div className="text-sm text-gray-600 line-clamp-2">
                      {version.content_preview}
                    </div>
                  </div>
                ))}
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
                            {((factCheckResult.verified_claims / factCheckResult.total_claims) * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-red-600 mb-1">
                            {factCheckResult.unverified_claims}
                          </div>
                          <div className="text-sm font-medium text-red-800">Unverified</div>
                          <div className="text-xs text-red-600 mt-1">
                            {((factCheckResult.unverified_claims / factCheckResult.total_claims) * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
                          <div className="text-2xl font-bold text-yellow-600 mb-1">
                            {factCheckResult.inconclusive_claims}
                          </div>
                          <div className="text-sm font-medium text-yellow-800">Inconclusive</div>
                          <div className="text-xs text-yellow-600 mt-1">
                            {((factCheckResult.inconclusive_claims / factCheckResult.total_claims) * 100).toFixed(1)}%
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
                            <option key={version.version_id} value={version.version_id}>
                              {formatDate(version.timestamp)}
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
                            <option key={version.version_id} value={version.version_id}>
                              {formatDate(version.timestamp)}
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
                      {/* Comparison Header */}
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
                        </div>
                        <div className="bg-white border border-gray-300 px-3 py-2 rounded shadow-sm">
                          <div className="text-base font-semibold text-gray-900">
                            {diffResult.total_changes} Changes
                          </div>
                        </div>
                      </div>
                      
                      {/* Diff Viewer with image constraints */}
                      <div className="diff-viewer-wrapper">
                        <ContentDiffViewer changes={diffResult.changes} />
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
                        Select two versions and click "Compare Versions" to see differences.
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