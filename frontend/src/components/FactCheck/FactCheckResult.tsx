import React from 'react';
import { FactCheckItem, Verdict, ClaimType } from '../../types/factCheck';

interface FactCheckResultProps {
  result: FactCheckItem;
}

const FactCheckResult: React.FC<FactCheckResultProps> = ({ result }) => {
  const getVerdictColor = (verdict: Verdict) => {
    switch (verdict) {
      case Verdict.TRUE:
        return 'bg-green-100 text-green-800 border-green-300';
      case Verdict.FALSE:
        return 'bg-red-100 text-red-800 border-red-300';
      case Verdict.UNVERIFIED:
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case Verdict.INCONCLUSIVE:
        return 'bg-gray-100 text-gray-800 border-gray-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getClaimTypeColor = (type: ClaimType) => {
    switch (type) {
      case ClaimType.VERSION_INFO:
        return 'bg-blue-100 text-blue-800';
      case ClaimType.PERFORMANCE:
        return 'bg-purple-100 text-purple-800';
      case ClaimType.SECURITY:
        return 'bg-red-100 text-red-800';
      case ClaimType.COMPATIBILITY:
        return 'bg-orange-100 text-orange-800';
      case ClaimType.API_REFERENCE:
        return 'bg-indigo-100 text-indigo-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const renderSourceLink = (source: string, index: number) => {
    // Check if source is in "Title (URL)" format
    const match = source.match(/^(.*?)\s*\((https?:\/\/[^)]+)\)$/);
    
    if (match) {
      const title = match[1].trim();
      const url = match[2];
      return (
        <div key={index} className="flex items-start text-sm mb-1">
          <span className="text-blue-600 mr-2 mt-0.5">•</span>
          <a 
            href={url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 hover:underline wrap-break-word"
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
          <div key={index} className="flex items-start text-sm mb-1">
            <span className="text-blue-600 mr-2 mt-0.5">•</span>
            <a 
              href={urlMatch[1]} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 hover:underline wrap-break-word"
            >
              {source}
            </a>
          </div>
        );
      }
      return (
        <div key={index} className="flex items-start text-sm mb-1">
          <span className="text-gray-600 mr-2 mt-0.5">•</span>
          <span className="text-gray-700 wrap-break-word">{source}</span>
        </div>
      );
    }
  };

  return (
    <div className="border rounded-lg p-4 mb-4 bg-white shadow-sm">
      <div className="flex justify-between items-start mb-3">
        <span className={`px-2 py-1 rounded text-xs font-medium ${getClaimTypeColor(result.claim_type)}`}>
          {result.claim_type.replace('_', ' ').toUpperCase()}
        </span>
        <span className={`px-2 py-1 rounded text-xs font-medium border ${getVerdictColor(result.verdict)}`}>
          {result.verdict.toUpperCase()}
        </span>
      </div>
      
      <p className="text-gray-800 mb-3 font-medium">{result.claim}</p>
      
      {result.context && (
        <div className="mb-3">
          <p className="text-sm text-gray-600 mb-1">Context:</p>
          <p className="text-sm text-gray-700 bg-gray-50 p-2 rounded">{result.context}</p>
        </div>
      )}
      
      <div className="flex justify-between items-center text-sm mb-3">
        <span className="text-gray-600">
          Confidence: <strong>{(result.confidence * 100).toFixed(1)}%</strong>
        </span>
        <span className="text-gray-600 text-xs">
          {result.sources.length} source{result.sources.length !== 1 ? 's' : ''}
        </span>
      </div>
      
      {/* Sources Section */}
      {result.sources && result.sources.length > 0 && (
        <div className="mb-3 p-3 bg-gray-50 rounded border border-gray-200">
          <p className="text-sm font-medium text-gray-700 mb-2">Verification Sources:</p>
          <div className="space-y-1">
            {result.sources.map((source, index) => renderSourceLink(source, index))}
          </div>
        </div>
      )}
      
      {result.explanation && (
        <div className="mt-3 p-3 bg-blue-50 rounded border border-blue-200">
          <p className="text-sm text-blue-800">{result.explanation}</p>
        </div>
      )}
    </div>
  );
};

export default FactCheckResult;