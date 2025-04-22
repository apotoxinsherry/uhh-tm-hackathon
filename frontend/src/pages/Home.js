import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/Home.css";

function Home() {
  const [notes, setNotes] = useState([]);
  const navigate = useNavigate();
  
  const handleAddNote = () => {
    const newNoteId = notes.length;
    const newNote = {
      id: newNoteId,
      title: `Note ${newNoteId + 1}`,
      preview: "Click to start writing...",
      color: getRandomColor(),
      date: new Date().toLocaleDateString()
    };
    setNotes([...notes, newNote]);
  };
  
  const handleNoteClick = (id) => {
    navigate(`/note/${id}`);
  };
  
  const getRandomColor = () => {
    const colors = [
      "#FFF9C4", // Light Yellow
      "#DCEDC8", // Light Green
      "#B3E5FC", // Light Blue
      "#F8BBD0", // Light Pink
      "#E1BEE7", // Light Purple
      "#FFE0B2", // Light Orange
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  };
  
  return (
    <div className="home-container">
      <div className="home-header">
        <h1 className="home-title">📝 My Notes</h1>
        <button onClick={handleAddNote} className="add-button" title="Add Note">
          <span className="add-icon">+</span>
        </button>
      </div>
      
      <div className="notes-grid">
        {notes.length === 0 ? (
          <div className="empty-state">
            <div className="empty-illustration">📝</div>
            <p className="empty-title">Your notes space is empty</p>
            <p className="empty-msg">Click the + button to create your first note!</p>
          </div>
        ) : (
          notes.map((note) => (
            <div
              key={note.id}
              onClick={() => handleNoteClick(note.id)}
              className="note-card"
              style={{ backgroundColor: note.color }}
            >
              <h3 className="note-title">{note.title}</h3>
              <p className="note-preview">{note.preview}</p>
              <div className="note-footer">
                <span className="note-date">{note.date}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Home;