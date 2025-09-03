import { useContext } from "react";
import { MyContext } from "./MyContext.jsx";
import "./Chat.css";

function Chat() {
  const { prevChats, setPrevChats } = useContext(MyContext);

  const handleDelete = (index) => {
    setPrevChats((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="chatMessages">
      {prevChats.map((msg, index) => (
        <div
          key={index}
          className={`chatRow ${msg.role === "user" ? "user-row" : "assistant-row"}`}
        >
          <div className={`chatBubble ${msg.role}-bubble`}>
            <p>{msg.content}</p>
            <span className="timestamp">
              {msg.timestamp ??
                new Date().toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
            </span>
            <button
              className="delete-btn"
              onClick={() => handleDelete(index)}
              title="Delete message"
            >
              🗑️
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export default Chat;