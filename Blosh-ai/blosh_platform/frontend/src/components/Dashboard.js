import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import Sidebar from './Sidebar';
import Home from './Home';
import BrandAnalyzer from './BrandAnalyzer/BrandAnalyzer';
import Settings from './Settings/Settings';
import { logout } from '../services/api';
import './Dashboard.css';

function Dashboard({ setIsAuthenticated }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
      setIsAuthenticated(false);
      navigate('/login');
    } catch (error) {
      toast.error('Logout failed. Please try again.');
    }
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="dashboard">
      <Sidebar 
        isOpen={isSidebarOpen} 
        toggleSidebar={toggleSidebar}
        onLogout={handleLogout}
      />
      
      <div className={`main-content ${isSidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="mobile-header">
          <button className="menu-button" onClick={toggleSidebar}>
            <span className="menu-icon"></span>
            <span className="menu-icon"></span>
            <span className="menu-icon"></span>
          </button>
          <img src="/logo.png" alt="Blosh" className="mobile-logo-img" />
        </div>
        
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/home" element={<Home />} />
          <Route path="/brand-analyzer" element={<BrandAnalyzer />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </div>
      
      {isSidebarOpen && (
        <div className="sidebar-overlay" onClick={toggleSidebar}></div>
      )}
    </div>
  );
}

export default Dashboard;

