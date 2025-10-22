import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Moon, Sun, Mic, MicOff, User, Search, Image, Paperclip,
  Send, ChevronDown, Settings, Upload, LogOut, Maximize,
  Minimize, X, Loader
} from 'lucide-react';
import './ChatWindow.css';

const ChatWindow = ({ user, onLogout, onChatUpdate }) => {
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
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const ws = useRef(null);
  const messageQueue = useRef([]);
  const isProcessing = useRef(false);

  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [prevChats, setPrevChats] = useState([
    {
      role: "assistant",
      content: "Hello! I'm your AI assistant. How can I help you today?",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    }
  ]);

  // Generate unique session ID
  const generateSessionId = () => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  // Save chats to localStorage and notify parent component
  const saveChatSession = useCallback((sessionId, chats, isNewSession = false) => {
    if (chats.length === 0) return;

    const lastUserMessage = chats.filter(chat => chat.role === 'user').pop();
    const chatTitle = lastUserMessage ? 
      lastUserMessage.content.substring(0, 30) + (lastUserMessage.content.length > 30 ? '...' : '') : 
      'New Chat';
    
    const chatSession = {
      id: sessionId,
      title: chatTitle,
      messages: chats,
      lastUpdated: new Date().toISOString(),
      preview: lastUserMessage?.content || 'New conversation',
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      messageCount: chats.length
    };
    
    const chatSessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
    
    if (isNewSession) {
      chatSessions.unshift(chatSession);
    } else {
      const existingIndex = chatSessions.findIndex(session => session.id === sessionId);
      if (existingIndex !== -1) {
        chatSessions[existingIndex] = chatSession;
      } else {
        chatSessions.unshift(chatSession);
      }
    }
    
    const limitedSessions = chatSessions.slice(0, 50);
    localStorage.setItem('chatSessions', JSON.stringify(limitedSessions));
    
    if (onChatUpdate) {
      onChatUpdate(limitedSessions);
    }

    return limitedSessions;
  }, [onChatUpdate]);

  // Load chat sessions from localStorage
  const loadChatSessions = useCallback(() => {
    const savedSessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
    
    if (savedSessions.length === 0) {
      const newSessionId = generateSessionId();
      setCurrentSessionId(newSessionId);
      const initialChats = [
        {
          role: "assistant",
          content: "Hello! I'm your AI assistant. How can I help you today?",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
        }
      ];
      saveChatSession(newSessionId, initialChats, true);
      setPrevChats(initialChats);
    } else {
      const mostRecentSession = savedSessions[0];
      setCurrentSessionId(mostRecentSession.id);
      setPrevChats(mostRecentSession.messages || []);
    }
    
    return savedSessions;
  }, [saveChatSession]);

  // Add this function to check for reminders
 // Add this function to check for reminders
const checkForReminders = useCallback(async () => {
  const userId = user?.id || "user123";
  console.log("🔄 checkForReminders called for user:", userId);
  
  try {
    console.log("🌐 Making API request...");
    const response = await fetch(`http://localhost:8000/check-reminders/${userId}`);
    console.log("📡 API Response status:", response.status);
    
    const data = await response.json();
    console.log("📊 Reminder check response:", data);
    
    if (data.has_reminder) {
      console.log("🔔 Found reminder:", data.message);
      
      // Add the reminder to chat messages
      const reminderMessage = {
        role: "assistant",
        content: data.message,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      
      console.log("💬 Adding reminder to chat...");
      setPrevChats(prev => {
        const newChats = [...prev, reminderMessage];
        saveChatSession(currentSessionId, newChats, false);
        return newChats;
      });
      
      // Mark reminder as read in backend
      console.log("📝 Marking reminder as read...");
      await fetch(`http://localhost:8000/mark-reminder-read/${userId}`, {
        method: 'POST'
      });
      
      console.log("✅ Reminder displayed and marked as read");
    } else {
      console.log("ℹ️ No reminders found");
    }
  } catch (error) {
    console.error('❌ Error checking reminders:', error);
  }
}, [user, currentSessionId, saveChatSession]);

// In your message rendering, replace or modify the message content rendering:
const renderMessageContent = (content) => {
  // Check if message contains YouTube embed
  if (content.includes('youtube.com/embed') || content.includes('youtu.be')) {
    return (
      <div 
        className="music-message"
        dangerouslySetInnerHTML={{ __html: content }} 
      />
    );
  }
  
  // Check if message contains YouTube iframe
  const iframeMatch = content.match(/<iframe[^>]*src="[^"]*youtube[^"]*"[^>]*><\/iframe>/);
  if (iframeMatch) {
    return (
      <div 
        className="youtube-embed"
        dangerouslySetInnerHTML={{ __html: iframeMatch[0] }} 
      />
    );
  }
  
  return content;
};

// Then in your message mapping:
{prevChats.map((chat, index) => (
  <div 
    key={index} 
    className={`message ${chat.role === 'assistant' ? 'ai-message' : 'user-message'}`}
  >
    <div className="message-content">
      {renderMessageContent(chat.content)}
    </div>
    <div className="message-time">{chat.timestamp}</div>
  </div>
))}

  // SINGLE WebSocket connection - FIXED VERSION
  useEffect(() => {
    // Only create WebSocket if it doesn't exist or is closed
    if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
      console.log("✅ WebSocket already exists, reusing connection");
      return;
    }

    console.log("🔄 Creating WebSocket connection...");
    ws.current = new WebSocket("ws://localhost:8000/ws");

    ws.current.onopen = () => {
      console.log("✅ Connected to backend WebSocket");
      setIsConnected(true);
      
      // Process any queued messages
      if (messageQueue.current.length > 0) {
        console.log(`📤 Processing ${messageQueue.current.length} queued messages`);
        messageQueue.current.forEach(message => {
          if (ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(message));
          }
        });
        messageQueue.current = [];
      }
    };

    ws.current.onmessage = (event) => {
      console.log("📥 Received WebSocket message:", event.data);
      
      try {
        let aiResponse;
        // Try to parse as JSON first
        try {
          const response = JSON.parse(event.data);
          aiResponse = response.response || response.message || response.text || event.data;
        } catch {
          // If parsing fails, use the raw data
          aiResponse = event.data;
        }

        const assistantMessage = {
          role: "assistant",
          content: aiResponse,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        
        setPrevChats((prev) => {
          const newChats = [...prev, assistantMessage];
          saveChatSession(currentSessionId, newChats, false);
          return newChats;
        });
        
      } catch (e) {
        console.error("❌ Error processing WebSocket message:", e);
        const assistantMessage = {
          role: "assistant",
          content: "I received your message! How can I help you?",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setPrevChats((prev) => {
          const newChats = [...prev, assistantMessage];
          saveChatSession(currentSessionId, newChats, false);
          return newChats;
        });
      }
      
      setLoading(false);
      isProcessing.current = false;
    };

    ws.current.onerror = (err) => {
      console.error("❌ WebSocket error:", err);
      setIsConnected(false);
      setLoading(false);
      isProcessing.current = false;
    };

    ws.current.onclose = (event) => {
      console.log("⚠️ WebSocket closed:", event.code, event.reason);
      setIsConnected(false);
      setLoading(false);
      isProcessing.current = false;
      
      // Auto-reconnect after 3 seconds
      setTimeout(() => {
        if (!ws.current || ws.current.readyState === WebSocket.CLOSED) {
          console.log("🔄 Attempting to reconnect WebSocket...");
          setIsConnected(false);
          // Force reconnection by updating state
          setPrevChats(prev => [...prev]);
        }
      }, 3000);
    };

    return () => {
      // Cleanup on component unmount
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.close();
      }
    };
  }, [saveChatSession, currentSessionId]);

  // Reminder polling effect - FIXED VERSION
useEffect(() => {
  console.log("🎯 POLLING EFFECT: Checking if user exists", user);
  
  const userId = user?.id || "user123";
  console.log("⏰ Starting reminder polling for user:", userId);
  
  // Check immediately
  console.log("🔄 Initial reminder check");
  checkForReminders();
  
  // Check every 5 seconds (more frequent for testing)
  const interval = setInterval(() => {
    console.log("⏰ Polling interval triggered");
    checkForReminders();
  }, 10000);
  
  return () => {
    console.log("⏰ Stopping reminder polling");
    clearInterval(interval);
  };
}, [user, checkForReminders]); // Include both dependencies

  // Speech Recognition Setup
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = 'en-US';

      recognitionInstance.onresult = (event) => {
        const transcriptText = Array.from(event.results)
          .map(result => result[0])
          .map(result => result.transcript)
          .join('');
        setTranscript(transcriptText);
      };

      recognitionInstance.onend = () => {
        if (transcript) {
          setPrompt(transcript);
          setTranscript("");
        }
        setIsRecording(false);
      };

      recognitionInstance.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsRecording(false);
      };

      setRecognition(recognitionInstance);
    } else {
      console.warn("Speech recognition not supported in this browser");
    }
  }, []);

  // Load existing chats on component mount
  useEffect(() => {
    loadChatSessions();
  }, [loadChatSessions]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [prevChats]);

  // Dark Mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  // Fullscreen toggle
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
      chatContainerRef.current?.requestFullscreen?.().catch(err => {
        console.error(`Error attempting to enable full-screen mode: ${err.message}`);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  const toggleRecording = () => {
    if (!recognition) return;
    
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

  // Start a new chat session
  const startNewChat = () => {
    const newSessionId = generateSessionId();
    const newChats = [
      {
        role: "assistant",
        content: "Hello! I'm your AI assistant. How can I help you today?",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      }
    ];
    
    setCurrentSessionId(newSessionId);
    setPrevChats(newChats);
    setPrompt("");
    
    saveChatSession(newSessionId, newChats, true);
  };

  // Load a specific chat session
  const loadChatSession = (sessionId) => {
    const chatSessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
    const session = chatSessions.find(s => s.id === sessionId);
    
    if (session) {
      setCurrentSessionId(sessionId);
      setPrevChats(session.messages || []);
      setIsHistoryOpen(false);
    }
  };

  // Send user message + get AI reply - IMPROVED VERSION
  const getReply = useCallback(() => {
    if (!prompt.trim() || loading || isProcessing.current) return;

    const userMessage = {
      role: "user",
      content: prompt,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const newChats = [...prevChats, userMessage];
    setPrevChats(newChats);
    setPrompt("");
    setLoading(true);
    isProcessing.current = true;

    saveChatSession(currentSessionId, newChats, false);

    const messageData = {
      text: prompt,
      user_id: user?.id || "user123",
      session_id: currentSessionId,
      timestamp: new Date().toISOString()
    };

    console.log("📤 Sending message to backend:", messageData);

    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify(messageData));
        console.log("✅ Message sent successfully via WebSocket");
      } catch (error) {
        console.error("❌ Error sending message:", error);
        handleSendError();
      }
    } else {
      console.log("⏳ WebSocket not ready, queuing message");
      messageQueue.current.push(messageData);
      
      // Show waiting message
      setTimeout(() => {
        if (isProcessing.current) {
          const waitingMessage = {
            role: "assistant",
            content: "🔄 Connecting to AI service... Please wait a moment",
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          };
          setPrevChats(prev => {
            const updatedChats = [...prev, waitingMessage];
            saveChatSession(currentSessionId, updatedChats, false);
            return updatedChats;
          });
          setLoading(false);
          isProcessing.current = false;
        }
      }, 2000);
    }
  }, [prompt, loading, prevChats, saveChatSession, currentSessionId, user]);

  const handleSendError = () => {
    const errorMessage = {
      role: "assistant",
      content: "Sorry, I'm having trouble connecting to the AI service. Please check your connection and try again.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setPrevChats(prev => {
      const updatedChats = [...prev, errorMessage];
      saveChatSession(currentSessionId, updatedChats, false);
      return updatedChats;
    });
    setLoading(false);
    isProcessing.current = false;
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      getReply();
    }
  };

  // Get all chat sessions for history dropdown
  const getAllChatSessions = () => {
    return JSON.parse(localStorage.getItem('chatSessions') || '[]');
  };

  return (
    <div 
      ref={chatContainerRef}
      className={`chat-container ${darkMode ? 'dark' : 'light'} ${isFullScreen ? 'fullscreen' : ''}`}
    >
      <div className="header">
        <div className="logo-container" onClick={navigateToDashboard} style={{cursor: 'pointer'}}>
          <div className="logo">AI</div>
          <div className="app-name">EVO AI</div>
        </div>
        
        <div className="header-actions">
          <button 
            className="icon-btn new-chat-btn"
            onClick={startNewChat}
            aria-label="Start new chat"
          >
            <span>+ New Chat</span>
          </button>
          
          {/* Connection Status */}
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </div>
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
              {getAllChatSessions().length === 0 ? (
                <div className="empty-history">No chat history yet</div>
              ) : (
                getAllChatSessions().map((session, index) => (
                  <div 
                    key={session.id} 
                    className={`history-item ${session.id === currentSessionId ? 'active' : ''}`}
                    onClick={() => loadChatSession(session.id)}
                  >
                    <div className="history-content">
                      <strong>{session.title}</strong>
                      <p className="history-preview">{session.preview}</p>
                    </div>
                    <div className="history-time">{session.timestamp}</div>
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