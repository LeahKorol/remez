import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'react-toastify';
import axios from '../axiosConfig';
import './PasswordReset.css';

// Function to handle backend error formatting
const handleBackendErrors = (data) => {
  let errorMessages = [];

  if (data.errors) {
    if (Array.isArray(data.errors)) {
      errorMessages = data.errors;
    } else if (typeof data.errors === 'object') {
      Object.keys(data.errors).forEach(field => {
        const fieldErrors = data.errors[field];
        if (Array.isArray(fieldErrors)) {
          fieldErrors.forEach(error => {
            errorMessages.push(`${field}: ${error}`);
          });
        } else {
          errorMessages.push(`${field}: ${fieldErrors}`);
        }
      });
    }
  } else if (data.detail) {
    errorMessages.push(data.detail);
  } else if (data.message) {
    errorMessages.push(data.message);
  }

  return errorMessages.length > 0 ? errorMessages : ['Unknown error occurred.'];
};

function PasswordReset() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState([]);
  const [isSuccess, setIsSuccess] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Get email from location state if passed from login page
  React.useEffect(() => {
    if (location.state?.email) {
      setEmail(location.state.email);
    }
  }, [location.state]);

  const handlePasswordReset = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors([]);

    // Client-side validation
    if (!email || email.trim() === '') {
      setErrors(['Please enter your email address.']);
      setIsLoading(false);
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setErrors(['Please enter a valid email address.']);
      setIsLoading(false);
      return;
    }

    try {
      const { data } = await axios.post('/auth/password/reset/', { email });

      setIsSuccess(true);
      setErrors([]);
      toast.success('If an account with this email exists, a reset link has been sent to your email address.');
    } catch (err) {
      console.error('Password reset error:', err);

      if (err.response?.status === 500) {
        setErrors(['Internal server error. Please try again later.']);
        setIsLoading(false);
        navigate('/500');
        return;
      }

      const backendErrors = handleBackendErrors(err.response?.data || []);
      setErrors(backendErrors.length ? backendErrors : ['Unknown error occurred.']);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLogin = () => {
    navigate('/login');
  };

  if (isSuccess) {
    return (
      <div className="password-reset-container">
        <div className="password-reset-header">
          <div className="logo">REMEZ</div>
        </div>

        <div className="password-reset-form-container">
          <div className="password-reset-form">
            <div className="success-icon">✓</div>
            <h1>Check Your Email</h1>
            <p className="success-message">
              If an account with this email address exists, we've sent you a password reset link.
            </p>
            <p className="success-note">
              Please check your inbox and spam folder. The link will expire in 24 hours.
            </p>

            <button
              className="back-to-login-button"
              onClick={handleBackToLogin}
              type="button"
            >
              Back to Login
            </button>

            <p className="resend-note">
              Didn't receive the email? Check your spam folder or try again with a different email address.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="password-reset-container">
      <div className="password-reset-header">
        <div className="logo">REMEZ</div>
      </div>

      <div className="password-reset-form-container">
        <div className="password-reset-form">
          <h1>Reset Your Password</h1>
          <p className="password-reset-subtitle">
            Enter your email address and we'll send you a link to reset your password.
          </p>

          {errors.length > 0 && (
            <div className="error-message">
              {errors.map((error, index) => (
                <div key={index} className="error-item">
                  {error}
                </div>
              ))}
            </div>
          )}

          <form onSubmit={handlePasswordReset}>
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email address"
                required
              />
            </div>

            <button
              type="submit"
              className="password-reset-button"
              disabled={isLoading}
            >
              {isLoading ? 'Sending Reset Link...' : 'Send Reset Link'}
            </button>
          </form>

          <div className="back-to-login">
            <button
              className="back-link"
              onClick={handleBackToLogin}
              type="button"
            >
              ← Back to Login
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PasswordReset;