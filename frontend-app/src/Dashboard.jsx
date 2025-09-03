import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom"; 
import axios from "axios";
import "./Dashboard.css";
import ChatWindow from "./ChatWindow"; // Import the ChatWindow component

const Dashboard = ({ onLogout }) => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showChatWindow, setShowChatWindow] = useState(false); // State to control chat window visibility
  const navigate = useNavigate();

  // API State
  const [statsData, setStatsData] = useState([]);
  const [recentChats, setRecentChats] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [loading, setLoading] = useState({
    stats: false,
    chats: false,
    notifications: false,
    export: false,
    search: false,
    ask: false,
    settings: false
  });

  // API Configuration
  const API_BASE_URL = window.API_BASE_URL || "http://localhost:5000/api";

  // API Calls
  useEffect(() => {
    fetchDashboardData();
    fetchRecentChats();
    fetchNotifications();
  }, []);

  // API Functions
  const fetchDashboardData = async () => {
    try {
      setLoading(prev => ({ ...prev, stats: true }));
      const response = await axios.get(`${API_BASE_URL}/dashboard/stats`);
      setStatsData(response.data);
    } catch (err) {
      console.error("Error fetching dashboard stats:", err);
      // Fallback to dummy data if API fails
      setStatsData([
        { title: "Total Chats", value: "248", icon: "fas fa-comments", change: "+12%" },
        { title: "Questions Asked", value: "1,247", icon: "fas fa-question-circle", change: "+8%" },
        { title: "Active Users", value: "183", icon: "fas fa-users", change: "+5%" },
        { title: "Satisfaction Rate", value: "94%", icon: "fas fa-star", change: "+2%" },
      ]);
    } finally {
      setLoading(prev => ({ ...prev, stats: false }));
    }
  };

  const fetchRecentChats = async () => {
    try {
      setLoading(prev => ({ ...prev, chats: true }));
      const response = await axios.get(`${API_BASE_URL}/chats/recent`);
      setRecentChats(response.data);
    } catch (err) {
      console.error("Error fetching recent chats:", err);
      // Fallback to dummy data if API fails
      setRecentChats([
        { id: 1, title: "Project Discussion", time: "10:30 AM", unread: false },
        { id: 2, title: "Technical Support", time: "Yesterday", unread: true },
        { id: 3, title: "Feature Request", time: "Oct 12", unread: false },
        { id: 4, title: "Bug Report", time: "Oct 10", unread: false },
        { id: 5, title: "General Inquiry", time: "Oct 8", unread: false },
      ]);
    } finally {
      setLoading(prev => ({ ...prev, chats: false }));
    }
  };

  const fetchNotifications = async () => {
    try {
      setLoading(prev => ({ ...prev, notifications: true }));
      const response = await axios.get(`${API_BASE_URL}/notifications`);
      setNotifications(response.data);
    } catch (err) {
      console.error("Error fetching notifications:", err);
      // Fallback to dummy data if API fails
      setNotifications([
        { id: 1, message: "New message from Sarah", time: "2 min ago" },
        { id: 2, message: "Your weekly report is ready", time: "1 hour ago" },
        { id: 3, message: "System update completed", time: "3 hours ago" },
      ]);
    } finally {
      setLoading(prev => ({ ...prev, notifications: false }));
    }
  };

  const exportData = async () => {
    try {
      setLoading(prev => ({ ...prev, export: true }));
      const response = await axios.get(`${API_BASE_URL}/data/export`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'exported-data.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Error exporting data:", err);
      alert("Failed to export data. Please try again.");
    } finally {
      setLoading(prev => ({ ...prev, export: false }));
    }
  };

  const handleQuickAction = async (action) => {
    switch (action) {
      case "new-chat":
        setShowChatWindow(true); // Show chat window
        break;
      case "search-history":
        setActiveTab("search");
        break;
      case "export-data":
        await exportData();
        break;
      case "settings":
        setActiveTab("settings");
        break;
      default:
        break;
    }
  };

  const handleViewAllChats = () => {
    setActiveTab("chats");
  };

  const handleStartChat = () => {
    setShowChatWindow(true); // Show chat window
  };

  const handleCloseChat = () => {
    setShowChatWindow(false); // Hide chat window
  };

  // Tab Components
  const DashboardHome = () => (
    <div className="dashboard-home">
      <div className="stats-grid">
        {statsData.map((stat, index) => (
          <div key={index} className="stat-card">
            <div className="stat-icon">
              <i className={stat.icon}></i>
            </div>
            <div className="stat-info">
              <h3>{loading.stats ? <div className="loading-spinner small"></div> : stat.value}</h3>
              <p>{stat.title}</p>
            </div>
            {stat.change && (
              <div className={`stat-change ${stat.change.includes('+') ? 'positive' : 'negative'}`}>
                <i className={`fas ${stat.change.includes('+') ? 'fa-arrow-up' : 'fa-arrow-down'}`}></i>
                <span>{stat.change}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="content-grid">
        {/* Recent Chats Panel */}
        <div className="panel recent-chats">
          <div className="panel-header">
            <h3>Recent Chats</h3>
            <button className="view-all" onClick={handleViewAllChats}>
              View All
            </button>
          </div>
          <div className="panel-content">
            {loading.chats ? (
              <div className="loading-placeholder">
                <div className="loading-spinner"></div>
                <p>Loading chats...</p>
              </div>
            ) : recentChats.length > 0 ? (
              recentChats.map((chat) => (
                <div key={chat.id} className="chat-item">
                  <div className="chat-info">
                    <h4>{chat.title}</h4>
                    <p>{chat.time}</p>
                  </div>
                  {chat.unread && <span className="unread-dot"></span>}
                </div>
              ))
            ) : (
              <div className="empty-state">
                <i className="fas fa-comments"></i>
                <p>No recent chats</p>
              </div>
            )}
          </div>
        </div>

        {/* Start Chat Panel */}
        <div className="panel chat-container">
          <div className="start-chat-panel">
            <h3>Start Chat</h3>
            <p>Begin a new conversation with PersonalAI</p>
            <button
              onClick={handleStartChat}
              className="start-chat-btn"
            >
              <i className="fas fa-comments"></i> Go to Chat Window
            </button>
          </div>
        </div>

        {/* Quick Actions Panel */}
        <div className="panel quick-actions">
          <div className="panel-header">
            <h3>Quick Actions</h3>
          </div>
          <div className="panel-content">
            <div className="quick-actions-grid">
              <button
                className="quick-action-btn"
                onClick={() => handleQuickAction("new-chat")}
              >
                <div className="quick-action-icon">
                  <i className="fas fa-plus"></i>
                </div>
                <span>New Chat</span>
              </button>
              <button
                className="quick-action-btn"
                onClick={() => handleQuickAction("search-history")}
              >
                <div className="quick-action-icon">
                  <i className="fas fa-search"></i>
                </div>
                <span>Search History</span>
              </button>
              <button
                className="quick-action-btn"
                onClick={() => handleQuickAction("export-data")}
                disabled={loading.export}
              >
                <div className="quick-action-icon">
                  {loading.export ? <div className="loading-spinner small"></div> : <i className="fas fa-download"></i>}
                </div>
                <span>{loading.export ? "Exporting..." : "Export Data"}</span>
              </button>
              <button
                className="quick-action-btn"
                onClick={() => handleQuickAction("settings")}
              >
                <div className="quick-action-icon">
                  <i className="fas fa-cog"></i>
                </div>
                <span>Settings</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const ChatHistory = () => {
    const [chatHistory, setChatHistory] = useState([]);
    const [historyLoading, setHistoryLoading] = useState(false);
    
    const fetchChatHistory = async () => {
      try {
        setHistoryLoading(true);
        const response = await axios.get(`${API_BASE_URL}/chats/history`);
        setChatHistory(response.data);
      } catch (err) {
        console.error("Error fetching chat history:", err);
        // Fallback to dummy data
        setChatHistory([
          { id: 1, title: "Project Discussion", preview: "We discussed the new features...", timestamp: new Date() },
          { id: 2, title: "Technical Support", preview: "Helped with login issues...", timestamp: new Date(Date.now() - 86400000) },
          { id: 3, title: "Feature Request", preview: "Requested dark mode implementation...", timestamp: new Date(Date.now() - 172800000) },
        ]);
      } finally {
        setHistoryLoading(false);
      }
    };
    
    useEffect(() => {
      if (activeTab === "chats") {
        fetchChatHistory();
      }
    }, [activeTab]);
    
    return (
      <div className="tab-content">
        <div className="tab-header">
          <h2>Chat History</h2>
          <button className="refresh-btn" onClick={fetchChatHistory} disabled={historyLoading}>
            <i className={`fas ${historyLoading ? "fa-spinner fa-spin" : "fa-sync-alt"}`}></i>
            Refresh
          </button>
        </div>
        
        {historyLoading ? (
          <div className="loading-placeholder">
            <div className="loading-spinner"></div>
            <p>Loading chat history...</p>
          </div>
        ) : chatHistory.length > 0 ? (
          <div className="chat-history-list">
            {chatHistory.map(chat => (
              <div key={chat.id} className="chat-history-item">
                <div className="chat-history-info">
                  <h4>{chat.title}</h4>
                  <p>{chat.preview}</p>
                  <span className="chat-date">{new Date(chat.timestamp).toLocaleDateString()}</span>
                </div>
                <button className="chat-action-btn">
                  <i className="fas fa-eye"></i> View
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <i className="fas fa-comments"></i>
            <p>No chat history available</p>
            <button className="primary-btn" onClick={handleStartChat}>
              Start a Chat
            </button>
          </div>
        )}
      </div>
    );
  };

  const Search = () => {
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState([]);
    const [searchLoading, setSearchLoading] = useState(false);
    
    const handleSearch = async () => {
      if (!searchQuery.trim()) return;
      
      try {
        setSearchLoading(true);
        const response = await axios.get(`${API_BASE_URL}/chats/search?q=${encodeURIComponent(searchQuery)}`);
        setSearchResults(response.data);
      } catch (err) {
        console.error("Error searching chats:", err);
        // Fallback to dummy results
        setSearchResults([
          { id: 1, title: "Search Result 1", preview: "Matching content for '" + searchQuery + "'...", timestamp: new Date() },
          { id: 2, title: "Search Result 2", preview: "Another match for '" + searchQuery + "'...", timestamp: new Date(Date.now() - 86400000) },
        ]);
      } finally {
        setSearchLoading(false);
      }
    };
    
    return (
      <div className="tab-content">
        <h2>Search</h2>
        <div className="search-tab">
          <div className="search-input-container">
            <input 
              type="text" 
              placeholder="Search through your chats..." 
              className="search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button className="search-button" onClick={handleSearch} disabled={searchLoading}>
              {searchLoading ? <div className="loading-spinner small"></div> : <i className="fas fa-search"></i>}
              {searchLoading ? "Searching..." : "Search"}
            </button>
          </div>
        </div>
        
        {searchLoading ? (
          <div className="loading-placeholder">
            <div className="loading-spinner"></div>
            <p>Searching...</p>
          </div>
        ) : searchResults.length > 0 ? (
          <div className="search-results">
            <h3>Search Results ({searchResults.length})</h3>
            {searchResults.map(result => (
              <div key={result.id} className="search-result-item">
                <h4>{result.title}</h4>
                <p>{result.preview}</p>
                <span className="search-date">{new Date(result.timestamp).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        ) : searchQuery && !searchLoading ? (
          <div className="empty-state">
            <i className="fas fa-search"></i>
            <p>No results found for "{searchQuery}"</p>
          </div>
        ) : null}
      </div>
    );
  };

  const AskAnything = () => {
    const [question, setQuestion] = useState("");
    const [answer, setAnswer] = useState("");
    const [askLoading, setAskLoading] = useState(false);
    
    const handleAsk = async () => {
      if (!question.trim()) return;
      
      try {
        setAskLoading(true);
        const response = await axios.post(`${API_BASE_URL}/ask`, {
          question: question
        });
        
        setAnswer(response.data.answer);
        setQuestion("");
      } catch (err) {
        console.error("Error asking question:", err);
        setAnswer("Sorry, there was an error processing your question. Please try again.");
      } finally {
        setAskLoading(false);
      }
    };
    
    return (
      <div className="tab-content">
        <h2>Ask Anything</h2>
        <div className="ask-anything-tab">
          <textarea 
            placeholder="What would you like to ask?" 
            className="question-input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={askLoading}
          ></textarea>
          <button className="ask-button" onClick={handleAsk} disabled={askLoading || !question.trim()}>
            {askLoading ? <div className="loading-spinner small"></div> : <i className="fas fa-paper-plane"></i>}
            {askLoading ? "Processing..." : "Ask"}
          </button>
        </div>
        
        {answer && (
          <div className="answer-container">
            <h3>Answer:</h3>
            <div className="answer-content">
              <p>{answer}</p>
            </div>
          </div>
        )}
      </div>
    );
  };

  const Settings = () => {
    const [settings, setSettings] = useState({
      notifications: true,
      darkMode: false,
      autoSave: true,
      language: 'en'
    });
    const [saveLoading, setSaveLoading] = useState(false);
    const [saveStatus, setSaveStatus] = useState(null);
    
    const saveSettings = async () => {
      try {
        setSaveLoading(true);
        await axios.post(`${API_BASE_URL}/settings`, settings);
        setSaveStatus('success');
        setTimeout(() => setSaveStatus(null), 3000);
      } catch (err) {
        console.error("Error saving settings:", err);
        setSaveStatus('error');
        setTimeout(() => setSaveStatus(null), 3000);
      } finally {
        setSaveLoading(false);
      }
    };
    
    const handleSettingChange = (key, value) => {
      setSettings(prev => ({ ...prev, [key]: value }));
    };
    
    return (
      <div className="tab-content">
        <h2>Settings</h2>
        <div className="settings-options">
          <div className="setting-item">
            <div className="setting-info">
              <h4>Notification Preferences</h4>
              <p>Receive notifications for new messages and updates</p>
            </div>
            <label className="switch">
              <input 
                type="checkbox" 
                checked={settings.notifications}
                onChange={() => handleSettingChange('notifications', !settings.notifications)}
              />
              <span className="slider round"></span>
            </label>
          </div>
          
          <div className="setting-item">
            <div className="setting-info">
              <h4>Dark Mode</h4>
              <p>Toggle dark theme for better night viewing</p>
            </div>
            <label className="switch">
              <input 
                type="checkbox" 
                checked={settings.darkMode}
                onChange={() => handleSettingChange('darkMode', !settings.darkMode)}
              />
              <span className="slider round"></span>
            </label>
          </div>
          
          <div className="setting-item">
            <div className="setting-info">
              <h4>Auto Save Chats</h4>
              <p>Automatically save all chat conversations</p>
            </div>
            <label className="switch">
              <input 
                type="checkbox" 
                checked={settings.autoSave}
                onChange={() => handleSettingChange('autoSave', !settings.autoSave)}
              />
              <span className="slider round"></span>
            </label>
          </div>
          
          <div className="setting-item">
            <div className="setting-info">
              <h4>Language</h4>
              <p>Select your preferred language</p>
            </div>
            <select 
              className="language-select"
              value={settings.language}
              onChange={(e) => handleSettingChange('language', e.target.value)}
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
            </select>
          </div>
          
          <div className="settings-actions">
            <button 
              className="save-settings-btn" 
              onClick={saveSettings}
              disabled={saveLoading}
            >
              {saveLoading ? <div className="loading-spinner small"></div> : 'Save Settings'}
            </button>
            
            {saveStatus === 'success' && (
              <div className="save-status success">
                <i className="fas fa-check-circle"></i>
                Settings saved successfully!
              </div>
            )}
            
            {saveStatus === 'error' && (
              <div className="save-status error">
                <i className="fas fa-exclamation-circle"></i>
                Failed to save settings. Please try again.
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="dashboard">
      {/* Render ChatWindow as a separate page when showChatWindow is true */}
      {showChatWindow ? (
        <div className="chat-window-fullscreen">
          <ChatWindow onClose={handleCloseChat} />
        </div>
      ) : (
        <>
          {/* Sidebar */}
          <div className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>
            <div className="sidebar-header">
              <h2>PersonalAI</h2>
              <button
                className="toggle-sidebar"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
              >
                <i
                  className={`fas ${sidebarOpen ? "fa-chevron-left" : "fa-chevron-right"}`}
                ></i>
              </button>
            </div>

            <ul className="sidebar-menu">
              <li
                className={activeTab === "dashboard" ? "active" : ""}
                onClick={() => setActiveTab("dashboard")}
              >
                <i className="fas fa-home"></i>
                {sidebarOpen && <span>Dashboard</span>}
              </li>
              {/* Removed Chat tab from sidebar */}
              <li
                className={activeTab === "search" ? "active" : ""}
                onClick={() => setActiveTab("search")}
              >
                <i className="fas fa-search"></i>
                {sidebarOpen && <span>Search</span>}
              </li>
              <li
                className={activeTab === "ask" ? "active" : ""}
                onClick={() => setActiveTab("ask")}
              >
                <i className="fas fa-question-circle"></i>
                {sidebarOpen && <span>Ask Anything</span>}
              </li>
              <li
                className={activeTab === "settings" ? "active" : ""}
                onClick={() => setActiveTab("settings")}
              >
                <i className="fas fa-cog"></i>
                {sidebarOpen && <span>Settings</span>}
              </li>
            </ul>

            <div className="sidebar-footer">
              <div className="user-profile">
                <img
                  src="https://ui-avatars.com/api/?name=PKR&background=4a6cfa&color=fff"
                  alt="User"
                />
                {sidebarOpen && (
                  <div>
                    <h4>PKR</h4>
                    <p>Admin</p>
                  </div>
                )}
              </div>
              <button className="logout-btn" onClick={onLogout}>
                <i className="fas fa-sign-out-alt"></i>
                {sidebarOpen && <span>Logout</span>}
              </button>
            </div>
          </div>

          {/* Main Content */}
          <div className="main-content">
            {/* Top Navigation */}
            <div className="top-nav">
              <div className="nav-left">
                <h1>
                  {activeTab === "dashboard"
                    ? "Dashboard"
                    : activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
                </h1>
              </div>
              <div className="nav-right">
                <div className="search-box">
                  <i className="fas fa-search"></i>
                  <input type="text" placeholder="Search..." />
                </div>
                <div className="notifications">
                  <button
                    className="notification-btn"
                    onClick={() => setShowNotifications(!showNotifications)}
                    aria-label="Notifications"
                  >
                    <i className="fas fa-bell"></i>
                    {notifications.length > 0 && (
                      <span className="badge">{notifications.length}</span>
                    )}
                  </button>
                  {showNotifications && (
                    <div className="notifications-dropdown">
                      <div className="notifications-header">
                        <h4>Notifications</h4>
                        <button 
                          className="mark-all-read"
                          onClick={() => setShowNotifications(false)}
                        >
                          Mark all as read
                        </button>
                      </div>
                      {notifications.length > 0 ? (
                        notifications.map((note) => (
                          <div key={note.id} className="notification-item">
                            <div className="notification-icon">
                              <i className="fas fa-bell"></i>
                            </div>
                            <div className="notification-content">
                              <p>{note.message}</p>
                              <span>{note.time}</span>
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="no-notifications">No new notifications</p>
                      )}
                    </div>
                  )}
                </div>
                <div className="user-menu">
                  <img
                    src="https://ui-avatars.com/api/?name=PKR&background=4a6cfa&color=fff"
                    alt="User"
                  />
                </div>
              </div>
            </div>

            {/* Dynamic Content Rendering */}
            <div className="content">
              {activeTab === "dashboard" && <DashboardHome />}
              {activeTab === "chats" && <ChatHistory />}
              {activeTab === "search" && <Search />}
              {activeTab === "ask" && <AskAnything />}
              {activeTab === "settings" && <Settings />}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;