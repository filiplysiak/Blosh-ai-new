import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { getSettings, updateSettings } from '../../services/api';
import './Settings.css';

function Settings() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [brands, setBrands] = useState([]);
  const [primaryBrand, setPrimaryBrand] = useState('');
  const [defaultTrendBrand, setDefaultTrendBrand] = useState('');
  const [defaultComparison, setDefaultComparison] = useState('GROUP_AVERAGE');
  const [newBrand, setNewBrand] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await getSettings();
      setSettings(data);
      setBrands(data.brand_analyzer?.competitor_brands || []);
      setPrimaryBrand(data.brand_analyzer?.primary_brand || '');
      setDefaultTrendBrand(data.brand_analyzer?.default_trend_brand || '');
      setDefaultComparison(data.brand_analyzer?.default_comparison || 'GROUP_AVERAGE');
    } catch (error) {
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleAddBrand = () => {
    if (!newBrand.trim()) {
      toast.error('Please enter a brand name');
      return;
    }
    if (brands.includes(newBrand.trim().toUpperCase())) {
      toast.error('Brand already exists');
      return;
    }
    setBrands([...brands, newBrand.trim().toUpperCase()]);
    setNewBrand('');
  };

  const handleRemoveBrand = (brandToRemove) => {
    setBrands(brands.filter(b => b !== brandToRemove));
    if (primaryBrand === brandToRemove) {
      setPrimaryBrand(brands[0] || '');
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const updatedSettings = {
        ...settings,
        brand_analyzer: {
          ...settings.brand_analyzer,
          competitor_brands: brands,
          primary_brand: primaryBrand,
          default_trend_brand: defaultTrendBrand,
          default_comparison: defaultComparison
        }
      };
      await updateSettings(updatedSettings);
      setSettings(updatedSettings);
      toast.success('Settings saved successfully!');
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="settings-container">
        <div className="loading-message">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="settings-container">
      <div className="settings-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">
          Configure your Brand Analyzer settings
        </p>
      </div>

      <div className="settings-content">
        <div className="settings-section">
          <h2 className="section-title">Brand Analyzer</h2>
          
          <div className="setting-group">
            <label className="setting-label">Primary Brand</label>
            <p className="setting-description">
              The main brand to focus analysis on
            </p>
            <select
              value={primaryBrand}
              onChange={(e) => setPrimaryBrand(e.target.value)}
              className="setting-select"
              disabled={saving}
            >
              {brands.map(brand => (
                <option key={brand} value={brand}>{brand}</option>
              ))}
            </select>
          </div>

          <div className="setting-group">
            <label className="setting-label">Default Trend Brand</label>
            <p className="setting-description">
              Default brand to show in trends view
            </p>
            <select
              value={defaultTrendBrand}
              onChange={(e) => setDefaultTrendBrand(e.target.value)}
              className="setting-select"
              disabled={saving}
            >
              {brands.map(brand => (
                <option key={brand} value={brand}>{brand}</option>
              ))}
            </select>
          </div>

          <div className="setting-group">
            <label className="setting-label">Default Comparison</label>
            <p className="setting-description">
              Default comparison for trends view
            </p>
            <select
              value={defaultComparison}
              onChange={(e) => setDefaultComparison(e.target.value)}
              className="setting-select"
              disabled={saving}
            >
              <option value="GROUP_AVERAGE">Group Average</option>
              {brands.map(brand => (
                <option key={brand} value={brand}>{brand}</option>
              ))}
            </select>
          </div>

          <div className="setting-group">
            <label className="setting-label">Competitor Brands</label>
            <p className="setting-description">
              Brands to compare against in analysis reports
            </p>
            
            <div className="brands-list">
              {brands.map(brand => (
                <div key={brand} className="brand-item">
                  <span className="brand-name">{brand}</span>
                  <button
                    className="remove-brand-btn"
                    onClick={() => handleRemoveBrand(brand)}
                    disabled={saving || brands.length <= 1}
                    title="Remove brand"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>

            <div className="add-brand-form">
              <input
                type="text"
                value={newBrand}
                onChange={(e) => setNewBrand(e.target.value)}
                placeholder="Enter brand name"
                className="brand-input"
                disabled={saving}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddBrand();
                  }
                }}
              />
              <button
                type="button"
                onClick={handleAddBrand}
                className="add-brand-btn"
                disabled={saving}
              >
                Add Brand
              </button>
            </div>
          </div>

          <div className="settings-actions">
            <button
              onClick={handleSave}
              className="save-button"
              disabled={saving || brands.length === 0}
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;

