import React from 'react';
import { ContentChange, ChangeType } from '../../types/diff';

interface ContentDiffViewerProps {
  changes: ContentChange[];
}

const ContentDiffViewer: React.FC<ContentDiffViewerProps> = ({ changes }) => {
  const getChangeColor = (changeType: ChangeType) => {
    switch (changeType) {
      case ChangeType.ADDED:
        return 'bg-green-50 border-green-200';
      case ChangeType.REMOVED:
        return 'bg-red-50 border-red-200';
      case ChangeType.MODIFIED:
        return 'bg-yellow-50 border-yellow-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getChangeIcon = (changeType: ChangeType) => {
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

  const getChangeTitle = (changeType: ChangeType) => {
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

  if (changes.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No changes detected between versions.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {changes.map((change, index) => (
        <div
          key={index}
          className={`border rounded-lg p-4 ${getChangeColor(change.change_type)}`}
        >
          <div className="flex items-center mb-3">
            <span className="text-lg mr-2">{getChangeIcon(change.change_type)}</span>
            <h4 className="font-medium text-gray-800">
              {getChangeTitle(change.change_type)}
            </h4>
            <span className="ml-auto text-sm text-gray-500">
              Lines {change.line_range_old[0]}-{change.line_range_old[1]} → {change.line_range_new[0]}-{change.line_range_new[1]}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {change.change_type !== ChangeType.ADDED && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Previous Version:</p>
                <pre className="text-sm text-gray-600 bg-white p-3 rounded border overflow-x-auto">
                  {change.old_content || <em className="text-gray-400">No content</em>}
                </pre>
              </div>
            )}
            
            {change.change_type !== ChangeType.REMOVED && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Current Version:</p>
                <pre className="text-sm text-gray-600 bg-white p-3 rounded border overflow-x-auto">
                  {change.new_content || <em className="text-gray-400">No content</em>}
                </pre>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ContentDiffViewer;