import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import "../styles/NotePage.css"; // Import the CSS file

function NotePage() {
  const { id } = useParams();
  const [inputs, setInputs] = useState([{ tag: "", topic: "", content: "", response: "" }]);
  const navigate = useNavigate();

  // Handle change in topic, tag, or content fields
  const handleChange = (index, field, value) => {
    const newInputs = [...inputs];
    newInputs[index][field] = value;
    setInputs(newInputs);
  };

  // Handle submit action to fetch response
  const handleSubmit = async (index) => {
    const { tag, topic, content } = inputs[index];
    try {
      const res = await axios.post("http://localhost:8000/users/user1/notes/note1/ask", { "query":content });
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
    setInputs([...inputs, { tag: "", topic: "", content: "", response: "" }]);
  };

  return (
    <div className="note-page">
      <div className="note-header">
        <h1>Note #{id}</h1>
        <div className="navigation-buttons">
          <button className="nav-button " onClick={() => navigate("/")}>
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
                  className="generate-button"
                  onClick={() => handleSubmit(index)}
                >
                  Generate Response
                </button>
              </div>
            </div>
          </div>

          {input.response && (
            <div className="response-container">
              <label>Response</label>
              <textarea
                value={input.response}
                readOnly
                className="response-text"
              />
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