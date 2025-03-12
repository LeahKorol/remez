import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./pages/login";
import Welcome from "./pages/welcome";

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Login />} />
                <Route path="/welcome/:username" element={<Welcome />} />
            </Routes>
        </Router>
    );
}

export default App;
