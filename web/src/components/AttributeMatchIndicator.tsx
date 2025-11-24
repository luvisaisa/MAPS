/**
 * AttributeMatchIndicator Component
 *
 * Visual indicator showing match percentage between expected and detected attributes
 * Part of MAPS (Medical Annotation Processing Suite) detection transparency system
 */

import React from 'react';

interface AttributeMatchIndicatorProps {
  matchPercentage: number;
  totalExpected: number;
  totalDetected: number;
  totalMissing: number;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
}

export const AttributeMatchIndicator: React.FC<AttributeMatchIndicatorProps> = ({
  matchPercentage,
  totalExpected,
  totalDetected,
  totalMissing,
  size = 'md',
  showDetails = true,
}) => {
  // Determine color based on match percentage
  const getColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600 bg-green-100 border-green-300';
    if (percentage >= 60) return 'text-yellow-600 bg-yellow-100 border-yellow-300';
    if (percentage >= 40) return 'text-orange-600 bg-orange-100 border-orange-300';
    return 'text-red-600 bg-red-100 border-red-300';
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-yellow-500';
    if (percentage >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const heightClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4',
  };

  return (
    <div className="space-y-2">
      {/* Match percentage badge */}
      <div className="flex items-center justify-between">
        <span className={`font-medium ${sizeClasses[size]}`}>Attribute Match</span>
        <span
          className={`px-3 py-1 rounded-full font-bold border ${getColor(matchPercentage)} ${
            sizeClasses[size]
          }`}
        >
          {matchPercentage.toFixed(1)}%
        </span>
      </div>

      {/* Progress bar */}
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${heightClasses[size]}`}>
        <div
          className={`${getProgressColor(matchPercentage)} ${heightClasses[size]} transition-all duration-500 ease-out`}
          style={{ width: `${matchPercentage}%` }}
        />
      </div>

      {/* Detailed breakdown */}
      {showDetails && (
        <div className={`flex items-center gap-4 text-gray-600 ${sizeClasses[size]}`}>
          <div className="flex items-center gap-1">
            <span className="font-medium text-blue-600">{totalExpected}</span>
            <span>expected</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="font-medium text-green-600">{totalDetected}</span>
            <span>found</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="font-medium text-red-600">{totalMissing}</span>
            <span>missing</span>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Compact circular indicator for inline use
 */
interface CompactMatchIndicatorProps {
  matchPercentage: number;
  size?: number;
}

export const CompactMatchIndicator: React.FC<CompactMatchIndicatorProps> = ({
  matchPercentage,
  size = 40,
}) => {
  const getColor = (percentage: number) => {
    if (percentage >= 80) return '#10b981'; // green-500
    if (percentage >= 60) return '#eab308'; // yellow-500
    if (percentage >= 40) return '#f97316'; // orange-500
    return '#ef4444'; // red-500
  };

  const color = getColor(matchPercentage);
  const radius = (size - 4) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (matchPercentage / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#e5e7eb"
          strokeWidth="3"
          fill="none"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth="3"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-500 ease-out"
        />
      </svg>
      {/* Percentage text */}
      <span
        className="absolute inset-0 flex items-center justify-center font-bold"
        style={{ fontSize: size / 3, color }}
      >
        {Math.round(matchPercentage)}
      </span>
    </div>
  );
};
