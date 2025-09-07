import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import './Login.css';

function EmailVerify() {
  const [isVerifying, setIsVerifying] = useState(true);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  const [errorType, setErrorType] = useState('');
  const [showResendButton, setShowResendButton] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailForResend, setEmailForResend] = useState('');
  const navigate = useNavigate();
  const { key } = useParams();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    // Check if this is a redirect from backend with URL parameters
    const verified = searchParams.get('verified');
    const urlError = searchParams.get('error');

    if (verified !== null) {
      setIsVerifying(false);
      
      if (verified === 'true') {
        setIsSuccess(true);
        toast.success('Email verified successfully! You can now log in.');
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else if (verified === 'false') {
        handleVerificationError(urlError);
      }
    } else if (key) {
      // Direct verification with key
      verifyEmail(key);
    } else {
      setError('Invalid verification link');
      setErrorType('invalid');
      setIsVerifying(false);
    }
  }, [key, searchParams]);

  const handleVerificationError = (errorType) => {
    if (errorType === 'expired') {
      setError('The compatibility link has expired. The link is only valid for 24 hours.');
      setErrorType('expired');
      setShowResendButton(true);
      toast.error('The compatibility link has expired. Please request a new link.');
    } else if (errorType === 'notfound') {
      setError('The appropriate link is invalid or not found in the system.');
      setErrorType('notfound');
      toast.error('Invalid matching link');
    } else if (errorType === 'invalid') {
      setError('Error matching email. The link may be broken.');
      setErrorType('invalid');
      toast.error('Error matching email. Try again.');
    } else {
      setError('Unexpected error in email verification.');
      setErrorType('general');
      toast.error('Email verification error');
    }
  };

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
        setErrorType('api_error');
        toast.error('Email verification failed');
      }
    } catch (err) {
      console.error('Verification error:', err);
      setError('Network error during verification');
      setErrorType('network');
      toast.error('Network error during verification');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleResendVerification = async () => {
    if (!emailForResend) {
      toast.error('Please enter your email address');
      return;
    }

    setIsResending(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/resend-verification/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: emailForResend
        })
      });

      const data = await response.json();

      if (response.ok) {
        toast.success('A new verification link has been sent to your email. Check your mailbox.');
        setShowResendButton(false);
        setShowEmailModal(false);
        setEmailForResend('');
        navigate('/login?message=verification_sent');
      } else {
        toast.error(data.error || 'Error sending new verification link');
      }
    } catch (err) {
      console.error('Resend error:', err);
      toast.error('Error connecting to server');
    } finally {
      setIsResending(false);
    }
  };

  const openResendModal = () => {
    setShowEmailModal(true);
  };

  const handleBackToLogin = () => {
    navigate('/login');
  };

  const getErrorIcon = () => {
    switch (errorType) {
      case 'expired':
        return '⏰';
      case 'notfound':
        return '🔍';
      case 'invalid':
        return '❌';
      case 'network':
        return '🌐';
      default:
        return '❌';
    }
  };

  const getErrorTitle = () => {
    switch (errorType) {
      case 'expired':
        return 'Verification Link Expired';
      case 'notfound':
        return 'Verification Link Not Found';
      case 'invalid':
        return 'Invalid Verification Link';
      case 'network':
        return 'Network Error';
      default:
        return 'Email Verification Failed';
    }
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
          <div className="error-icon">{getErrorIcon()}</div>
          <h1>{getErrorTitle()}</h1>
          <p className="error-message">{error}</p>
          
          {errorType === 'expired' && (
            <p>Verification links expire after 24 hours for security reasons.</p>
          )}
          
          {errorType === 'notfound' && (
            <p>The verification link may have been used already or doesn't exist.</p>
          )}
          
          {errorType === 'invalid' && (
            <p>The verification link appears to be corrupted or malformed.</p>
          )}
          
          {errorType === 'network' && (
            <p>Please check your internet connection and try again.</p>
          )}
          
          <div className="button-group" style={{ marginTop: '20px' }}>
            {showResendButton && (
              <button 
                className="login-button resend-button"
                onClick={openResendModal}
                disabled={isResending}
                type="button"
                style={{ 
                  marginBottom: '10px',
                  backgroundColor: isResending ? '#ccc' : '#007bff',
                  cursor: isResending ? 'not-allowed' : 'pointer'
                }}
              >
                Send New Verification Link
              </button>
            )}
            
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

      {/* Email Modal */}
      {showEmailModal && (
        <div className="modal-overlay" onClick={() => setShowEmailModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Resend Verification Email</h2>
            <p>Enter your email address to receive a new verification link:</p>
            <input
              type="email"
              value={emailForResend}
              onChange={(e) => setEmailForResend(e.target.value)}
              placeholder="Enter your email"
              className="email-input"
              autoFocus
            />
            <div className="modal-buttons">
              <button 
                onClick={handleResendVerification}
                disabled={isResending || !emailForResend}
                className="modal-button primary"
              >
                {isResending ? 'Sending...' : 'Send'}
              </button>
              <button 
                onClick={() => setShowEmailModal(false)}
                className="modal-button secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default EmailVerify;