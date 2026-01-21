// frontend/src/components/FactCheck/FactCheckResults.tsx
import React from 'react';
import { FactCheckResponse } from '../../types/factCheck';
import FactCheckResult from './FactCheckResult'; // Import the single result component

interface FactCheckResultsProps {
  data: FactCheckResponse;
}

const FactCheckResults: React.FC<FactCheckResultsProps> = ({ data }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Header with summary */}
      <div className="bg-gray-50 px-6 py-4 border-b">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-800">Fact Check Results</h3>
            <p className="text-sm text-gray-600">
              {data.page_title} • {new Date(data.checked_at).toLocaleDateString()}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Confidence Score</p>
            <p className={`text-lg font-bold ${
              data.results.length > 0 ? 'text-green-600' : 'text-gray-600'
            }`}>
              {data.results.length > 0 
                ? `${Math.round(
                    (data.verified_claims / data.total_claims) * 100
                  )}%` 
                : 'N/A'
              }
            </p>
          </div>
        </div>
        
        {/* Summary stats */}
        <div className="flex gap-4 mt-3">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{data.verified_claims}</div>
            <div className="text-xs text-gray-600">Verified</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{data.unverified_claims}</div>
            <div className="text-xs text-gray-600">Unverified</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{data.inconclusive_claims}</div>
            <div className="text-xs text-gray-600">Inconclusive</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-800">{data.total_claims}</div>
            <div className="text-xs text-gray-600">Total</div>
          </div>
        </div>
      </div>

      {/* Individual results */}
      <div className="p-6">
        {data.results.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No verifiable technical claims found in this content.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {data.results.map((result, index) => (
              <FactCheckResult key={index} result={result} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default FactCheckResults;