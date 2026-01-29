import React from 'react';
import { FactCheckItem, Verdict, ClaimType } from '../../types/factCheck';
import './FactCheckResult.css'; // Import the CSS file

interface FactCheckResultProps {
  result: FactCheckItem;
}

const FactCheckResult: React.FC<FactCheckResultProps> = ({ result }) => {
  const getVerdictClass = (verdict: Verdict) => {
    switch (verdict) {
      case Verdict.TRUE:
        return 'true';
      case Verdict.FALSE:
        return 'false';
      case Verdict.UNVERIFIED:
        return 'unverified';
      case Verdict.INCONCLUSIVE:
        return 'inconclusive';
      default:
        return 'inconclusive';
    }
  };

  const getClaimTypeClass = (type: ClaimType) => {
    switch (type) {
      case ClaimType.VERSION_INFO:
        return 'version-info';
      case ClaimType.PERFORMANCE:
        return 'performance';
      case ClaimType.SECURITY:
        return 'security';
      case ClaimType.COMPATIBILITY:
        return 'compatibility';
      case ClaimType.API_REFERENCE:
        return 'api-reference';
      default:
        return 'version-info';
    }
  };

  const renderSourceLink = (source: string, index: number) => {
    // Check if source is in "Title (URL)" format
    const match = source.match(/^(.*?)\s*\((https?:\/\/[^)]+)\)$/);
    
    if (match) {
      const title = match[1].trim();
      const url = match[2];
      return (
        <div key={index} className="source-item hover-lift">
          <span className="source-bullet">•</span>
          <a 
            href={url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="source-link wrap-break-word"
          >
            {title}
          </a>
        </div>
      );
    } else {
      // If not in expected format, just display as text with potential link
      const urlMatch = source.match(/(https?:\/\/[^\s]+)/);
      if (urlMatch) {
        return (
          <div key={index} className="source-item hover-lift">
            <span className="source-bullet">•</span>
            <a 
              href={urlMatch[1]} 
              target="_blank" 
              rel="noopener noreferrer"
              className="source-link wrap-break-word"
            >
              {source}
            </a>
          </div>
        );
      }
      return (
        <div key={index} className="source-item">
          <span className="source-bullet">•</span>
          <span className="source-text wrap-break-word">{source}</span>
        </div>
      );
    }
  };

  return (
    <div className="fact-check-result hover-lift">
      <div className="fact-check-header">
        <span className={`claim-type-badge ${getClaimTypeClass(result.claim_type)}`}>
          {result.claim_type.replace('_', ' ').toUpperCase()}
        </span>
        <span className={`verdict-badge ${getVerdictClass(result.verdict)}`}>
          {result.verdict.toUpperCase()}
        </span>
      </div>
      
      <p className="claim-text">{result.claim}</p>
      
      {result.context && (
        <div className="context-section">
          <span className="context-label">Context</span>
          <p className="context-content">{result.context}</p>
        </div>
      )}
      
      <div className="stats-bar">
        <div className="confidence-meter">
          <span className="confidence-label">Confidence:</span>
          <span className={`confidence-value ${getVerdictClass(result.verdict)}`}>
            {(result.confidence * 100).toFixed(1)}%
          </span>
          <div className="progress-bar">
            <div 
              className={`progress-fill ${getVerdictClass(result.verdict)}`}
              style={{ width: `${result.confidence * 100}%` }}
            ></div>
          </div>
        </div>
        <span className="sources-count">
          {result.sources.length} source{result.sources.length !== 1 ? 's' : ''}
        </span>
      </div>
      
      {/* Sources Section */}
      {result.sources && result.sources.length > 0 && (
        <div className="sources-section">
          <span className="sources-label">Verification Sources</span>
          <div className="sources-list">
            {result.sources.map((source, index) => renderSourceLink(source, index))}
          </div>
        </div>
      )}
      
      {result.explanation && (
        <div className="explanation-section">
          <p className="explanation-text">{result.explanation}</p>
        </div>
      )}
    </div>
  );
};

export default FactCheckResult;