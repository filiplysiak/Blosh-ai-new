import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { getAnalysisDetail, getDownloadUrl } from '../../services/api';
import './AnalysisDetail.css';

function AnalysisDetail({ analysis, onBack, onDelete }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDetails();
  }, [analysis.id]);

  const loadDetails = async () => {
    try {
      setLoading(true);
      const data = await getAnalysisDetail(analysis.id);
      setDetails(data);
    } catch (error) {
      toast.error('Failed to load analysis details');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (fileType) => {
    const filename = details?.files?.[fileType];
    if (!filename) return;
    const url = getDownloadUrl(analysis.id, filename);
    
    // Simple direct navigation - browser will handle download based on Content-Disposition header
    window.location.href = url;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="analysis-detail-container">
        <button className="back-button" onClick={onBack}>
          ← Back to List
        </button>
        <div className="loading-message">Loading analysis details...</div>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="analysis-detail-container">
        <button className="back-button" onClick={onBack}>
          ← Back to List
        </button>
        <div className="error-message">Failed to load analysis details</div>
      </div>
    );
  }

  const summary = details.summary || {};
  const freebird = summary.freebird || {};
  const competitors = summary.competitors || {};
  const groupAvg = summary.group_average || {};

  return (
    <div className="analysis-detail-container">
      <div className="detail-header">
        <button className="back-button" onClick={onBack}>
          ← Back to List
        </button>
        
        <div className="detail-title-section">
          <h1 className="detail-title">
            Week {details.week_number} {details.year} Analysis
          </h1>
          <p className="detail-subtitle">
            Uploaded: {formatDate(details.upload_date)}
          </p>
        </div>

        <div className="detail-actions">
          <button
            className="download-btn"
            onClick={() => handleDownload('pdf')}
          >
            Download Original PDF
          </button>
          <button
            className="download-btn"
            onClick={() => handleDownload('docx')}
          >
            Download Report (DOCX)
          </button>
          <button
            className="download-btn"
            onClick={() => handleDownload('brands_xlsx')}
          >
            Download Brands Excel
          </button>
          <button
            className="download-btn"
            onClick={() => handleDownload('summary_xlsx')}
          >
            Download Summary Excel
          </button>
          <button
            className="delete-btn"
            onClick={() => onDelete(analysis.id)}
          >
            Delete Analysis
          </button>
        </div>
      </div>

      <div className="detail-content">
        {/* FREEBIRD Performance */}
        <div className="detail-section">
          <h2 className="section-title">FREEBIRD Performance</h2>
          <div className="metrics-grid">
            <div className="metric-card">
              <span className="metric-label">Omzet Index</span>
              <span className="metric-value">{freebird.omzet_index || 'N/A'}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Doorverkoop (%)</span>
              <span className="metric-value">{freebird.dvk || 'N/A'}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Marge</span>
              <span className="metric-value">{freebird.marge || 'N/A'}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Rentabiliteit</span>
              <span className="metric-value">{freebird.rent || 'N/A'}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">OS (Voorraadrotatie)</span>
              <span className="metric-value">{freebird.os || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Group Average */}
        <div className="detail-section">
          <h2 className="section-title">Group Average</h2>
          <div className="metrics-grid">
            <div className="metric-card">
              <span className="metric-label">Omzet Index</span>
              <span className="metric-value">{groupAvg.omzet_index || 'N/A'}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Doorverkoop (%)</span>
              <span className="metric-value">{groupAvg.dvk || 'N/A'}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Marge</span>
              <span className="metric-value">{groupAvg.marge || 'N/A'}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Rentabiliteit</span>
              <span className="metric-value">{groupAvg.rent || 'N/A'}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">OS (Voorraadrotatie)</span>
              <span className="metric-value">{groupAvg.os || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Competitors Comparison */}
        {Object.keys(competitors).length > 0 && (
          <div className="detail-section">
            <h2 className="section-title">Competitor Comparison</h2>
            <div className="competitors-table">
              <table>
                <thead>
                  <tr>
                    <th>Brand</th>
                    <th>Omzet Index</th>
                    <th>DvK %</th>
                    <th>Marge</th>
                    <th>OS</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(competitors).map(([brand, data]) => (
                    <tr key={brand} className={brand === 'FREEBIRD' ? 'highlight-row' : ''}>
                      <td className="brand-name">{brand}</td>
                      <td>{data.omzet_index || 'N/A'}</td>
                      <td>{data.dvk || 'N/A'}</td>
                      <td>{data.marge || 'N/A'}</td>
                      <td>{data.os || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Summary Stats */}
        <div className="detail-section">
          <h2 className="section-title">Analysis Summary</h2>
          <div className="summary-stats">
            <div className="summary-item">
              <span className="summary-label">Total Brands Analyzed</span>
              <span className="summary-value">{summary.total_brands || 'N/A'}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Week Number</span>
              <span className="summary-value">{details.week_number}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Year</span>
              <span className="summary-value">{details.year}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Status</span>
              <span className="summary-value status-completed">{details.status}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AnalysisDetail;

