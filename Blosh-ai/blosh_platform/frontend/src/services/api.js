import axios from 'axios';

const API_BASE_URL = '/api';

export const login = async (password) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/login`, { password });
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.message || 'Login failed');
    }
    throw new Error('Network error. Please try again.');
  }
};

export const logout = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/logout`);
    return response.data;
  } catch (error) {
    throw new Error('Logout failed');
  }
};

export const checkAuth = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/check-auth`);
    return response.data.authenticated;
  } catch (error) {
    return false;
  }
};

// ============================================================================
// BRAND ANALYZER API
// ============================================================================

export const uploadBrandAnalysis = async (file, weekNumber, year) => {
  try {
    const formData = new FormData();
    formData.append('pdf', file);
    formData.append('week_number', weekNumber);
    formData.append('year', year);
    
    const response = await axios.post(`${API_BASE_URL}/brand-analyzer/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.message || 'Upload failed');
    }
    throw new Error('Network error. Please try again.');
  }
};

export const getAllAnalyses = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/brand-analyzer/analyses`);
    return response.data.data;
  } catch (error) {
    throw new Error('Failed to fetch analyses');
  }
};

export const getAnalysisDetail = async (analysisId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/brand-analyzer/analysis/${analysisId}`);
    return response.data.data;
  } catch (error) {
    throw new Error('Failed to fetch analysis details');
  }
};

export const getDownloadUrl = (analysisId, filename) => {
  // Direct backend URL - bypass React entirely
  return `http://localhost:5001/api/downloads/${analysisId}/${filename}`;
};

export const deleteAnalysis = async (analysisId) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/brand-analyzer/analysis/${analysisId}`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to delete analysis');
  }
};

// ============================================================================
// SETTINGS API
// ============================================================================

export const getSettings = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/settings`);
    return response.data.data;
  } catch (error) {
    throw new Error('Failed to fetch settings');
  }
};

export const updateSettings = async (settings) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/settings`, settings);
    return response.data;
  } catch (error) {
    throw new Error('Failed to update settings');
  }
};

