import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { MyProvider } from './MyContext';
import LandingPage from './LandingPage';
import Dashboard from './Dashboard';
import ChatWindow from './ChatWindow';

// ✅ Relaxed token validity check
function isTokenValid(token) {
  if (!token) return false;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    // If no exp claim → treat as valid
    if (!payload.exp) return true;
    const exp = payload.exp * 1000; // convert to ms
    return Date.now() < exp;
  } catch (e) {
    return false;
  }
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // ✅ Load auth state from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');

    if (token && isTokenValid(token)) {
      setIsAuthenticated(true);
      if (storedUser) setUser(JSON.parse(storedUser));
    } else {
      // cleanup if expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData, token) => {
    setIsAuthenticated(true);
    setUser(userData);
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    // Force navigation to landing page
    window.location.href = '/';
  };

  // Show loading while checking authentication
  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <MyProvider>
      <Router>
        <div className="App">
          <Routes>
            {/* Landing page - always accessible */}
            <Route 
              path="/" 
              element={
                !isAuthenticated 
                  ? <LandingPage onLogin={handleLogin} /> 
                  : <Navigate to="/dashboard" replace />
              } 
            />

            {/* Protected Dashboard route */}
            <Route 
              path="/dashboard" 
              element={
                isAuthenticated 
                  ? <Dashboard user={user} onLogout={handleLogout} /> 
                  : <Navigate to="/" replace />
              } 
            />

            {/* Protected Chat window */}
            <Route 
              path="/chat" 
              element={
                isAuthenticated 
                  ? <ChatWindow user={user} onLogout={handleLogout} /> 
                  : <Navigate to="/" replace />
              } 
            />

            {/* Catch all route - redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </MyProvider>
  );
}

export default App;