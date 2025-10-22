import React, { useState } from 'react';
import Dashboard from './Dashboard';
import AuthModal from './AuthModal'; // Import the new component
import './LandingPage.css';

const LandingPage = () => {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authModalTab, setAuthModalTab] = useState('login');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  const openAuthModal = (tab) => {
    setAuthModalTab(tab);
    setShowAuthModal(true);
  };

  const closeAuthModal = () => {
    setShowAuthModal(false);
  };

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  if (isAuthenticated) {
    return <Dashboard user={user} />;
  }

  return (
    <div className="landing-page">
      <nav className="navbar">
        <div className="nav-container">
          <div className="logo">
            <i className="fas fa-brain"></i>
            <span>EVOAI</span>
          </div>
          <div className="nav-actions">
            <button 
              className="nav-btn login-btn"
              onClick={() => openAuthModal('login')}
            >
              Sign In
            </button>
            <button 
              className="nav-btn register-btn"
              onClick={() => openAuthModal('register')}
            >
              Register
            </button>
          </div>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-content">
          <div className="hero-text">
            <h1>Your Intelligent Assistant Is Here</h1>
            <p>PersonalAI helps you work smarter, not harder. Get quick answers, spark new ideas, and enjoy personalized support tailored just for you.</p>
            <div className="hero-buttons">
              <button className="btn-primary" onClick={() => openAuthModal('register')}>
                Get Started Free
              </button>
              <button className="btn-secondary">
                <i className="fas fa-play-circle"></i> Watch Demo
              </button>
            </div>
          </div>
          <div className="hero-visual">
            <div className="ai-visualization">
              <div className="central-orb">
                <i className="fas fa-brain"></i>
              </div>
              <div className="floating-elements">
                <div className="floating-element el-1">
                  <i className="fas fa-comment"></i>
                </div>
                <div className="floating-element el-2">
                  <i className="fas fa-lightbulb"></i>
                </div>
                <div className="floating-element el-3">
                  <i className="fas fa-chart-line"></i>
                </div>
                <div className="floating-element el-4">
                  <i className="fas fa-code"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="features-section">
        <div className="container">
          <h2>Why Professionals Choose PersonalAI</h2>
          <p className="section-subtitle">Experience the future of personal assistance with our powerful features</p>
          
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <i className="fas fa-rocket"></i>
              </div>
              <h3>Lightning Fast</h3>
              <p>Get instant responses to your queries with our optimized AI engine</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">
                <i className="fas fa-lock"></i>
              </div>
              <h3>Secure & Private</h3>
              <p>Your data is encrypted and never shared with third parties</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">
                <i className="fas fa-lightbulb"></i>
              </div>
              <h3>Smart Learning</h3>
              <p>Adapts to your preferences and style for personalized assistance</p>
            </div>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-brand">
              <div className="logo">
                <i className="fas fa-brain"></i>
                <span>PersonalAI</span>
              </div>
              <p>Transforming the way you work and think with artificial intelligence</p>
            </div>
            
            <div className="footer-links">
              <div className="footer-column">
                <h4>Product</h4>
                <a href="#">Features</a>
                <a href="#">Use Cases</a>
              </div>
              
              <div className="footer-column">
                <h4>Company</h4>
                <a href="#">About</a>
                <a href="#">Blog</a>
              </div>
              
              <div className="footer-column">
                <h4>Support</h4>
                <a href="#">Help Center</a>
                <a href="#">Contact</a>
              </div>
            </div>
          </div>
          
          <div className="footer-bottom">
            <p>&copy; 2023 PersonalAI. All rights reserved.</p>
          </div>
        </div>
      </footer>

      <AuthModal 
        showAuthModal={showAuthModal}
        closeAuthModal={closeAuthModal}
        activeTab={authModalTab}
        onLoginSuccess={handleLoginSuccess}
      />
    </div>
  );
};

export default LandingPage;