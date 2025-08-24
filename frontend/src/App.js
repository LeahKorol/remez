import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import './App.css';
import Home from './HomePage';
import Login from './Login';
import Register from './Registration';
import UserProfile from './UserProfile';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/profile" element={<UserProfile />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>

      <ToastContainer
        position="top-center"
        autoClose={7000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false} 
        pauseOnFocusLoss={false}
        draggable
        pauseOnHover
        theme="light" 
      />
    </BrowserRouter>
  );
}

// Protected route component
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');

  if (!token) {
    return <Navigate to="/login" />;
  }

  return children;
}

export default App;
