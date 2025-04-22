import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import NotePage from "./pages/NotePage";
import PUX from "./pages/PUX";
import Tutor from "./pages/Tutor";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/note/:id" element={<NotePage />} />
        <Route path="/pux" element={<PUX />} />
        <Route path="/tutor" element={<Tutor />} />
      </Routes>
    </Router>
  );
}

export default App;
