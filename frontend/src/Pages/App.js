import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import './App.css';
import Home from './HomePage';
import Login from './Login';
import PasswordReset from './PasswordReset';
import PasswordResetConfirm from './PasswordResetConfirm';
import Register from './Registration';
import EmailVerify from './EmailVerify';
import EmailVerificationSent from './EmailVerificationSent';
import UserProfile from './UserProfile';
import LoadingPage from './LoadingPage';
import NotFoundPage from './NotFoundPage';
import ServerErrorPage from './ServerErrorPage';
import MaintenancePage from './MaintenancePage';
import SessionExpiredPage from './SessionExpiredPage';
import QueryResultPage from './QueryResultPage';
import AnalysisEmailNotification from './AnalysisEmailNotification';


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/password-reset" element={<PasswordReset />} />
        <Route path="/reset-password/:uidb64/:token" element={<PasswordResetConfirm />} />
        <Route path="/register" element={<Register />} />
        <Route path="/email-verify/:key" element={<EmailVerify />} />
        <Route path="/email-verification-sent" element={<EmailVerificationSent />} />
        <Route path="/profile" element={<UserProfile />} />
        <Route path="/loading" element={<LoadingPage />} />
        <Route path="/queries/:id" element={<QueryResultPage />} />
        <Route path="*" element={<NotFoundPage />} />
        <Route path="/404" element={<NotFoundPage />} />
        <Route path="/500" element={<ServerErrorPage />} />
        <Route path="/maintenance" element={<MaintenancePage />} />
        <Route path="/session-expired" element={<SessionExpiredPage />} />
        <Route path="/analysis-email-notification" element={<AnalysisEmailNotification />} />
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

// // Protected route component
// function ProtectedRoute({ children }) {
//   const token = localStorage.getItem('token');

//   if (!token) {
//     return <Navigate to="/login" />;
//   }

//   return children;
// }

export default App;