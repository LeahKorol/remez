import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { GoogleAuthButton } from '../components/GoogleAuth';
import { useUser } from '../utils/UserContext';
import './Login.css';

// handle backend errors and return an array of error messages
const handleBackendErrors = (data) => {
  let errorMessages = [];

  if (data.errors) {
    if (Array.isArray(data.errors)) errorMessages = data.errors;
    else if (typeof data.errors === 'object') {
      Object.keys(data.errors).forEach((field) => {
        const fieldErrors = data.errors[field];
        if (Array.isArray(fieldErrors)) fieldErrors.forEach((error) => errorMessages.push(`${field}: ${error}`));
        else errorMessages.push(`${field}: ${fieldErrors}`);
      });
    }
  } else if (data.detail) errorMessages.push(data.detail);
  else if (data.message) errorMessages.push(data.message);
  else if (data.non_field_errors) {
    if (Array.isArray(data.non_field_errors)) errorMessages = [...errorMessages, ...data.non_field_errors];
  }

  return errorMessages.length > 0 ? errorMessages : ['Unknown error occurred.'];
};

// check if email already exists
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

function Register() {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const [isLongEnough, setIsLongEnough] = useState(false);
  const [hasLetter, setHasLetter] = useState(false);
  const [notCommon, setNotCommon] = useState(true);

  const commonPasswords = [
    '123456','password','123456789','12345678','12345','qwerty','abc123',
    'football','monkey','letmein','111111','123123','welcome','admin','passw0rd'
  ];

  const { login } = useUser();
  
  useEffect(() => {
    setIsLongEnough(password.length >= 8);
    setHasLetter(/[A-Za-z]/.test(password));
    setNotCommon(!commonPasswords.includes(password.toLowerCase()));
  }, [password]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) navigate('/profile');
  }, [navigate]);

  const handleNameChange = (e) => {
    const value = e.target.value;
    if (value.length <= 200) setName(value);
    else toast.error('Name cannot exceed 200 characters.');
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    // check if email already exists
    const emailExists = await checkEmailExists(email);
    if (emailExists) {
      toast.error('This email is already registered. Redirecting to login...');
      navigate('/login', { state: { email } });
      setIsLoading(false);
      return;
    }

    // client-side validations
    if (name.length > 200) {
      toast.error('Name cannot exceed 200 characters.');
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

    const requestBody = { email, password1: password, password2: confirmPassword, name };

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/registration/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });
      const data = await response.json();

      if (response.ok) {
        if (data.user_id) login(data.user_id);
        
        toast.success('Registration successful! Please check your email to verify your account.');
        navigate('/email-verification-sent');
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

  return (
    <div className="login-container">
      <div className="login-header"><div className="logo">REMEZ</div></div>

      <div className="login-form-container">
        <div className="login-form">
          <h1>Create Account</h1>
          <p className="login-subtitle">Please complete the form to register</p>

          <form onSubmit={handleRegister}>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input type="email" id="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>

            <div className="form-group">
              <label htmlFor="name">Username</label>
              <input type="text" id="name" value={name} onChange={handleNameChange} maxLength={200} required />
              <small style={{ color: name.length > 180 ? 'orange' : 'gray' }}>{name.length}/200 characters</small>
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              <div className="password-guidelines">
                <ul>
                  <li style={{ color: isLongEnough ? 'green' : 'red' }}>{isLongEnough ? '✔' : '✖'} At least 8 characters</li>
                  <li style={{ color: hasLetter ? 'green' : 'red' }}>{hasLetter ? '✔' : '✖'} Include at least one letter</li>
                  <li style={{ color: notCommon ? 'green' : 'red' }}>{notCommon ? '✔' : '✖'} Not be too common</li>
                </ul>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input type="password" id="confirmPassword" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
            </div>

            <button type="submit" className="login-button" disabled={isLoading}>
              {isLoading ? 'Registering...' : 'Register'}
            </button>
          </form>

          <div className="separator"><span>or</span></div>
          <GoogleAuthButton isRegistration={true} className="google-login-button" size="large" />

          <p className="register-link">
            Already have an account? <a href="/login">Login</a>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Register;
