import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { uploadBrandAnalysis, getAllAnalyses, deleteAnalysis } from '../../services/api';
import UploadSection from './UploadSection';
import AnalysisList from './AnalysisList';
import AnalysisDetail from './AnalysisDetail';
import TrendsView from './TrendsView';
import './BrandAnalyzer.css';

function BrandAnalyzer() {
  const [analyses, setAnalyses] = useState([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [activeTab, setActiveTab] = useState('analyses'); // 'analyses' or 'trends'

  useEffect(() => {
    loadAnalyses();
  }, []);

  const loadAnalyses = async () => {
    try {
      setLoading(true);
      const data = await getAllAnalyses();
      setAnalyses(data);
    } catch (error) {
      toast.error('Failed to load analyses');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file, weekNumber, year) => {
    try {
      setUploading(true);
      const result = await uploadBrandAnalysis(file, weekNumber, year);
      toast.success('Analysis generated successfully!');
      await loadAnalyses();
      return true;
    } catch (error) {
      toast.error(error.message || 'Upload failed');
      return false;
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (analysisId) => {
    if (!window.confirm('Are you sure you want to delete this analysis?')) {
      return;
    }

    try {
      await deleteAnalysis(analysisId);
      toast.success('Analysis deleted successfully');
      await loadAnalyses();
      if (selectedAnalysis?.id === analysisId) {
        setSelectedAnalysis(null);
      }
    } catch (error) {
      toast.error('Failed to delete analysis');
    }
  };

  const handleViewDetail = (analysis) => {
    setSelectedAnalysis(analysis);
  };

  const handleBackToList = () => {
    setSelectedAnalysis(null);
  };

  if (selectedAnalysis) {
    return (
      <AnalysisDetail
        analysis={selectedAnalysis}
        onBack={handleBackToList}
        onDelete={handleDelete}
      />
    );
  }

  return (
    <div className="brand-analyzer-container">
      <div className="brand-analyzer-header">
        <h1 className="page-title">Blosh Brand Analyzer</h1>
        <p className="page-subtitle">
          Upload ERM Fashion Branche reports to generate comprehensive brand performance analysis
        </p>
      </div>

      <div className="tab-navigation">
        <button
          className={`tab-button ${activeTab === 'analyses' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyses')}
        >
          Analyses
        </button>
        <button
          className={`tab-button ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          Trends
        </button>
      </div>

      {activeTab === 'analyses' ? (
        <>
          <UploadSection onUpload={handleUpload} uploading={uploading} />
          <AnalysisList
            analyses={analyses}
            loading={loading}
            onView={handleViewDetail}
            onDelete={handleDelete}
          />
        </>
      ) : (
        <TrendsView />
      )}
    </div>
  );
}

export default BrandAnalyzer;


