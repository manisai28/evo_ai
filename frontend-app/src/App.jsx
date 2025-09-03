import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { MyProvider } from './MyContext';
import LandingPage from './LandingPage';
import Dashboard from './Dashboard';
import ChatWindow from './ChatWindow';

// Helper to check token validity (basic decode without verifying signature)
function isTokenValid(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // convert to ms
    return Date.now() < exp;
  } catch (e) {
    return false;
  }
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  // Load auth state from localStorage on mount
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
  };

  return (
    <MyProvider>
      <Router>
        <div className="App">
          <Routes>
            {/* Landing page */}
            <Route 
              path="/" 
              element={
                isAuthenticated 
                  ? <Navigate to="/dashboard" /> 
                  : <LandingPage onLogin={handleLogin} />
              } 
            />

            {/* Dashboard */}
            <Route 
              path="/dashboard" 
              element={
                isAuthenticated 
                  ? <Dashboard user={user} onLogout={handleLogout} /> 
                  : <Navigate to="/" />
              } 
            />

            {/* Chat window */}
            <Route 
              path="/chat" 
              element={
                isAuthenticated 
                  ? <ChatWindow user={user} onLogout={handleLogout} /> 
                  : <Navigate to="/" />
              } 
            />

            {/* 404 page */}
            <Route path="*" element={<h2>404 - Page Not Found</h2>} />
          </Routes>
        </div>
      </Router>
    </MyProvider>
  );
}

export default App;
