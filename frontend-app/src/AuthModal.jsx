import React, { useState } from 'react';
import { Mail, Lock, User, LogIn } from 'lucide-react';

// ✅ JWT Utility Functions
const saveToken = (token) => {
  localStorage.setItem("token", token);
};

const getToken = () => {
  return localStorage.getItem("token");
};

const removeToken = () => {
  localStorage.removeItem("token");
};

const AuthModal = ({ showAuthModal, closeAuthModal, activeTab: initialTab, onLoginSuccess }) => {
  const [activeTab, setActiveTab] = useState(initialTab || 'login');
  const [loginData, setLoginData] = useState({ username: '', password: '' });
  const [registerData, setRegisterData] = useState({ 
    name: '', email: '', password: '', confirmPassword: '' 
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  const handleLoginChange = (e) => {
    setLoginData({ ...loginData, [e.target.name]: e.target.value });
  };

  const handleRegisterChange = (e) => {
    setRegisterData({ ...registerData, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ text: '', type: '' });

    try {
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      username: loginData.username, 
      password: loginData.password 
    }),
  });

      if (!res.ok) {
        throw new Error("Invalid username or password");
      }

      const data = await res.json();
      saveToken(data.access_token); // ✅ Save JWT with helper
      
      const demoUser = {
        name: loginData.username,
        email: loginData.username + '@example.com' // You might want to get this from the actual response
      };
      
      onLoginSuccess(demoUser);
      setMessage({ text: 'Login successful! Redirecting...', type: 'success' });
    } catch (err) {
      setMessage({ text: err.message, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    if (registerData.password !== registerData.confirmPassword) {
      setMessage({ text: 'Passwords do not match', type: 'error' });
      return;
    }
    
    setLoading(true);
    setMessage({ text: '', type: '' });

    try {
  // Adjust this endpoint and payload according to your registration API
  const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      username: registerData.name,
      email: registerData.email,
      password: registerData.password
    }),
  });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || "Registration failed");
      }

      setMessage({ text: 'Registration successful! You can now login.', type: 'success' });
      
      setTimeout(() => {
        setActiveTab('login');
        setRegisterData({ name: '', email: '', password: '', confirmPassword: '' });
      }, 1500);
    } catch (err) {
      setMessage({ text: err.message, type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  if (!showAuthModal) return null;

  return (
    <div className="auth-modal-overlay" onClick={closeAuthModal}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <button className="close-modal" onClick={closeAuthModal}>
          <i className="fas fa-times"></i>
        </button>
        
        <div className="auth-container">
          <div className="auth-header">
            <h2>{activeTab === 'login' ? 'Welcome Back' : 'Create Your Account'}</h2>
            <p>
              {activeTab === 'login' 
                ? 'Sign in to continue your journey with PersonalAI' 
                : 'Join thousands of users enhancing their productivity with PersonalAI'
              }
            </p>
          </div>

          <div className="auth-tabs">
            <button 
              className={`auth-tab ${activeTab === 'login' ? 'active' : ''}`}
              onClick={() => setActiveTab('login')}
            >
              Sign In
            </button>
            <button 
              className={`auth-tab ${activeTab === 'register' ? 'active' : ''}`}
              onClick={() => setActiveTab('register')}
            >
              Register
            </button>
          </div>

          <div className="auth-forms">
            {activeTab === 'login' ? (
              <form className="auth-form" onSubmit={handleLogin}>
                {message.text && (
                  <div className={`message ${message.type}`}>
                    {message.text}
                  </div>
                )}
                
                <div className="input-group">
                  <div className="input-with-icon">
                    <Mail size={18} />
                    <input
                      type="text"
                      name="username"
                      value={loginData.username}
                      onChange={handleLoginChange}
                      placeholder="Enter your username"
                      required
                      disabled={loading}
                    />
                  </div>
                </div>

                <div className="input-group">
                  <div className="input-with-icon">
                    <Lock size={18} />
                    <input
                      type="password"
                      name="password"
                      value={loginData.password}
                      onChange={handleLoginChange}
                      placeholder="Enter your password"
                      required
                      disabled={loading}
                    />
                  </div>
                </div>

                <button 
                  type="submit" 
                  className="auth-submit-btn"
                  disabled={loading}
                >
                  {loading ? <div className="spinner"></div> : (
                    <>
                      <LogIn size={18} /> Sign In
                    </>
                  )}
                </button>

                <div className="auth-divider">
                  <span>Or continue with</span>
                </div>

                <div className="social-auth">
                  <button type="button" className="social-btn google-btn">
                    <i className="fab fa-google"></i>
                    Google
                  </button>
                  <button type="button" className="social-btn github-btn">
                    <i className="fab fa-github"></i>
                    GitHub
                  </button>
                </div>
              </form>
            ) : (
              <form className="auth-form" onSubmit={handleRegister}>
                {message.text && (
                  <div className={`message ${message.type}`}>
                    {message.text}
                  </div>
                )}
                
                <div className="input-group">
                  <div className="input-with-icon">
                    <User size={18} />
                    <input
                      type="text"
                      name="name"
                      value={registerData.name}
                      onChange={handleRegisterChange}
                      placeholder="Full name"
                      required
                      disabled={loading}
                    />
                  </div>
                </div>

                <div className="input-group">
                  <div className="input-with-icon">
                    <Mail size={18} />
                    <input
                      type="email"
                      name="email"
                      value={registerData.email}
                      onChange={handleRegisterChange}
                      placeholder="Email address"
                      required
                      disabled={loading}
                    />
                  </div>
                </div>

                <div className="input-group">
                  <div className="input-with-icon">
                    <Lock size={18} />
                    <input
                      type="password"
                      name="password"
                      value={registerData.password}
                      onChange={handleRegisterChange}
                      placeholder="Create password"
                      required
                      disabled={loading}
                    />
                  </div>
                </div>

                <div className="input-group">
                  <div className="input-with-icon">
                    <Lock size={18} />
                    <input
                      type="password"
                      name="confirmPassword"
                      value={registerData.confirmPassword}
                      onChange={handleRegisterChange}
                      placeholder="Confirm password"
                      required
                      disabled={loading}
                    />
                  </div>
                </div>

                <button 
                  type="submit" 
                  className="auth-submit-btn"
                  disabled={loading}
                >
                  {loading ? <div className="spinner"></div> : 'Create Account'}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
export { getToken, removeToken };