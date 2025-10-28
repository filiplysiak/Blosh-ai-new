import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Styles - All CSS in one place
const styles = {
  // Global styles
  '*': {
    margin: 0,
    padding: 0,
    boxSizing: 'border-box',
  },
  
  body: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    backgroundColor: '#ffffff',
    color: '#333333',
    lineHeight: 1.6,
  },

  // Container styles
  container: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },

  // Header styles
  header: {
    backgroundColor: '#ffffff',
    borderBottom: '1px solid #e5e5e5',
    padding: '1rem 0',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },

  nav: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 2rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  logo: {
    fontSize: '1.75rem',
    fontWeight: '700',
    color: '#000000',
    textDecoration: 'none',
    letterSpacing: '-0.025em',
  },

  navLinks: {
    display: 'flex',
    gap: '2rem',
    alignItems: 'center',
  },

  navLink: {
    color: '#666666',
    textDecoration: 'none',
    fontSize: '0.95rem',
    fontWeight: '500',
    transition: 'color 0.2s ease',
  },

  // Main content styles
  main: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
  },

  // Login page styles
  loginContainer: {
    width: '100%',
    maxWidth: '400px',
    padding: '3rem',
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    border: '1px solid #f3f4f6',
  },

  loginTitle: {
    fontSize: '2rem',
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: '2rem',
    color: '#111827',
    letterSpacing: '-0.025em',
  },

  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
  },

  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },

  label: {
    fontSize: '0.875rem',
    fontWeight: '600',
    color: '#374151',
  },

  input: {
    padding: '0.75rem 1rem',
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: '#d1d5db',
    borderRadius: '8px',
    fontSize: '1rem',
    transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
    outline: 'none',
  },

  inputFocus: {
    borderColor: '#3b82f6',
    boxShadow: '0 0 0 3px rgba(59, 130, 246, 0.1)',
  },

  button: {
    backgroundColor: '#000000',
    color: '#ffffff',
    padding: '0.75rem 1.5rem',
    border: 'none',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease, transform 0.1s ease',
    marginTop: '1rem',
  },

  buttonHover: {
    backgroundColor: '#1f2937',
    transform: 'translateY(-1px)',
  },

  buttonDisabled: {
    backgroundColor: '#9ca3af',
    cursor: 'not-allowed',
    transform: 'none',
  },

  // Home page styles
  homeContainer: {
    textAlign: 'center',
    maxWidth: '800px',
    padding: '4rem 2rem',
  },

  welcomeTitle: {
    fontSize: '3rem',
    fontWeight: '700',
    marginBottom: '1rem',
    background: 'linear-gradient(135deg, #000000 0%, #4a5568 100%)',
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    letterSpacing: '-0.025em',
  },

  welcomeSubtitle: {
    fontSize: '1.25rem',
    color: '#6b7280',
    marginBottom: '3rem',
    lineHeight: 1.6,
  },

  // Error styles
  errorMessage: {
    backgroundColor: '#fef2f2',
    border: '1px solid #fecaca',
    color: '#dc2626',
    padding: '0.75rem 1rem',
    borderRadius: '8px',
    fontSize: '0.875rem',
    marginBottom: '1rem',
  },

  // Logout button
  logoutButton: {
    backgroundColor: 'transparent',
    color: '#dc2626',
    border: '1px solid #dc2626',
    padding: '0.5rem 1rem',
    borderRadius: '6px',
    fontSize: '0.875rem',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },

  logoutButtonHover: {
    backgroundColor: '#dc2626',
    color: '#ffffff',
  },

  // Responsive styles
  '@media (max-width: 768px)': {
    nav: {
      padding: '0 1rem',
    },
    
    logo: {
      fontSize: '1.5rem',
    },
    
    loginContainer: {
      padding: '2rem',
      margin: '1rem',
    },
    
    loginTitle: {
      fontSize: '1.75rem',
    },
    
    welcomeTitle: {
      fontSize: '2.25rem',
    },
    
    welcomeSubtitle: {
      fontSize: '1.125rem',
    },
    
    homeContainer: {
      padding: '2rem 1rem',
    },
  },

  '@media (max-width: 480px)': {
    navLinks: {
      gap: '1rem',
    },
    
    loginContainer: {
      padding: '1.5rem',
    },
    
    welcomeTitle: {
      fontSize: '2rem',
    },
    
    main: {
      padding: '1rem',
    },
  },
};

// Apply global styles
const GlobalStyles = () => {
  useEffect(() => {
    // Apply global styles
    Object.assign(document.body.style, styles.body);
    
    // Add responsive styles
    const styleSheet = document.createElement('style');
    styleSheet.textContent = `
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      
      @media (max-width: 768px) {
        .nav {
          padding: 0 1rem !important;
        }
        .logo {
          font-size: 1.5rem !important;
        }
        .login-container {
          padding: 2rem !important;
          margin: 1rem !important;
        }
        .login-title {
          font-size: 1.75rem !important;
        }
        .welcome-title {
          font-size: 2.25rem !important;
        }
        .welcome-subtitle {
          font-size: 1.125rem !important;
        }
        .home-container {
          padding: 2rem 1rem !important;
        }
      }
      
      @media (max-width: 480px) {
        .nav-links {
          gap: 1rem !important;
        }
        .login-container {
          padding: 1.5rem !important;
        }
        .welcome-title {
          font-size: 2rem !important;
        }
        .main {
          padding: 1rem !important;
        }
      }
    `;
    document.head.appendChild(styleSheet);
    
    return () => {
      document.head.removeChild(styleSheet);
    };
  }, []);
  
  return null;
};

// Authentication context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/check-auth', {
        credentials: 'include',
      });
      const data = await response.json();
      
      if (data.authenticated) {
        setUser({ username: data.username });
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setUser({ username: data.username });
        return { success: true };
      } else {
        return { success: false, error: data.error };
      }
    } catch (error) {
      return { success: false, error: 'Network error occurred' };
    }
  };

  const logout = async () => {
    try {
      await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include',
      });
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Header component
const Header = () => {
  const { user, logout } = useAuth();
  const [logoutHovered, setLogoutHovered] = useState(false);

  return (
    <header style={styles.header}>
      <nav style={styles.nav} className="nav">
        <a href="/" style={styles.logo} className="logo">
          Blosh
        </a>
        {user && (
          <div style={styles.navLinks} className="nav-links">
            <span style={styles.navLink}>Home</span>
            <button
              style={{
                ...styles.logoutButton,
                ...(logoutHovered ? styles.logoutButtonHover : {}),
              }}
              onMouseEnter={() => setLogoutHovered(true)}
              onMouseLeave={() => setLogoutHovered(false)}
              onClick={logout}
            >
              Logout
            </button>
          </div>
        )}
      </nav>
    </header>
  );
};

// Login component
const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [focusedInput, setFocusedInput] = useState('');
  const [buttonHovered, setButtonHovered] = useState(false);
  
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(username, password);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div style={styles.main} className="main">
      <div style={styles.loginContainer} className="login-container">
        <h1 style={styles.loginTitle} className="login-title">Welcome to Blosh</h1>
        
        {error && (
          <div style={styles.errorMessage}>
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.inputGroup}>
            <label htmlFor="username" style={styles.label}>
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onFocus={() => setFocusedInput('username')}
              onBlur={() => setFocusedInput('')}
              style={{
                ...styles.input,
                ...(focusedInput === 'username' ? styles.inputFocus : {}),
              }}
              required
              disabled={loading}
            />
          </div>
          
          <div style={styles.inputGroup}>
            <label htmlFor="password" style={styles.label}>
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onFocus={() => setFocusedInput('password')}
              onBlur={() => setFocusedInput('')}
              style={{
                ...styles.input,
                ...(focusedInput === 'password' ? styles.inputFocus : {}),
              }}
              required
              disabled={loading}
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            onMouseEnter={() => setButtonHovered(true)}
            onMouseLeave={() => setButtonHovered(false)}
            style={{
              ...styles.button,
              ...(loading ? styles.buttonDisabled : {}),
              ...(buttonHovered && !loading ? styles.buttonHover : {}),
            }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Home component
const Home = () => {
  const { user } = useAuth();

  return (
    <div style={styles.main} className="main">
      <div style={styles.homeContainer} className="home-container">
        <h1 style={styles.welcomeTitle} className="welcome-title">
          Welcome back, {user?.username}!
        </h1>
        <p style={styles.welcomeSubtitle} className="welcome-subtitle">
          You're now logged into Blosh AI. This is your home dashboard where you can access all your AI tools and services.
        </p>
      </div>
    </div>
  );
};

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={styles.main}>
        <div style={{ textAlign: 'center' }}>Loading...</div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" replace />;
};

// Main App component
const App = () => {
  return (
    <Router>
      <AuthProvider>
        <GlobalStyles />
        <div style={styles.container}>
          <Header />
          <Routes>
            <Route 
              path="/login" 
              element={
                <AuthContext.Consumer>
                  {({ user }) => user ? <Navigate to="/" replace /> : <Login />}
                </AuthContext.Consumer>
              } 
            />
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <Home />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  );
};

export default App;
