import React, { useState } from 'react';
import './UploadSection.css';

function UploadSection({ onUpload, uploading }) {
  // Calculate current week number
  const getCurrentWeek = () => {
    const now = new Date();
    const start = new Date(now.getFullYear(), 0, 1);
    const diff = now - start;
    const oneWeek = 1000 * 60 * 60 * 24 * 7;
    return Math.ceil(diff / oneWeek);
  };

  const [file, setFile] = useState(null);
  const [weekNumber, setWeekNumber] = useState(getCurrentWeek().toString());
  const [year, setYear] = useState(new Date().getFullYear());
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (selectedFile) => {
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      
      // Try to extract week number from filename
      const match = selectedFile.name.match(/[Ww]eek?\s*(\d+)/);
      if (match && !weekNumber) {
        setWeekNumber(match[1]);
      }
    } else {
      alert('Please select a PDF file');
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      alert('Please select a file');
      return;
    }
    
    if (!weekNumber || !year) {
      alert('Please enter week number and year');
      return;
    }

    const success = await onUpload(file, parseInt(weekNumber), parseInt(year));
    if (success) {
      // Reset form
      setFile(null);
      setWeekNumber(getCurrentWeek().toString());
      setYear(new Date().getFullYear());
    }
  };

  return (
    <div className="upload-section">
      <h2 className="upload-title">Upload New Analysis</h2>
      
      <form onSubmit={handleSubmit} className="upload-form">
        <div
          className={`upload-dropzone ${dragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input').click()}
        >
          <input
            id="file-input"
            type="file"
            accept=".pdf"
            onChange={handleFileInput}
            style={{ display: 'none' }}
          />
          
          {file ? (
            <div className="file-selected">
              <div className="file-icon">📄</div>
              <div className="file-name">{file.name}</div>
              <div className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
            </div>
          ) : (
            <div className="dropzone-content">
              <div className="dropzone-icon">📄</div>
              <p className="dropzone-text">Drag & drop PDF here</p>
              <p className="dropzone-subtext">or click to browse</p>
            </div>
          )}
        </div>

        <div className="upload-inputs">
          <div className="input-group">
            <label htmlFor="week-number">Week Number</label>
            <input
              id="week-number"
              type="number"
              min="1"
              max="53"
              value={weekNumber}
              onChange={(e) => setWeekNumber(e.target.value)}
              placeholder="39"
              required
              disabled={uploading}
            />
          </div>

          <div className="input-group">
            <label htmlFor="year">Year</label>
            <input
              id="year"
              type="number"
              min="2020"
              max="2030"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              required
              disabled={uploading}
            />
          </div>
        </div>

        <button
          type="submit"
          className="upload-button"
          disabled={!file || uploading}
        >
          {uploading ? 'Processing...' : 'Upload & Analyze'}
        </button>
      </form>
    </div>
  );
}

export default UploadSection;

