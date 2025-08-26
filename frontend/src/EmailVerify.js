import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import './Login.css'; // Use the same styling as login

function EmailVerify() {
  const [isVerifying, setIsVerifying] = useState(true);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { key } = useParams();

  useEffect(() => {
    if (key) {
      verifyEmail(key);
    } else {
      setError('Invalid verification link');
      setIsVerifying(false);
    }
  }, [key]);

  const verifyEmail = async (verificationKey) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/auth/email-verify/${verificationKey}/`);

      if (response.ok) {
        setIsSuccess(true);
        toast.success('Email verified successfully! You can now log in.');
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Email verification failed');
        toast.error('Email verification failed');
      }
    } catch (err) {
      console.error('Verification error:', err);
      setError('Network error during verification');
      toast.error('Network error during verification');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleBackToLogin = () => {
    navigate('/login');
  };

  if (isVerifying) {
    return (
      <div className="login-container">
        <div className="login-header">
          <div className="logo">REMEZ</div>
        </div>
        
        <div className="login-form-container">
          <div className="login-form">
            <div className="loading-icon">⏳</div>
            <h1>Verifying Email...</h1>
            <p>Please wait while we verify your email address.</p>
          </div>
        </div>
      </div>
    );
  }

  if (isSuccess) {
    return (
      <div className="login-container">
        <div className="login-header">
          <div className="logo">REMEZ</div>
        </div>
        
        <div className="login-form-container">
          <div className="login-form">
            <div className="success-icon">✅</div>
            <h1>Email Verified Successfully!</h1>
            <p>Your email has been verified. You can now log in to your account.</p>
            <p className="redirect-info">You will be redirected to the login page in a few seconds.</p>
            
            <button 
              className="login-button"
              onClick={handleBackToLogin}
              type="button"
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-header">
        <div className="logo">REMEZ</div>
      </div>
      
      <div className="login-form-container">
        <div className="login-form">
          <div className="error-icon">❌</div>
          <h1>Email Verification Failed</h1>
          <p className="error-message">{error}</p>
          <p>The verification link may have expired or is invalid.</p>
          
          <button 
            className="login-button"
            onClick={handleBackToLogin}
            type="button"
          >
            Back to Login
          </button>
        </div>
      </div>
    </div>
  );
}

export default EmailVerify;