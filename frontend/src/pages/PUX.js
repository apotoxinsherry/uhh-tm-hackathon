import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "../styles/PUX.css";

function PUX() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  // Load chat history when component mounts
  useEffect(() => {
    loadChatHistory();
    scrollToBottom();
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Scroll to the bottom of the chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Load saved chat history from localStorage
  const loadChatHistory = () => {
    try {
      const savedChat = localStorage.getItem("pux-chat");
      if (savedChat) {
        setMessages(JSON.parse(savedChat));
      } else {
        // Initialize with a welcome message if no history exists
        setMessages([
          {
            type: "bot",
            content: "Greetings! I’m InsightBuilder, here to help you transform meeting notes, technical shorthand, or full transcripts into detailed, easy-to-understand content. I’ll break down complex terms, add context, and provide clarity, so you can easily grasp the key insights. Let’s get started!",
            timestamp: new Date().toISOString()
          }
        ]);
      }
    } catch (err) {
      console.error("Error loading chat history:", err);
    }
  };

  // Save chat history to localStorage
  const saveChatHistory = (updatedMessages) => {
    try {
      localStorage.setItem("pux-chat", JSON.stringify(updatedMessages));
    } catch (err) {
      console.error("Error saving chat history:", err);
    }
  };

  // Handle sending a message
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    // Create user message
    const userMessage = {
      type: "user",
      content: input,
      timestamp: new Date().toISOString()
    };
    
    // Update state with user message
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    saveChatHistory(updatedMessages);
    
    // Clear input field
    setInput("");
    
    // Set loading state
    setIsLoading(true);
    
    try {
      // Send request to backend API
      const response = await axios.post("http://localhost:8000/users/user2/notes/note1/pux", {
        query: input
      });
      
      // Process response from backend
      const botMessage = {
        type: "bot",
        content: response.data.answer || "I'm sorry, I couldn't process your request.",
        timestamp: new Date().toISOString()
      };
      
      // Update state with bot response
      const finalMessages = [...updatedMessages, botMessage];
      setMessages(finalMessages);
      saveChatHistory(finalMessages);
    } catch (err) {
      console.error("Error getting response from tutor API:", err);
      
      // Create error message
      const errorMessage = {
        type: "bot",
        content: "Sorry, I encountered an error processing your request. Please try again later.",
        timestamp: new Date().toISOString(),
        isError: true
      };
      
      // Update state with error message
      const finalMessages = [...updatedMessages, errorMessage];
      setMessages(finalMessages);
      saveChatHistory(finalMessages);
    } finally {
      setIsLoading(false);
    }
  };

  // Format timestamp for display
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Clear chat history
  const clearChat = () => {
    const confirmClear = window.confirm("Are you sure you want to clear the chat history?");
    if (confirmClear) {
      const welcomeMessage = [
        {
          type: "bot",
          content: "Greetings! I’m InsightBuilder, here to help you transform meeting notes, technical shorthand, or full transcripts into detailed, easy-to-understand content. I’ll break down complex terms, add context, and provide clarity, so you can easily grasp the key insights. Let’s get started!",
          timestamp: new Date().toISOString()
        }
      ];
      setMessages(welcomeMessage);
      saveChatHistory(welcomeMessage);
    }
  };

  return (
    <div className="tutor-container">
      <div className="tutor-header">
        <h1>InsightBuilder</h1>
        <div className="tutor-actions">
          <button className="clear-button" onClick={clearChat}>
            Clear Chat
          </button>
          <button className="home-button" onClick={() => navigate("/")}>
            <span className="button-icon">🏠</span>
            Home
          </button>
        </div>
      </div>

      <div className="messages-container">
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`message ${message.type} ${message.isError ? 'error' : ''}`}
          >
            <div className="message-content">
              <div className="message-avatar">
                {message.type === "bot" ? "🤖" : "👤"}
              </div>
              <div className="message-bubble">
                <div className="message-text">{message.content}</div>
                <div className="message-time">{formatTime(message.timestamp)}</div>
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message bot">
            <div className="message-content">
              <div className="message-avatar">🤖</div>
              <div className="message-bubble loading">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={isLoading}
          className="message-input"
        />
        <button 
          type="submit" 
          disabled={isLoading || !input.trim()} 
          className="send-button"
        >
          <span className="send-icon">➤</span>
        </button>
      </form>
    </div>
  );
}

export default PUX;