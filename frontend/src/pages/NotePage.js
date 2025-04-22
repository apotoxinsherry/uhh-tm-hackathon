import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import "../styles/NotePage.css";

function NotePage() {
  const { id } = useParams();
  const [inputs, setInputs] = useState([{ 
    tag: "", 
    topic: "", 
    content: "", 
    response: "",
    contextLevel: 3, // Default context level
    includeDiagram: false, // Default diagram setting
    showExcalidraw: false // Control Excalidraw visibility for this section
  }]);
  const navigate = useNavigate();

  // Handle change in topic, tag, or content fields
  const handleChange = (index, field, value) => {
    const newInputs = [...inputs];
    newInputs[index][field] = value;
    setInputs(newInputs);
  };

  // Handle submit action to fetch response
  const handleSubmit = async (index) => {
    const { tag, topic, content, contextLevel, includeDiagram } = inputs[index];
    try {
      // Send contextLevel and includeDiagram to backend
      const res = await axios.post("http://localhost:8000/users/user1/notes/note1/ask", { 
        query: content,
        contextLevel: contextLevel,
        includeDiagram: includeDiagram
      });
      
      const newInputs = [...inputs];
      newInputs[index].response = res.data.answer || "Dummy Response"; // For now
      console.log("Response:", res);
      setInputs(newInputs);
      
      // Automatically add a new section after generating a response
      if (index === inputs.length - 1) {
        addNewInput();
      }
    } catch (err) {
      console.error("Error:", err);
      // Show error message or fallback response
      const newInputs = [...inputs];
      newInputs[index].response = "Failed to generate response. Please try again.";
      setInputs(newInputs);
    }
  };

  // Add a new input box
  const addNewInput = () => {
    setInputs([
      ...inputs, 
      { 
        tag: "", 
        topic: "", 
        content: "", 
        response: "", 
        contextLevel: 3, 
        includeDiagram: false,
        showExcalidraw: false
      }
    ]);
  };

  // Toggle Excalidraw iframe visibility for a specific section
  const toggleExcalidraw = (index) => {
    const newInputs = [...inputs];
    newInputs[index].showExcalidraw = !newInputs[index].showExcalidraw;
    setInputs(newInputs);
  };

  return (
    <div className="note-page">
      <div className="note-header">
        <h1>Note #{id}</h1>
        <div className="navigation-buttons">
          <button className="nav-button" onClick={() => navigate("/")}>
            <span className="button-icon">🏠</span>
            Home
          </button>
          <button className="nav-button" onClick={() => navigate("/pux")}>
            <span className="button-icon">📊</span>
            PUX
          </button>
          <button className="nav-button" onClick={() => navigate("/tutor")}>
            <span className="button-icon">📝</span>
            TUTOR
          </button>
        </div>
      </div>

      {inputs.map((input, index) => (
        <div key={index} className="input-section">
          <div className="input-container">
            <div className="input-fields">
              <div className="input-row">
                <div className="input-field">
                  <label>Topic</label>
                  <input
                    type="text"
                    placeholder="Enter Topic"
                    value={input.topic}
                    onChange={(e) => handleChange(index, "topic", e.target.value)}
                  />
                </div>
                <div className="input-field">
                  <label>Tag</label>
                  <input
                    type="text"
                    placeholder="Enter Tag"
                    value={input.tag}
                    onChange={(e) => handleChange(index, "tag", e.target.value)}
                  />
                </div>
              </div>
              
              <div className="advanced-options">
                <div className="context-level-container">
                  <label htmlFor={`context-level-${index}`}>
                    Context Level: {input.contextLevel}
                  </label>
                  <input
                    id={`context-level-${index}`}
                    type="range"
                    min="1"
                    max="5"
                    value={input.contextLevel}
                    onChange={(e) => handleChange(index, "contextLevel", parseInt(e.target.value))}
                    className="context-slider"
                  />
                  <span className="slider-value">{input.contextLevel}</span>
                </div>
                
                <div className="diagram-checkbox-container">
                  <input
                    id={`include-diagram-${index}`}
                    type="checkbox"
                    checked={input.includeDiagram}
                    onChange={(e) => handleChange(index, "includeDiagram", e.target.checked)}
                    className="diagram-checkbox"
                  />
                  <label htmlFor={`include-diagram-${index}`} className="checkbox-label">
                    Include Diagrams in Response
                  </label>
                </div>
              </div>
              
              <div className="content-field">
                <label>Content</label>
                <textarea
                  placeholder="Enter your content here..."
                  value={input.content}
                  onChange={(e) => handleChange(index, "content", e.target.value)}
                />
              </div>
              
              <div className="button-container">
              <button
                  className="draw-button"
                  onClick={() => toggleExcalidraw(index)}
                >
                  <span className="button-icon">✏️</span>
                  {input.showExcalidraw ? "Close Drawing Tool" : "Draw"}
                </button>
                <button
                  className="generate-button"
                  onClick={() => handleSubmit(index)}
                >
                  Generate Response
                </button>
                
              </div>
              
              {/* Embed Excalidraw directly below the content area when toggled */}
              {input.showExcalidraw && (
                <div className="section-excalidraw-container">
                  <div className="excalidraw-header">
                    <h3>Drawing Tool</h3>
                    <button className="close-button" onClick={() => toggleExcalidraw(index)}>Close</button>
                  </div>
                  <iframe 
                    src="https://excalidraw.com/"
                    title="Excalidraw Drawing Tool"
                    className="excalidraw-frame"
                    allowFullScreen
                  />
                </div>
              )}
            </div>
          </div>

          {input.response && (
            <div className="response-container">
              <label>Response</label>
              <div className="markdown-response">
                <ReactMarkdown>{input.response}</ReactMarkdown>
              </div>
              <div className="response-actions">
                <button 
                  className="view-raw-button"
                  onClick={() => {
                    const newInputs = [...inputs];
                    newInputs[index].showRaw = !newInputs[index].showRaw;
                    setInputs(newInputs);
                  }}
                >
                  {input.showRaw ? "View Rendered" : "View Raw"}
                </button>
                {/* <button 
                  className="draw-button" 
                  onClick={() => toggleExcalidraw(index)}
                >
                  <span className="button-icon">✏️</span>
                  {input.showExcalidraw ? "Close Drawing Tool" : "Draw Diagram"}
                </button> */}
              </div>
              {input.showRaw && (
                <textarea
                  value={input.response}
                  readOnly
                  className="response-text"
                />
              )}
            </div>
          )}
        </div>
      ))}

      <div className="add-section-container">
        <button className="add-section-button" onClick={addNewInput}>
          Add New Section
        </button>
      </div>
    </div>
  );
}

export default NotePage;