import { createContext, useState, useEffect } from "react";

export const MyContext = createContext();

export function MyProvider({ children }) {
  const [prevChats, setPrevChats] = useState([]);

  // ✅ Load history when app starts
  useEffect(() => {
    const savedChats = localStorage.getItem("chatHistory");
    if (savedChats) {
      setPrevChats(JSON.parse(savedChats));
    }
  }, []);

  // ✅ Save history whenever chats change
  useEffect(() => {
    if (prevChats.length > 0) {
      localStorage.setItem("chatHistory", JSON.stringify(prevChats));
    }
  }, [prevChats]);

  // ✅ Function to add a new message
  const addMessage = (role, content) => {
    const newMsg = {
      role, // "user" or "assistant"
      content,
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };
    setPrevChats((prev) => [...prev, newMsg]);
  };

  return (
    <MyContext.Provider value={{ prevChats, addMessage, setPrevChats }}>
      {children}
    </MyContext.Provider>
  );
}
