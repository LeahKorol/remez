import React from 'react';
import { useNavigate } from 'react-router-dom';
import './EmailVerificationSent.css';

function EmailVerificationSent() {
  const navigate = useNavigate();

  const handleBackToRegister = () => {
    navigate('/register');
  };

  return (
    <div className="login-container">
      <div className="login-header">
        <div className="logo">REMEZ</div>
      </div>
      
      <div className="login-form-container">
        <div className="login-form">
          <div className="success-icon">📧</div>
          <h1>Check Your Email</h1>
          <p className="verification-message">
            We've sent you a verification email. Please check your inbox and click the verification link to activate your account.
          </p>
          
          <div className="verification-info">
            <h3>What to do next:</h3>
            <ol>
              <li>Open your email inbox</li>
              <li>Look for an email from REMEZ</li>
              <li>Click the verification link in the email</li>
              <li>Return to the login page to sign in</li>
            </ol>
          </div>

          <div className="verification-note">
            <p><strong>Didn't receive the email?</strong></p>
            <ul>
              <li>Check your spam/junk folder</li>
              <li>Make sure you entered the correct email address</li>
              <li>Wait a few minutes and check again</li>
            </ul>
          </div>
          
          <div className="button-group">
            <button 
              className="login-button secondary"
              onClick={handleBackToRegister}
              type="button"
            >
              Back to Registration
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EmailVerificationSent;