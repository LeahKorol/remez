import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { GoogleAuthButton, GoogleOneTap } from './GoogleAuth';
import { fetchWithRefresh } from './tokenService'; // Import the enhanced fetchWithRefresh
import './Login.css';

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
  const [showEmailNotVerified, setShowEmailNotVerified] = useState(false);
  const [unverifiedEmail, setUnverifiedEmail] = useState('');
  const [isResending, setIsResending] = useState(false);
  const [dynamicButtonType, setDynamicButtonType] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/profile');
    }
  }, [navigate]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors([]);
    setShowRegisterButton(false);
    setShowForgotPassword(false);
    setShowEmailNotVerified(false);
    setDynamicButtonType(null);

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
        body: JSON.stringify({ email: email, password: password }),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success('Login successful!');
        // Store both access and refresh tokens
        localStorage.setItem('token', data.access);
        if (data.refresh) {
          localStorage.setItem('refreshToken', data.refresh);
        }
        console.log('Tokens saved - Access:', data.access, 'Refresh:', data.refresh);
        navigate('/profile');
        return;
      }

      // Check for email not verified error first
      const backendErrors = handleBackendErrors(data);
      const isEmailNotVerified = backendErrors.some(error =>
        error.toLowerCase().includes('e-mail is not verified') ||
        error.toLowerCase().includes('email is not verified') ||
        error.toLowerCase().includes('not verified')
      );

      if (isEmailNotVerified) {
        setShowEmailNotVerified(true);
        setUnverifiedEmail(email);
        setDynamicButtonType('verification');
        toast.error('Your email is not verified yet');
      }
      // Handle different status codes
      else if (response.status === 401) {
        const backendErrors = handleBackendErrors(data);
        setErrors(backendErrors.length > 0 ? backendErrors : ['Incorrect email or password.']);

        const passwordError = backendErrors.some(error =>
          error.toLowerCase().includes('password') ||
          error.toLowerCase().includes('incorrect') ||
          error.toLowerCase().includes('invalid credentials') ||
          error.toLowerCase().includes('unable to log in')
        );

        if (passwordError) {
          setShowForgotPassword(true);
          setDynamicButtonType('reset');
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
          setErrors(['This email is not registered in our system.']);
          setShowRegisterButton(true);
        } else {
          setShowForgotPassword(true);
          setDynamicButtonType('reset');
        }
      } else if (response.status === 404) {
        setErrors(['This email is not registered in our system.']);
        setShowRegisterButton(true);
      } else if (response.status >= 500) {
        setErrors(['Internal server error. Please try again later.']);
      } else {
        const backendErrors = handleBackendErrors(data);
        setErrors(backendErrors);
      }

    } catch (err) {
      console.error('Login error:', err);
      setErrors(['Network error. Please check your connection and try again.']);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendVerification = async () => {
    setIsResending(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/resend-verification/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: unverifiedEmail }),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success('Verification email resent! Please check your inbox.');
        setShowEmailNotVerified(false);
        setDynamicButtonType(null);
      } else {
        toast.error(data.error || 'Failed to resend verification email.');
      }
    } catch (error) {
      console.error('Resend verification error:', error);
      toast.error('Network error. Please try again later.');
    } finally {
      setIsResending(false);
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
        setDynamicButtonType(null);
      } else {
        const data = await res.json();
        const backendErrors = handleBackendErrors(data);
        setErrors(backendErrors);
      }
    } catch {
      setErrors(['Network error. Please try again.']);
    } finally {
      setIsResetLoading(false);
    }
  };

  return (
    <div className="login-container">
      <GoogleOneTap />

      <div className="login-header">
        <div className="logo">REMEZ</div>
      </div>

      <div className="login-form-container">
        <div className="login-form">
          <h1>Welcome Back</h1>
          <p className="login-subtitle">Please login to access your personal area</p>

          {(showEmailNotVerified || showForgotPassword) && (
            <div className={`alert ${dynamicButtonType === 'verification' ? 'alert-warning' : 'forgot-password-suggestion'}`}>
              <div className="alert-content">
                {dynamicButtonType === 'verification' ? (
                  <>
                    <strong>Email verification required</strong>
                    <p>Please check your email and click the verification link to activate your account.</p>
                  </>
                ) : (
                  <p>Forgot your password?</p>
                )}
                
                <button
                  className={dynamicButtonType === 'verification' ? 'resend-verification-btn' : 'forgot-password-button'}
                  onClick={dynamicButtonType === 'verification' ? handleResendVerification : handleForgotPassword}
                  type="button"
                  disabled={isResending || isResetLoading}
                >
                  {dynamicButtonType === 'verification' 
                    ? (isResending ? 'Sending verification email...' : 'Resend Verification Email')
                    : (isResetLoading ? 'Sending reset email...' : 'Reset Password')
                  }
                </button>
              </div>
            </div>
          )}

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
          </form>

          <div className="separator">
            <span>or</span>
          </div>

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