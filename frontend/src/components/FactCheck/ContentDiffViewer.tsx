import React, { useState } from 'react';
import { ContentChange, ChangeType, DiffResponse, SideBySideLine } from '../../types/diff';
import './ContentDiffViewer.css';

interface ContentDiffViewerProps {
  diffData?: DiffResponse;
  changes?: ContentChange[];
  viewMode?: 'inline' | 'side-by-side' | 'unified';
}

const ContentDiffViewer: React.FC<ContentDiffViewerProps> = ({ 
  diffData, 
  changes: legacyChanges, 
  viewMode: initialViewMode = 'inline' 
}) => {
  const [currentViewMode, setCurrentViewMode] = useState<'inline' | 'side-by-side' | 'unified'>(initialViewMode);
  
  const changes = diffData?.changes || legacyChanges || [];
  const sideBySideData = diffData?.side_by_side_diff as SideBySideLine[] | undefined;
  
  const getChangeColor = (changeType: ChangeType): string => {
    switch (changeType) {
      case ChangeType.ADDED:
        return 'added-change';
      case ChangeType.REMOVED:
        return 'removed-change';
      case ChangeType.MODIFIED:
        return 'modified-change';
      default:
        return 'unchanged-change';
    }
  };

  const getChangeIcon = (changeType: ChangeType): string => {
    switch (changeType) {
      case ChangeType.ADDED:
        return '➕';
      case ChangeType.REMOVED:
        return '➖';
      case ChangeType.MODIFIED:
        return '✏️';
      default:
        return '📝';
    }
  };

  const getChangeTitle = (changeType: ChangeType): string => {
    switch (changeType) {
      case ChangeType.ADDED:
        return 'Added Content';
      case ChangeType.REMOVED:
        return 'Removed Content';
      case ChangeType.MODIFIED:
        return 'Modified Content';
      default:
        return 'Change';
    }
  };

  const renderInlineChanges = () => {
    return (
      <div className="space-y-4">
        {changes.map((change: ContentChange, index: number) => (
          <div
            key={index}
            className={`change-item ${getChangeColor(change.change_type)}`}
          >
            <div className="change-header">
              <span className="change-icon">{getChangeIcon(change.change_type)}</span>
              <span className="change-title">{getChangeTitle(change.change_type)}</span>
              {change.change_summary && (
                <span className="change-summary">{change.change_summary}</span>
              )}
              <span className="line-info">
                Lines {change.line_range_old[0]}-{change.line_range_old[1]} → {change.line_range_new[0]}-{change.line_range_new[1]}
              </span>
            </div>

            <div className="change-content">
              {change.change_type === ChangeType.MODIFIED && (
                <div className="modified-comparison">
                  <div className="comparison-column">
                    <div className="column-header">Previous Version</div>
                    {change.highlighted_old ? (
                      <div 
                        className="highlighted-content old-content"
                        dangerouslySetInnerHTML={{ __html: change.highlighted_old }}
                      />
                    ) : (
                      <pre className="plain-content">{change.old_content || <em>No content</em>}</pre>
                    )}
                  </div>
                  <div className="comparison-column">
                    <div className="column-header">Current Version</div>
                    {change.highlighted_new ? (
                      <div 
                        className="highlighted-content new-content"
                        dangerouslySetInnerHTML={{ __html: change.highlighted_new }}
                      />
                    ) : (
                      <pre className="plain-content">{change.new_content || <em>No content</em>}</pre>
                    )}
                  </div>
                </div>
              )}
              
              {change.change_type === ChangeType.ADDED && (
                <div className="single-column">
                  <div className="column-header">Added Content</div>
                  {change.highlighted_new ? (
                    <div 
                      className="highlighted-content added-content"
                      dangerouslySetInnerHTML={{ __html: change.highlighted_new }}
                    />
                  ) : (
                    <pre className="plain-content">{change.new_content || <em>No content</em>}</pre>
                  )}
                </div>
              )}
              
              {change.change_type === ChangeType.REMOVED && (
                <div className="single-column">
                  <div className="column-header">Removed Content</div>
                  {change.highlighted_old ? (
                    <div 
                      className="highlighted-content removed-content"
                      dangerouslySetInnerHTML={{ __html: change.highlighted_old }}
                    />
                  ) : (
                    <pre className="plain-content">{change.old_content || <em>No content</em>}</pre>
                  )}
                </div>
              )}
            </div>
            
            {(change.context_before || change.context_after) && (
              <div className="change-context">
                {change.context_before && (
                  <div className="context-before">
                    <span className="context-label">Before: </span>
                    {change.context_before}
                  </div>
                )}
                {change.context_after && (
                  <div className="context-after">
                    <span className="context-label">After: </span>
                    {change.context_after}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderSideBySide = () => {
    if (!sideBySideData || sideBySideData.length === 0) {
      return renderInlineChanges();
    }

    return (
      <div className="side-by-side-view">
        <div className="side-by-side-header">
          <div className="side-header-column">Previous Version</div>
          <div className="side-header-column">Current Version</div>
        </div>
        
        <div className="side-by-side-content">
          {sideBySideData.map((line: SideBySideLine, index: number) => (
            <div key={index} className={`side-by-side-line ${line.type}`}>
              <div className="line-number old-line-num">{line.old_line_num || ''}</div>
              <div className="line-content old-line-content">
                {line.highlighted_old ? (
                  <span dangerouslySetInnerHTML={{ __html: line.highlighted_old || line.old_line || '' }} />
                ) : (
                  line.old_line || ''
                )}
              </div>
              <div className="line-number new-line-num">{line.new_line_num || ''}</div>
              <div className="line-content new-line-content">
                {line.highlighted_new ? (
                  <span dangerouslySetInnerHTML={{ __html: line.highlighted_new || line.new_line || '' }} />
                ) : (
                  line.new_line || ''
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderUnifiedView = () => {
    if (!diffData?.html_diff) {
      return renderInlineChanges();
    }

    return (
      <div 
        className="unified-diff-view"
        dangerouslySetInnerHTML={{ __html: diffData.html_diff }}
      />
    );
  };

  if (!changes || changes.length === 0) {
    return (
      <div className="no-changes text-center py-8 text-gray-500">
        No changes detected between versions.
      </div>
    );
  }

  return (
    <div className="content-diff-viewer">
      {diffData?.change_metrics && (
        <div className="diff-metrics">
          <div className="metric-item">
            <span className="metric-label">Similarity:</span>
            <span className="metric-value">
              {diffData.change_metrics.similarity_score?.toFixed(1) || 0}%
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Words Added:</span>
            <span className="metric-value added">
              {diffData.change_metrics.words_added || 0}
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Words Removed:</span>
            <span className="metric-value removed">
              {diffData.change_metrics.words_removed || 0}
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Changes:</span>
            <span className="metric-value">{changes.length}</span>
          </div>
        </div>
      )}
      
      <div className="view-controls">
        <button 
          className={`view-btn ${currentViewMode === 'inline' ? 'active' : ''}`}
          onClick={() => setCurrentViewMode('inline')}
        >
          Inline Changes
        </button>
        <button 
          className={`view-btn ${currentViewMode === 'side-by-side' ? 'active' : ''}`}
          onClick={() => setCurrentViewMode('side-by-side')}
        >
          Side by Side
        </button>
        <button 
          className={`view-btn ${currentViewMode === 'unified' ? 'active' : ''}`}
          onClick={() => setCurrentViewMode('unified')}
        >
          Unified View
        </button>
      </div>

      {currentViewMode === 'inline' && renderInlineChanges()}
      {currentViewMode === 'side-by-side' && renderSideBySide()}
      {currentViewMode === 'unified' && renderUnifiedView()}
    </div>
  );
};

export default ContentDiffViewer;