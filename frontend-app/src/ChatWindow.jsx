import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Moon, Sun, Mic, MicOff, User, Search, Image, 
  Paperclip, Send, ChevronDown, Settings, Upload, 
  LogOut, Maximize, Minimize, X, Loader 
} from 'lucide-react';
import Dashboard from './Dashboard';
import './ChatWindow.css';

const ChatWindow = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [darkMode, setDarkMode] = useState(true);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [transcript, setTranscript] = useState("");
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const ws = useRef(null); // WebSocket reference

  const [prevChats, setPrevChats] = useState([
    {
      role: "assistant",
      content: "Hello! I'm your AI assistant. How can I help you today?",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    }
  ]);

  // --- Initialize WebSocket connection ---
  useEffect(() => {
    ws.current = new WebSocket("ws://localhost:8000/ws");

    ws.current.onopen = () => {
      console.log("✅ Connected to backend WebSocket");
    };

    ws.current.onmessage = (event) => {
      const aiResponse = event.data;
      const assistantMessage = {
        role: "assistant",
        content: aiResponse,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
      setPrevChats((prev) => [...prev, assistantMessage]);
      setLoading(false);
    };

    ws.current.onerror = (err) => {
      console.error("❌ WebSocket error:", err);
    };

    ws.current.onclose = () => {
      console.log("⚠️ WebSocket closed");
    };

    return () => {
      ws.current.close();
    };
  }, []);

  // --- Speech Recognition Setup ---
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      
      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0])
          .map(result => result.transcript)
          .join('');
        setTranscript(transcript);
      };
      
      recognition.onend = () => {
        if (transcript) {
          setPrompt(transcript);
          setTranscript("");
        }
        setIsRecording(false);
      };
      
      setRecognition(recognition);
    } else {
      console.warn("Speech recognition not supported in this browser");
    }
  }, [transcript]);

  // --- Auto-scroll to bottom ---
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [prevChats]);

  // --- Dark Mode ---
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  // --- Fullscreen toggle ---
  useEffect(() => {
    const handleFullScreenChange = () => {
      setIsFullScreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullScreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullScreenChange);
    };
  }, []);

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      chatContainerRef.current.requestFullscreen().catch(err => {
        console.error(`Error attempting to enable full-screen mode: ${err.message}`);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      recognition.stop();
    } else {
      setTranscript("");
      recognition.start();
      setIsRecording(true);
    }
  };

  const navigateToDashboard = useCallback(() => {
    navigate('/dashboard');
  }, [navigate]);

  const handleLogout = () => {
    onLogout();
    navigate('/');
  };

  // --- Send user message + get AI reply from backend ---
  const getReply = useCallback(() => {
    if (!prompt.trim() || loading) return;

    const userMessage = {
      role: "user",
      content: prompt,
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setPrevChats((prev) => [...prev, userMessage]);
    setPrompt("");
    setLoading(true);

    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ text: userMessage.content }));
    } else {
      console.error("⚠️ WebSocket not connected");
      setLoading(false);
    }
  }, [prompt, loading]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      getReply();
    }
  };

  return (
    <div 
      ref={chatContainerRef}
      className={`chat-container ${darkMode ? 'dark' : 'light'} ${isFullScreen ? 'fullscreen' : ''}`}
    >
      <div className="header">
        <div className="logo-container" onClick={navigateToDashboard} style={{cursor: 'pointer'}}>
          <div className="logo">AI</div>
          <div className="app-name">AI Assistant</div>
        </div>
        <div className="header-icons">
          <button 
            className="icon-btn" 
            onClick={() => setDarkMode(!darkMode)}
            aria-label="Toggle dark mode"
          >
            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          <button 
            className="icon-btn" 
            onClick={() => setIsHistoryOpen(!isHistoryOpen)}
            aria-label="Search history"
          >
            <Search size={20} />
          </button>
          <button 
            className="icon-btn" 
            onClick={toggleFullScreen}
            aria-label="Toggle full screen"
          >
            {isFullScreen ? <Minimize size={20} /> : <Maximize size={20} />}
          </button>
          <button 
            className="icon-btn" 
            onClick={() => setIsOpen(!isOpen)}
            aria-label="User menu"
          >
            <User size={20} />
          </button>
        </div>
        
        {/* User dropdown */}
        {isOpen && (
          <div className="dropdown-menu">
            <div className="dropdown-item">
              <Settings size={16} />
              <span>Settings</span>
            </div>
            <div className="dropdown-item">
              <Upload size={16} />
              <span>Upgrade</span>
            </div>
            <div className="dropdown-item" onClick={handleLogout}>
              <LogOut size={16} />
              <span>Log out</span>
            </div>
          </div>
        )}
        
        {/* History dropdown */}
        {isHistoryOpen && (
          <div className="dropdown-menu history-dropdown">
            <div className="dropdown-header">
              <span>Chat History</span>
              <button 
                className="icon-btn"
                onClick={() => setIsHistoryOpen(false)}
                aria-label="Close history"
              >
                <X size={16} />
              </button>
            </div>
            <div className="history-list">
              {prevChats.length === 0 ? (
                <div className="empty-history">No chat history yet</div>
              ) : (
                prevChats.map((chat, index) => (
                  <div key={index} className="history-item">
                    <div className="history-content">
                      <strong>{chat.role === "user" ? "You" : "AI"}:</strong> {chat.content}
                    </div>
                    <div className="history-time">{chat.timestamp}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
      
      <div className="chat-area">
        {prevChats.map((chat, index) => (
          <div 
            key={index} 
            className={`message ${chat.role === 'assistant' ? 'ai-message' : 'user-message'}`}
          >
            <div className="message-content">{chat.content}</div>
            <div className="message-time">{chat.timestamp}</div>
          </div>
        ))}
        {loading && (
          <div className="message ai-message">
            <div className="message-content">
              <Loader size={16} className="thinking-animation" /> Thinking...
            </div>
            <div className="message-time">
              {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </div>
          </div>
        )}
        {isRecording && (
          <div className="message ai-message">
            <div className="message-content">
              <div className="recording-indicator">
                <span className="pulse"></span>
                Listening... {transcript && `"${transcript}"`}
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="input-area">
        <div className="input-container">
          <input
            type="text"
            className="input-field"
            placeholder="Ask anything..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <div className="input-actions">
            <button className="icon-btn" aria-label="Attach image">
              <Image size={20} />
            </button>
            <button className="icon-btn" aria-label="Attach file">
              <Paperclip size={20} />
            </button>
            <button 
              className={`icon-btn ${isRecording ? 'recording' : ''}`}
              onClick={toggleRecording}
              disabled={!recognition}
              aria-label={isRecording ? "Stop recording" : "Start voice search"}
            >
              {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
            <button 
              className="action-btn" 
              onClick={getReply}
              disabled={loading || !prompt.trim()}
              aria-label="Send message"
            >
              {loading ? <Loader size={20} className="spin" /> : <Send size={20} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;
