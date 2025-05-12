import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

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

      if (!response.ok) {
        if (response.status === 401) {
          setError('Invalid email or password');
        } else if (response.status === 404) {
          // User not found, redirect to registration
          navigate('/register');
        } else {
          setError(data.message || 'Login failed. Please try again.');
        }
        return;
      }

    }
    catch (err) {
      setError('Network error. Please try again.');
    }
    finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    // Implement Google OAuth logic here
    // This would typically redirect to Google's OAuth page
    console.log('Google login clicked');
  };


  const handleForgotPassword = async () => {
    if (!email) {
      setError('Please enter your email.');
      return;
    }

    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/auth/password/reset/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (res.ok) {
        alert('If an account with this email exists, a reset link was sent.');
      } else {
        const data = await res.json();
        setError(data.message || 'Something went wrong.');
      }
    } catch {
      setError('Network error.');
    }
  };

  // Function to fetch data with token refresh logic
  const fetchWithRefresh = async (url, options = {}) => {
    let response = await fetch(url, {
      ...options,
      credentials: 'include'  
    });

    if (response.status === 401) {
      // token expired, try to refresh
      const refreshResponse = await fetch('http://127.0.0.1:8000/api/v1/auth/token/refresh/', {
        method: 'POST',
        credentials: 'include'  // send cookies
      });

      if (refreshResponse.ok) {
        // try to get a new access token
        response = await fetch(url, {
          ...options,
          credentials: 'include'
        });
      } else {
        // if the refresh token is invalid, redirect to login
        window.location.href = '/login';
        return;
      }
    }

    return response;
  };


  return (
    <div className="login-container">
      <div className="login-header">
        <div className="logo">REMEZ</div>
      </div>

      <div className="login-form-container">
        <div className="login-form">
          <h1>Welcome Back</h1>
          <p className="login-subtitle">Please login to access your personal area</p>

          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
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

          <button
            className="google-login-button"
            onClick={handleGoogleLogin}
          >
            <img src="/google-icon.svg" alt="Google" />
            Sign in with Google
          </button>

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