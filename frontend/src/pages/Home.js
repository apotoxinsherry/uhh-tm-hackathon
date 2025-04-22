import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/Home.css";

function Home() {
  const [notes, setNotes] = useState([]);
  const navigate = useNavigate();
  
  // Load saved notes when component mounts
  useEffect(() => {
    loadSavedNotes();
  }, []);
  
  // Load notes from localStorage
  const loadSavedNotes = () => {
    try {
      // Check if there are any saved notes in localStorage
      const savedNotes = [];
      const keys = Object.keys(localStorage);
      
      // Look for note entries in localStorage
      keys.forEach(key => {
        if (key.startsWith('note-')) {
          // Extract the ID from the key (e.g., 'note-0' -> '0')
          const id = parseInt(key.split('-')[1]);
          
          // Create note object with extracted data
          const noteData = JSON.parse(localStorage.getItem(key));
          const title = `Note ${id + 1}`;
          
          // Extract preview from first input's content or response
          let preview = "Click to start writing...";
          if (noteData && noteData.length > 0) {
            if (noteData[0].content) {
              preview = noteData[0].content.substring(0, 50) + (noteData[0].content.length > 50 ? "..." : "");
            } else if (noteData[0].response) {
              preview = noteData[0].response.substring(0, 50) + (noteData[0].response.length > 50 ? "..." : "");
            }
          }
          
          savedNotes.push({
            id,
            title,
            preview,
            color: getRandomColor(),
            date: new Date().toLocaleDateString()
          });
        }
      });
      
      // Sort notes by ID
      savedNotes.sort((a, b) => a.id - b.id);
      setNotes(savedNotes);
      
    } catch (err) {
      console.error("Error loading saved notes:", err);
    }
  };

  const handleAddNote = () => {
    // Find the highest existing note ID and add 1
    const maxId = notes.length > 0 ? Math.max(...notes.map(note => note.id)) : -1;
    const newNoteId = maxId + 1;
    
    const newNote = {
      id: newNoteId,
      title: `Note ${newNoteId + 1}`,
      preview: "Click to start writing...",
      color: getRandomColor(),
      date: new Date().toLocaleDateString()
    };
    
    // Create empty structure for the new note in localStorage
    localStorage.setItem(`note-${newNoteId}`, JSON.stringify([{
      tag: "",
      topic: "",
      content: "",
      response: "",
      contextLevel: 3,
      includeDiagram: false,
      showExcalidraw: false,
      isEditing: false,
      editedResponse: ""
    }]));
    
    setNotes([...notes, newNote]);
    
    // Optionally, navigate directly to the new note
    navigate(`/note/${newNoteId}`);
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