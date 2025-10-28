import React from 'react';
import { NavLink } from 'react-router-dom';
import './Sidebar.css';

function Sidebar({ isOpen, toggleSidebar, onLogout }) {
  const menuItems = [
    { name: 'Home', path: '/' },
    { name: 'Brand Analyzer', path: '/brand-analyzer' }
  ];

  return (
    <div className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <img src="/logo.png" alt="Blosh" className="sidebar-logo-img" />
      </div>
      
      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => 
              `nav-item ${isActive ? 'active' : ''}`
            }
            onClick={() => {
              if (window.innerWidth <= 768) {
                toggleSidebar();
              }
            }}
          >
            <span className="nav-text">{item.name}</span>
          </NavLink>
        ))}
      </nav>
      
      <div className="sidebar-footer">
        <NavLink
          to="/settings"
          className="settings-button"
          onClick={() => {
            if (window.innerWidth <= 768) {
              toggleSidebar();
            }
          }}
        >
          <span className="nav-text">Settings</span>
        </NavLink>
        <button className="logout-button" onClick={onLogout}>
          <span className="nav-text">Logout</span>
        </button>
      </div>
    </div>
  );
}

export default Sidebar;

