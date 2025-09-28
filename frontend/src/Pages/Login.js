import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { GoogleAuthButton, GoogleOneTap } from '../components/GoogleAuth';
import { fetchWithRefresh } from '../utils/tokenService';
import { useUser } from '../utils/UserContext';
import axios from "../axiosConfig";
import './Login.css';

// Handle backend errors
const handleBackendErrors = (data) => {
  let errorMessages = [];

  if (data.errors) {
    if (Array.isArray(data.errors)) {
      errorMessages = data.errors;
    } else if (typeof data.errors === 'object') {
      Object.keys(data.errors).forEach((field) => {
        const fieldErrors = data.errors[field];
        if (Array.isArray(fieldErrors)) {
          fieldErrors.forEach((error) => errorMessages.push(`${field}: ${error}`));
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

// API check if email exists
const checkEmailExists = async (email) => {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/v1/auth/check-email/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    const data = await res.json();
    return data.exists;
  } catch (err) {
    console.error('Email check failed:', err);
    return false;
  }
};

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState([]);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [isResetLoading, setIsResetLoading] = useState(false);
  const [showEmailNotVerified, setShowEmailNotVerified] = useState(false);
  const [unverifiedEmail, setUnverifiedEmail] = useState('');
  const [isResending, setIsResending] = useState(false);
  const [dynamicButtonType, setDynamicButtonType] = useState(null);

  const navigate = useNavigate();
  const { login } = useUser();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) navigate('/profile');
  }, [navigate]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors([]);
    setShowForgotPassword(false);
    setShowEmailNotVerified(false);
    setDynamicButtonType(null);

    // Validation
    const validationErrors = [];
    if (!email.trim()) validationErrors.push('Please enter your email.');
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) validationErrors.push('Invalid email format.');
    if (!password.trim()) validationErrors.push('Please enter your password.');
    if (validationErrors.length) {
      setErrors(validationErrors);
      setIsLoading(false);
      return;
    }

    try {
      const { data } = await axios.post('/auth/login', { email, password });

      toast.success('Login successful!');
      localStorage.setItem('token', data.access);
      if (data.refresh) {
        localStorage.setItem('refreshToken', data.refresh);
      }

      if (data.user_id) {
        login(data.user_id);
      }

      navigate('/profile');
      return;
    }

    catch (error) {
      console.error("Login error:", error);

      const backendErrors = handleBackendErrors(error.response?.data || []);

      if (error.response?.status === 500) {
        setErrors(['Internal server error. Please try again later.']);
        navigate('/500');
        return;
      }

      const isEmailNotVerified = backendErrors.some((err) =>
        /not verified/i.test(err)
      );

      if (isEmailNotVerified) {
        setShowEmailNotVerified(true);
        setUnverifiedEmail(email);
        setDynamicButtonType('verification');
        toast.error('Your email is not verified yet');
        return;
      }

      if (error.response?.status === 401) {
        setErrors(backendErrors.length ? backendErrors : ['Incorrect email or password.']);
        setShowForgotPassword(true);
        setDynamicButtonType('reset');
        return;
      }

      if (error.response?.status === 400) {
        const emailExists = await checkEmailExists(email);
        if (!emailExists) {
          toast.info('Email not registered. Redirecting to registration...');
          navigate('/register', { state: { email } });
          return;
        } else {
          setErrors(['Incorrect password.']);
          setShowForgotPassword(true);
          setDynamicButtonType('reset');
        }
      }

      setErrors(backendErrors);
    } 
  };

  const handleResendVerification = async () => {
    setIsResending(true);
    try {
      try {
        await axios.post('/auth/resend-verification/', { email: unverifiedEmail });
        toast.success('Verification email resent!');
      } catch (err) {
        toast.error(err.response?.data?.error || 'Failed to resend verification email.');
      }
      setShowEmailNotVerified(false);
      setDynamicButtonType(null);
    } catch (err) {
      console.error(err);
      toast.error('Network error. Please try again later.');
    } finally {
      setIsResending(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!email.trim()) return setErrors(['Please enter your email to reset password.']);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return setErrors(['Please enter a valid email address.']);
    setIsResetLoading(true);
    setErrors([]);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/auth/password/reset/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (res.ok) {
        toast.success('If an account exists, a reset link has been sent.');
        setShowForgotPassword(false);
        setDynamicButtonType(null);
      } else {
        const data = await res.json();
        setErrors(handleBackendErrors(data));
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

      <div className="login-header"><div className="logo">REMEZ</div></div>

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
                    <p>Please check your email and click the verification link.</p>
                  </>
                ) : <p>Forgot your password?</p>}

                <button
                  className={dynamicButtonType === 'verification' ? 'resend-verification-btn' : 'forgot-password-button'}
                  onClick={dynamicButtonType === 'verification' ? handleResendVerification : handleForgotPassword}
                  disabled={isResending || isResetLoading}
                  type="button"
                >
                  {dynamicButtonType === 'verification'
                    ? isResending ? 'Sending...' : 'Resend Verification Email'
                    : isResetLoading ? 'Sending...' : 'Reset Password'}
                </button>
              </div>
            </div>
          )}

          {errors.length > 0 && (
            <div className="error-message">
              {errors.map((err, idx) => <div key={idx}>{err}</div>)}
            </div>
          )}

          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input type="email" id="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <button type="submit" className="login-button" disabled={isLoading}>
              {isLoading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          <div className="separator"><span>or</span></div>
          <GoogleAuthButton isRegistration={false} className="google-login-button" size="large" />

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
