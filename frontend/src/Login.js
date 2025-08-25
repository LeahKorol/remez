import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { GoogleAuthButton, GoogleOneTap } from './GoogleAuth';
import './Login.css';

// Function to fetch data with token refresh logic
const fetchWithRefresh = async (url, options = {}) => {
  let response = await fetch(url, {
    ...options,
    credentials: 'include' // Send cookies with request
  });

  if (response.status === 401) {
    // Token expired, try to refresh
    const refreshResponse = await fetch('http://127.0.0.1:8000/api/v1/auth/token/refresh/', {
      method: 'POST',
      credentials: 'include'
    });

    if (refreshResponse.ok) {
      // Retry original request after refreshing token
      response = await fetch(url, {
        ...options,
        credentials: 'include'
      });
    } else {
      // Redirect to login if refresh fails
      window.location.href = '/login';
      return;
    }
  }

  return response;
};

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
  } else if (data.non_field_errors) {
    if (Array.isArray(data.non_field_errors)) {
      errorMessages = [...errorMessages, ...data.non_field_errors];
    }
  }

  return errorMessages.length > 0 ? errorMessages : ['Unknown error occurred.'];
};

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState([]);
  const [showRegisterButton, setShowRegisterButton] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [isResetLoading, setIsResetLoading] = useState(false);
  const navigate = useNavigate();

  // Initialize Google One Tap on component mount
  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/profile');
    }
  }, [navigate]);

  // Check if email exists in the system
  const checkEmailExists = async (emailToCheck) => {
    try {
      // First, try to login with a dummy password to see the error response
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: emailToCheck, password: 'dummy_password_check' }),
      });

      const data = await response.json();

      // If we get a 401 or password-related error, it means the email exists
      if (response.status === 401) {
        const errorMessages = handleBackendErrors(data);
        const passwordError = errorMessages.some(error =>
          error.toLowerCase().includes('password') ||
          error.toLowerCase().includes('incorrect') ||
          error.toLowerCase().includes('invalid credentials')
        );
        return passwordError; // Email exists if it's a password error
      }

      // If we get a 400 with email/user not found error, email doesn't exist
      if (response.status === 400 || response.status === 404) {
        const errorMessages = handleBackendErrors(data);
        const emailNotFoundError = errorMessages.some(error =>
          error.toLowerCase().includes('email') ||
          error.toLowerCase().includes('user') ||
          error.toLowerCase().includes('not found') ||
          error.toLowerCase().includes('does not exist')
        );
        return !emailNotFoundError; // Email doesn't exist
      }

      return false;
    } catch (err) {
      console.error('Error checking email:', err);
      return false;
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors([]);
    setShowRegisterButton(false);
    setShowForgotPassword(false);

    // Client-side validation
    const validationErrors = [];

    if (!email || email.trim() === '') {
      validationErrors.push('Please enter your email address.');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      validationErrors.push('Invalid email format.');
    }

    if (!password || password.trim() === '') {
      validationErrors.push('Please enter your password.');
    }

    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('token', data.access);
        console.log('Token saved:', data.access);
        navigate('/profile');
        return;
      }

      if (response.status === 401) {
        const backendErrors = handleBackendErrors(data);
        setErrors(backendErrors.length > 0 ? backendErrors : ['Incorrect email or password.']);

        // Check if this is a password error (meaning email exists)
        const passwordError = backendErrors.some(error =>
          error.toLowerCase().includes('password') ||
          error.toLowerCase().includes('incorrect') ||
          error.toLowerCase().includes('invalid credentials') ||
          error.toLowerCase().includes('unable to log in')
        );

        if (passwordError) {
          setShowForgotPassword(true);
        }
      } else if (response.status === 400) {
        const backendErrors = handleBackendErrors(data);
        setErrors(backendErrors);

        const emailNotFoundError = backendErrors.some(error =>
          error.toLowerCase().includes('email') ||
          error.toLowerCase().includes('user') ||
          error.toLowerCase().includes('not found') ||
          error.toLowerCase().includes('does not exist')
        );

        if (emailNotFoundError) {
          setShowRegisterButton(true);
        }
        else {
          // If it's not an email not found error, show forgot password
          setShowForgotPassword(true);
        }
      } else if (response.status === 404) {
        setErrors(['User not found.']);
        setShowRegisterButton(true);
      } else if (response.status >= 500) {
        setErrors(['Internal server error. Please try again later.']);
      } else {
        const backendErrors = handleBackendErrors(data);
        setErrors(backendErrors);
      }

    } catch (err) {
      console.error('Network error:', err);
      setErrors(['Network error. Please check your connection and try again.']);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterRedirect = () => {
    navigate('/register', { state: { email } });
  };

  const handleForgotPassword = async () => {
    if (!email) {
      setErrors(['Please enter your email to reset your password.']);
      return;
    }

    // Validate email format
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setErrors(['Please enter a valid email address.']);
      return;
    }

    setIsResetLoading(true);
    setErrors([]);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/auth/password/reset/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (res.ok) {
        toast.success('If an account with this email exists, a reset link has been sent.');
        setErrors([]);
        setShowForgotPassword(false);
      } else {
        const data = await res.json();
        const backendErrors = handleBackendErrors(data);
        setErrors(backendErrors);
      }
    } catch {
      setErrors(['Network error.']);
      setErrors(['Network error. Please try again.']);
    }
    finally {
      setIsResetLoading(false);
    }
  };

  return (
    <div className="login-container">
      {/* Google One Tap Component - will show automatically */}
      <GoogleOneTap />

      <div className="login-header">
        <div className="logo">REMEZ</div>
      </div>

      <div className="login-form-container">
        <div className="login-form">
          <h1>Welcome Back</h1>
          <p className="login-subtitle">Please login to access your personal area</p>

          {errors.length > 0 && (
            <div className="error-message">
              {errors.map((error, index) => (
                <div key={index} className="error-item">
                  {error}
                </div>
              ))}
            </div>
          )}

          {showRegisterButton && (
            <div className="register-suggestion">
              <p>Don't have an account yet?</p>
              <button
                className="register-button"
                onClick={handleRegisterRedirect}
                type="button"
              >
                Register now
              </button>
            </div>
          )}

          {showForgotPassword && (
            <div className="forgot-password-suggestion">
              <p>Forgot your password?</p>
              <button
                className="forgot-password-button"
                onClick={handleForgotPassword}
                type="button"
                disabled={isResetLoading}
              >
                {isResetLoading ? 'Sending reset link...' : 'Reset Password'}
              </button>
            </div>
          )}

          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              className="login-button"
              disabled={isLoading}
            >
              {isLoading ? 'Logging in...' : 'Login'}
            </button>

            <p className="forgot-password" onClick={handleForgotPassword}>
              Forgot your password?
            </p>
          </form>

          <div className="separator">
            <span>or</span>
          </div>

          {/* Replace the old Google button with the new GoogleAuthButton component */}
          <GoogleAuthButton
            isRegistration={false}
            className="google-login-button"
            size="large"
          />

          <p className="register-link">
            Don't have an account? <a href="/register">Register</a>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
export { fetchWithRefresh };