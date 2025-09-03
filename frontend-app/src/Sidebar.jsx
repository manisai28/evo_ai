import "./Sidebar.css";
import { useContext, useEffect, useState } from "react";
import { MyContext } from "./MyContext.jsx";
import { v1 as uuidv1 } from "uuid";

function Sidebar() {
    const { allThreads, setAllThreads, currThreadId, setNewChat, setPrompt, setReply, setCurrThreadId, setPrevChats } = useContext(MyContext);

    const [searchQuery, setSearchQuery] = useState(""); // 🔍 State for search input
    const API_BASE = import.meta.env.VITE_API_URL;

    const getAllThreads = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/thread`);
            const res = await response.json();

            const filteredData = res.map(thread => ({
                threadId: thread.threadId,
                title: thread.title || "Untitled Chat", // ✅ Ensure title is always a string
            }));

            setAllThreads(filteredData);
        } catch (err) {
            console.log("Error fetching threads:", err);
        }
    };

    useEffect(() => {
        getAllThreads();
    }, [currThreadId]);

    const createNewChat = () => {
        setNewChat(true);
        setPrompt("");
        setReply(null);
        setCurrThreadId(uuidv1());
        setPrevChats([]);
    };

    const changeThread = async (newThreadId) => {
        setCurrThreadId(newThreadId);
        try {
            const response = await fetch(`${API_BASE}/api/thread/${newThreadId}`);
            const res = await response.json();

            if (Array.isArray(res)) {
                setPrevChats(res);
            } else {
                setPrevChats([]);
            }

            setNewChat(false);
            setReply(null);
        } catch (err) {
            console.log("Error loading thread:", err);
        }
    };

    const deleteThread = async (threadId) => {
        try {
            const response = await fetch(`${API_BASE}/api/thread/${threadId}`, { method: "DELETE" });
            const res = await response.json();
            console.log(res);

            setAllThreads(prev => prev.filter(thread => thread.threadId !== threadId));
            if (threadId === currThreadId) {
                createNewChat();
            }
        } catch (err) {
            console.log(err);
        }
    };

    return (
        <div className="sidebar">
            {/* Logo + New Chat + Search */}
            <div className="sidebar-header">
                <div className="logo-container">
                    <img src="src/new.jpg" alt="AI Logo" className="logo-img" />
                </div>

                <button className="new-chat-btn" onClick={createNewChat}>
                    <i className="fa-solid fa-plus"></i>
                    <span>New Chat</span>
                </button>

                {/* 🔍 Search Bar */}
                <div className="search-container">
                    <i className="fas fa-search search-icon"></i>
                    <input
                        type="text"
                        className="search-input"
                        placeholder="Search chats..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </div>

            {/* 💬 Chat History */}
            <div className="history-section">
                {allThreads
                    ?.filter(thread =>
                        (thread.title || "").toLowerCase().includes(searchQuery.toLowerCase()) // ✅ Safe filter
                    )
                    .map((thread, idx) => (
                        <div
                            key={idx}
                            className={`thread-item ${currThreadId === thread.threadId ? 'highlighted' : ''}`}
                            onClick={() => changeThread(thread.threadId)}
                        >
                            <i className="fa-regular fa-comments icon"></i>
                            <span className="thread-title" title={thread.title}>{thread.title}</span>
                            <i
                                className="fa-solid fa-trash"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    deleteThread(thread.threadId);
                                }}
                            ></i>
                        </div>
                    ))}
            </div>

            {/* Footer */}
            <div className="sign">
                Done by PKR
            </div>
        </div>
    );
}

export default Sidebar;
