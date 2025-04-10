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

      // Handle successful login
      localStorage.setItem('token', data.token);
      navigate('/profile');
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    // Implement Google OAuth logic here
    // This would typically redirect to Google's OAuth page
    console.log('Google login clicked');
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