/**
 * ParseCaseDetails Component
 *
 * Display detailed parse case detection information including:
 * - Expected vs detected attributes
 * - Match percentage visualization
 * - Field-by-field analysis
 * - Missing attributes highlighting
 *
 * Part of MAPS (Medical Annotation Processing Suite) transparency system
 */

import React, { useState } from 'react';
import type { DetectionDetails } from '../types/api';
import { AttributeMatchIndicator } from './AttributeMatchIndicator';

interface ParseCaseDetailsProps {
  detectionDetails: Partial<DetectionDetails>;
  showFieldAnalysis?: boolean;
  compact?: boolean;
}

export const ParseCaseDetails: React.FC<ParseCaseDetailsProps> = ({
  detectionDetails,
  showFieldAnalysis = true,
  compact = false,
}) => {
  const [expandedSections, setExpandedSections] = useState<{
    expected: boolean;
    detected: boolean;
    missing: boolean;
    analysis: boolean;
  }>({
    expected: false,
    detected: true,
    missing: true,
    analysis: false,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  if (!detectionDetails) {
    return (
      <div className="text-sm text-gray-500 italic">
        No detection details available
      </div>
    );
  }

  const {
    parse_case,
    confidence,
    match_percentage,
    total_expected,
    total_detected,
    expected_attributes,
    detected_attributes,
    missing_attributes,
    field_analysis,
    confidence_breakdown,
  } = detectionDetails;

  // Compact view for cards/inline display
  if (compact) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Parse Case</span>
          <span className="text-sm font-bold text-blue-600">{parse_case}</span>
        </div>
        {match_percentage !== undefined && total_expected !== undefined && total_detected !== undefined && (
          <AttributeMatchIndicator
            matchPercentage={match_percentage}
            totalExpected={total_expected}
            totalDetected={total_detected}
            totalMissing={(total_expected || 0) - (total_detected || 0)}
            size="sm"
            showDetails={false}
          />
        )}
      </div>
    );
  }

  // Full detailed view
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="border-b border-gray-200 pb-3">
        <h3 className="text-lg font-semibold text-gray-900">Parse Case Detection Analysis</h3>
        <p className="text-sm text-gray-600 mt-1">
          Detailed attribute matching for <span className="font-medium text-blue-600">{parse_case}</span>
        </p>
      </div>

      {/* Match Indicator */}
      {match_percentage !== undefined && total_expected !== undefined && total_detected !== undefined && (
        <div className="bg-gray-50 rounded-lg p-4">
          <AttributeMatchIndicator
            matchPercentage={match_percentage}
            totalExpected={total_expected}
            totalDetected={total_detected}
            totalMissing={(total_expected || 0) - (total_detected || 0)}
            size="md"
            showDetails={true}
          />
        </div>
      )}

      {/* Confidence Breakdown */}
      {confidence !== undefined && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-blue-900">Detection Confidence</span>
            <span className="text-2xl font-bold text-blue-600">{(confidence * 100).toFixed(1)}%</span>
          </div>
          {confidence_breakdown && (
            <div className="mt-2 text-xs text-blue-700 space-y-1">
              {confidence_breakdown.base_confidence !== undefined && (
                <div>Base: {(confidence_breakdown.base_confidence * 100).toFixed(0)}%</div>
              )}
              {confidence_breakdown.match_percentage !== undefined && (
                <div>Match: {confidence_breakdown.match_percentage.toFixed(1)}%</div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Expected Attributes */}
      {expected_attributes && expected_attributes.length > 0 && (
        <div className="border border-gray-200 rounded-lg">
          <button
            onClick={() => toggleSection('expected')}
            className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
          >
            <h4 className="text-sm font-semibold text-gray-900">
              Expected Attributes ({expected_attributes.length})
            </h4>
            <svg
              className={`w-5 h-5 text-gray-500 transition-transform ${expandedSections.expected ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedSections.expected && (
            <div className="p-4 pt-0 border-t border-gray-100">
              <div className="space-y-2">
                {expected_attributes.map((attr, idx) => (
                  <div key={idx} className="text-xs bg-gray-50 p-2 rounded">
                    <div className="font-medium text-gray-900">{attr.name}</div>
                    <div className="text-gray-600 mt-1">{attr.description}</div>
                    <div className="text-gray-500 mt-1 font-mono text-[10px]">{attr.xpath}</div>
                    <div className="mt-1">
                      <span className={`px-2 py-0.5 rounded text-[10px] ${attr.required ? 'bg-red-100 text-red-700' : 'bg-gray-200 text-gray-600'}`}>
                        {attr.required ? 'Required' : 'Optional'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detected Attributes */}
      {detected_attributes && detected_attributes.length > 0 && (
        <div className="border border-green-200 rounded-lg bg-green-50">
          <button
            onClick={() => toggleSection('detected')}
            className="w-full flex items-center justify-between p-4 hover:bg-green-100 transition-colors"
          >
            <h4 className="text-sm font-semibold text-green-900">
              Detected Attributes ({detected_attributes.length})
            </h4>
            <svg
              className={`w-5 h-5 text-green-600 transition-transform ${expandedSections.detected ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedSections.detected && (
            <div className="p-4 pt-0 border-t border-green-200">
              <div className="space-y-2">
                {detected_attributes.map((attr, idx) => (
                  <div key={idx} className="text-xs bg-white p-2 rounded border border-green-200">
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-gray-900">{attr.name}</div>
                      <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    {attr.value && (
                      <div className="text-gray-700 mt-1 bg-gray-50 p-1 rounded font-mono text-[10px]">
                        {attr.value}
                      </div>
                    )}
                    <div className="text-gray-500 mt-1 font-mono text-[10px]">{attr.xpath}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Missing Attributes */}
      {missing_attributes && missing_attributes.length > 0 && (
        <div className="border border-red-200 rounded-lg bg-red-50">
          <button
            onClick={() => toggleSection('missing')}
            className="w-full flex items-center justify-between p-4 hover:bg-red-100 transition-colors"
          >
            <h4 className="text-sm font-semibold text-red-900">
              Missing Attributes ({missing_attributes.length})
            </h4>
            <svg
              className={`w-5 h-5 text-red-600 transition-transform ${expandedSections.missing ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedSections.missing && (
            <div className="p-4 pt-0 border-t border-red-200">
              <div className="space-y-2">
                {missing_attributes.map((attr, idx) => (
                  <div key={idx} className="text-xs bg-white p-2 rounded border border-red-200">
                    <div className="flex items-center justify-between">
                      <div className="font-medium text-gray-900">{attr.name}</div>
                      <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="text-gray-500 mt-1 font-mono text-[10px]">{attr.xpath}</div>
                    {attr.required && (
                      <span className="mt-1 inline-block px-2 py-0.5 bg-red-200 text-red-800 rounded text-[10px]">
                        Required
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Field Analysis */}
      {showFieldAnalysis && field_analysis && field_analysis.length > 0 && (
        <div className="border border-gray-200 rounded-lg">
          <button
            onClick={() => toggleSection('analysis')}
            className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
          >
            <h4 className="text-sm font-semibold text-gray-900">
              Field-by-Field Analysis ({field_analysis.length})
            </h4>
            <svg
              className={`w-5 h-5 text-gray-500 transition-transform ${expandedSections.analysis ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedSections.analysis && (
            <div className="p-4 pt-0 border-t border-gray-100">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-700">Field</th>
                      <th className="px-3 py-2 text-center font-medium text-gray-700">Found</th>
                      <th className="px-3 py-2 text-center font-medium text-gray-700">Confidence</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-700">Value Sample</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {field_analysis.map((field, idx) => (
                      <tr key={idx} className={field.found ? 'bg-green-50' : 'bg-red-50'}>
                        <td className="px-3 py-2 font-medium text-gray-900">{field.field}</td>
                        <td className="px-3 py-2 text-center">
                          {field.found ? (
                            <span className="text-green-600 font-bold">✓</span>
                          ) : (
                            <span className="text-red-600 font-bold">✗</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-center text-gray-700">
                          {(field.confidence * 100).toFixed(0)}%
                        </td>
                        <td className="px-3 py-2 text-gray-600 font-mono text-[10px] truncate max-w-xs">
                          {field.value_sample || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
