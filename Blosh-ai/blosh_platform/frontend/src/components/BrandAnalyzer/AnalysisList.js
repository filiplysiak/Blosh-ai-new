import React from 'react';
import { getDownloadUrl } from '../../services/api';
import './AnalysisList.css';

function AnalysisList({ analyses, loading, onView, onDelete }) {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const handleDownload = (analysis, fileType, e) => {
    e.stopPropagation();
    const filename = analysis.summary?.files?.[fileType];
    if (!filename) return;
    const url = getDownloadUrl(analysis.id, filename);
    
    // Simple direct navigation - browser will handle download based on Content-Disposition header
    window.location.href = url;
  };

  const handleDelete = (analysisId, e) => {
    e.stopPropagation();
    onDelete(analysisId);
  };

  if (loading) {
    return (
      <div className="analyses-section">
        <h2 className="analyses-title">Past Analyses</h2>
        <div className="loading-message">Loading analyses...</div>
      </div>
    );
  }

  if (analyses.length === 0) {
    return (
      <div className="analyses-section">
        <h2 className="analyses-title">Past Analyses</h2>
        <div className="empty-message">
          <p>No analyses yet. Upload a PDF to get started.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="analyses-section">
      <h2 className="analyses-title">Past Analyses ({analyses.length})</h2>
      
      <div className="analyses-grid">
        {analyses.map((analysis) => (
          <div
            key={analysis.id}
            className="analysis-card"
            onClick={() => onView(analysis)}
          >
            <div className="card-header">
              <h3 className="card-title">
                Week {analysis.week_number} {analysis.year}
              </h3>
              <span className="card-date">{formatDate(analysis.upload_date)}</span>
            </div>

            <div className="card-stats">
              <div className="stat-item">
                <span className="stat-label">Brands Analyzed</span>
                <span className="stat-value">
                  {analysis.summary?.total_brands || 'N/A'}
                </span>
              </div>
              
              {analysis.summary?.freebird?.omzet_index && (
                <div className="stat-item">
                  <span className="stat-label">FREEBIRD Index</span>
                  <span className="stat-value">
                    {analysis.summary.freebird.omzet_index}
                  </span>
                </div>
              )}
            </div>

            <div className="card-actions">
              <button
                className="action-button view-button"
                onClick={(e) => {
                  e.stopPropagation();
                  onView(analysis);
                }}
              >
                View Details
              </button>
              
              <button
                className="action-button delete-button"
                onClick={(e) => handleDelete(analysis.id, e)}
                title="Delete Analysis"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AnalysisList;

