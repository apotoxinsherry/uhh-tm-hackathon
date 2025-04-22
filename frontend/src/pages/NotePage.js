import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import "../styles/NotePage.css";

function NotePage() {
  const { id } = useParams();
  let num = parseInt(id, 10)+1;
  const [inputs, setInputs] = useState([{ 
    tag: "", 
    topic: "", 
    content: "", 
    response: "",
    contextLevel: 3, // Default context level
    includeDiagram: false, // Default diagram setting
    showExcalidraw: false, // Control Excalidraw visibility for this section
    isEditing: false, // Control whether response is in edit mode
    editedResponse: "" // Store edited response text
  }]);
  const navigate = useNavigate();

  // Load saved data when the component mounts
  useEffect(() => {
    loadSavedData();
  }, [id]);

  // Load saved data from localStorage or backend
  const loadSavedData = () => {
    try {
      const savedData = localStorage.getItem(`note-${id}`);
      if (savedData) {
        setInputs(JSON.parse(savedData));
      }
    } catch (err) {
      console.error("Error loading saved data:", err);
    }
  };

  // Save note data to localStorage and potentially to backend
  const saveData = async () => {
    try {
      // First, save any section that's currently being edited
      const updatedInputs = [...inputs];
      updatedInputs.forEach((input, index) => {
        if (input.isEditing) {
          updatedInputs[index].response = updatedInputs[index].editedResponse;
          updatedInputs[index].isEditing = false;
        }
      });
      
      setInputs(updatedInputs);
      localStorage.setItem(`note-${id}`, JSON.stringify(updatedInputs));
      
      // You can also implement backend saving:
      // await axios.post(`http://localhost:8000/users/user1/notes/${id}/save`, { inputs: updatedInputs });
      
      alert("Note saved successfully!");
    } catch (err) {
      console.error("Error saving data:", err);
      alert("Failed to save note. Please try again.");
    }
  };

  // Save a specific section
  const saveSection = async (index) => {
    try {
      // If in edit mode, update the response with edited content
      const newInputs = [...inputs];
      
      if (newInputs[index].isEditing) {
        // Update the main response with edited content
        newInputs[index].response = newInputs[index].editedResponse;
        newInputs[index].isEditing = false;
      }
      
      setInputs(newInputs);
      
      // Save all data to localStorage
      localStorage.setItem(`note-${id}`, JSON.stringify(newInputs));
      
      // Optionally save to backend
      // await axios.post(`http://localhost:8000/users/user1/notes/${id}/sections/${index}/save`, newInputs[index]);
      
      alert(`Section ${index + 1} saved successfully!`);
    } catch (err) {
      console.error("Error saving section:", err);
      alert("Failed to save section. Please try again.");
    }
  };

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
      const responseText = res.data.answer || "Dummy Response"; // For now
      newInputs[index].response = responseText;
      newInputs[index].editedResponse = responseText; // Initialize edited response
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
      const errorText = "Failed to generate response. Please try again.";
      newInputs[index].response = errorText;
      newInputs[index].editedResponse = errorText;
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
        showExcalidraw: false,
        isEditing: false,
        editedResponse: ""
      }
    ]);
  };

  // Toggle Excalidraw iframe visibility for a specific section
  const toggleExcalidraw = (index) => {
    const newInputs = [...inputs];
    newInputs[index].showExcalidraw = !newInputs[index].showExcalidraw;
    setInputs(newInputs);
  };

  // Toggle edit mode for response
  const toggleEditMode = (index) => {
    const newInputs = [...inputs];
    
    // If switching to edit mode, initialize editedResponse with current response
    if (!newInputs[index].isEditing) {
      newInputs[index].editedResponse = newInputs[index].response;
    } else {
      // If exiting edit mode, apply the changes
      newInputs[index].response = newInputs[index].editedResponse;
    }
    
    newInputs[index].isEditing = !newInputs[index].isEditing;
    setInputs(newInputs);
  };

  // For saving edits specifically (separate from general section save)
  const saveEdits = (index) => {
    const newInputs = [...inputs];
    
    // Apply edits to the main response
    newInputs[index].response = newInputs[index].editedResponse;
    newInputs[index].isEditing = false;
    
    setInputs(newInputs);
    
    // Also save to storage
    localStorage.setItem(`note-${id}`, JSON.stringify(newInputs));
    alert("Edits saved successfully!");
  };

  return (
    <div className="note-page">
      <div className="note-header">
        <h1>Note {num}</h1>
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
          <button className="save-all-button" onClick={saveData}>
            <span className="button-icon">💾</span>
            Save All
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
                <button
                  className="save-button"
                  onClick={() => saveSection(index)}
                >
                  <span className="button-icon">💾</span>
                  Save Section
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
              
              {/* Show either the editable textarea or the rendered markdown */}
              {input.isEditing ? (
                <textarea
                  value={input.editedResponse}
                  onChange={(e) => handleChange(index, "editedResponse", e.target.value)}
                  className="editable-response-text"
                />
              ) : (
                <div className="markdown-response">
                  <ReactMarkdown>{input.response}</ReactMarkdown>
                </div>
              )}
              
              <div className="response-actions">
                <button 
                  className="edit-button"
                  onClick={() => toggleEditMode(index)}
                >
                  {input.isEditing ? "Cancel Editing" : "Edit Response"}
                </button>
                
                {input.isEditing ? (
                  <button 
                    className="save-edits-button"
                    onClick={() => saveEdits(index)}
                  >
                    Save Edits
                  </button>
                ) : (
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
                )}
              </div>
              
              {/* Raw view (only shown when not in edit mode and showRaw is true) */}
              {!input.isEditing && input.showRaw && (
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