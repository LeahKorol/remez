import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import './Login.css';

const handleBackendErrors = (data) => {
  let errorMessages = [];

  if (data.errors) {
    if (Array.isArray(data.errors)) {
      errorMessages = data.errors;
    } else if (typeof data.errors === 'object') {
      Object.keys(data.errors).forEach((field) => {
        const fieldErrors = data.errors[field];
        if (Array.isArray(fieldErrors)) {
          fieldErrors.forEach((error) => {
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

  if (data.email) {
    Array.isArray(data.email)
      ? data.email.forEach((e) => errorMessages.push(`Email: ${e}`))
      : errorMessages.push(`Email: ${data.email}`);
  }

  if (data.username) {
    Array.isArray(data.username)
      ? data.username.forEach((e) => errorMessages.push(`Username: ${e}`))
      : errorMessages.push(`Username: ${data.username}`);
  }

  if (data.password1) {
    Array.isArray(data.password1)
      ? data.password1.forEach((e) => errorMessages.push(`Password: ${e}`))
      : errorMessages.push(`Password: ${data.password1}`);
  }

  if (data.password2) {
    Array.isArray(data.password2)
      ? data.password2.forEach((e) => errorMessages.push(`Confirm Password: ${e}`))
      : errorMessages.push(`Confirm Password: ${data.password2}`);
  }

  return errorMessages.length > 0 ? errorMessages : ['Unknown error occurred.'];
};

function Register() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const [isLongEnough, setIsLongEnough] = useState(false);
  const [hasLetter, setHasLetter] = useState(false);
  const [notCommon, setNotCommon] = useState(true);

  const commonPasswords = [
    '123456', 'password', '123456789', '12345678', '12345',
    'qwerty', 'abc123', 'football', 'monkey', 'letmein',
    '111111', '123123', 'welcome', 'admin', 'passw0rd',
  ];

  useEffect(() => {
    setIsLongEnough(password.length >= 8);
    setHasLetter(/[A-Za-z]/.test(password));
    setNotCommon(!commonPasswords.includes(password.toLowerCase()));
  }, [password]);

  const handleUsernameChange = (e) => {
    const value = e.target.value;
    if (value.length <= 200) {
      setUsername(value);
    } else {
      toast.error('Username cannot exceed 200 characters.');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    // בדיקת אורך Username
    if (username.length > 200) {
      toast.error('Username cannot exceed 200 characters.');
      setIsLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      toast.error('Passwords do not match.');
      setIsLoading(false);
      return;
    }

    if (!isLongEnough || !hasLetter || !notCommon) {
      toast.error('Password does not meet the requirements.');
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/registration/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          username,
          password1: password,
          password2: confirmPassword,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        if (data.token || data.access) {
          localStorage.setItem('token', data.token || data.access);
          toast.success('Registration successful!');
          navigate('/dashboard');
        } else {
          toast.info('Registration successful. Please verify your email before logging in.');
        }
        return;
      }

      const backendErrors = handleBackendErrors(data);
      backendErrors.forEach((err) => toast.error(err));
    } catch (err) {
      console.error('Network error:', err);
      toast.error('Network error. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleRegister = () => {
    console.log('Google registration clicked');
  };

  return (
    <div className="login-container">
      <div className="login-header">
        <div className="logo">REMEZ</div>
      </div>

      <div className="login-form-container">
        <div className="login-form">
          <h1>Create Account</h1>
          <p className="login-subtitle">Please complete the form to register</p>

          <form onSubmit={handleRegister}>
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
              <label htmlFor="username">Username</label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={handleUsernameChange}
                maxLength={200}
                required
              />
              <small style={{ color: username.length > 180 ? 'orange' : 'gray' }}>
                {username.length}/200 characters
              </small>
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
              <div className="password-guidelines">
                <p>Password must:</p>
                <ul>
                  <li style={{ color: isLongEnough ? 'green' : 'red' }}>
                    {isLongEnough ? '✔' : '✖'} At least 8 characters
                  </li>
                  <li style={{ color: hasLetter ? 'green' : 'red' }}>
                    {hasLetter ? '✔' : '✖'} Include at least one letter
                  </li>
                  <li style={{ color: notCommon ? 'green' : 'red' }}>
                    {notCommon ? '✔' : '✖'} Not be too common
                  </li>
                </ul>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                type="password"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="login-button" disabled={isLoading}>
              {isLoading ? 'Registering...' : 'Register'}
            </button>
          </form>

          <div className="separator">
            <span>or</span>
          </div>

          <button className="google-login-button" onClick={handleGoogleRegister}>
            <img src="/google-icon.svg" alt="Google" />
            Register with Google
          </button>

          <p className="register-link">
            Already have an account? <a href="/login">Login</a>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Register;