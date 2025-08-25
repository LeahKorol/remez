import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import './PasswordResetConfirm.css';

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

function PasswordResetConfirm() {
  const [newPassword1, setNewPassword1] = useState('');
  const [newPassword2, setNewPassword2] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState([]);
  const [showPassword1, setShowPassword1] = useState(false);
  const [showPassword2, setShowPassword2] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  
  const navigate = useNavigate();
  const { uidb64, token } = useParams();

  // Validate that we have the required URL parameters
  useEffect(() => {
    if (!uidb64 || !token) {
      console.error('Missing parameters:', { uidb64, token });
      setErrors(['Invalid password reset link. Please request a new one.']);
    }
  }, [uidb64, token]);

  const validatePasswords = () => {
    const validationErrors = [];

    if (!newPassword1 || newPassword1.trim() === '') {
      validationErrors.push('Please enter a new password.');
    } else if (newPassword1.length < 8) {
      validationErrors.push('Password must be at least 8 characters long.');
    }

    if (!newPassword2 || newPassword2.trim() === '') {
      validationErrors.push('Please confirm your new password.');
    }

    if (newPassword1 && newPassword2 && newPassword1 !== newPassword2) {
      validationErrors.push('Passwords do not match.');
    }

    // Additional password strength validation
    if (newPassword1) {
      const hasUpperCase = /[A-Z]/.test(newPassword1);
      const hasLowerCase = /[a-z]/.test(newPassword1);
      const hasNumbers = /\d/.test(newPassword1);
      
      if (!hasUpperCase || !hasLowerCase || !hasNumbers) {
        validationErrors.push('Password must contain at least one uppercase letter, one lowercase letter, and one number.');
      }
    }

    return validationErrors;
  };

  const handlePasswordReset = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors([]);

    // Client-side validation
    const validationErrors = validatePasswords();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      setIsLoading(false);
      return;
    }

    if (!uidb64 || !token) {
      setErrors(['Invalid password reset link. Please request a new one.']);
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/password/reset/confirm/', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          new_password1: newPassword1,
          new_password2: newPassword2,
          uid: uidb64,
          token: token
        }),
      });

      if (response.ok) {
        setIsSuccess(true);
        toast.success('Your password has been successfully reset!');
        // Redirect to login after 3 seconds
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else {
        const data = await response.json();
        const backendErrors = handleBackendErrors(data);
        
        // Handle specific error cases
        if (response.status === 400) {
          const tokenErrors = backendErrors.filter(error => 
            error.toLowerCase().includes('token') || 
            error.toLowerCase().includes('invalid') ||
            error.toLowerCase().includes('expired')
          );
          
          if (tokenErrors.length > 0) {
            setErrors(['This password reset link is invalid or has expired. Please request a new one.']);
          } else {
            setErrors(backendErrors);
          }
        } else {
          setErrors(backendErrors);
        }
      }
    } catch (err) {
      console.error('Password reset error:', err);
      setErrors(['Network error. Please check your connection and try again.']);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLogin = () => {
    navigate('/login');
  };

  const getPasswordStrength = (password) => {
    if (!password) return { strength: 0, label: '' };
    
    let strength = 0;
    const checks = {
      length: password.length >= 8,
      lowercase: /[a-z]/.test(password),
      uppercase: /[A-Z]/.test(password),
      numbers: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
    
    strength = Object.values(checks).filter(Boolean).length;
    
    const labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
    const colors = ['#dc3545', '#fd7e14', '#ffc107', '#20c997', '#28a745'];
    
    return {
      strength: Math.min(strength, 5),
      label: labels[Math.min(strength - 1, 4)] || '',
      color: colors[Math.min(strength - 1, 4)] || '#dc3545'
    };
  };

  const passwordStrength = getPasswordStrength(newPassword1);

  if (isSuccess) {
    return (
      <div className="password-reset-confirm-container">
        <div className="password-reset-confirm-header">
          <div className="logo">REMEZ</div>
        </div>
        
        <div className="password-reset-confirm-form-container">
          <div className="password-reset-confirm-form">
            <div className="success-icon">✓</div>
            <h1>Password Reset Successful!</h1>
            <p className="success-message">
              Your password has been successfully updated.
            </p>
            <p className="success-note">
              You will be redirected to the login page in a few seconds.
            </p>
            
            <button 
              className="login-redirect-button"
              onClick={handleBackToLogin}
              type="button"
            >
              Go to Login Now
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="password-reset-confirm-container">
      <div className="password-reset-confirm-header">
        <div className="logo">REMEZ</div>
      </div>
      
      <div className="password-reset-confirm-form-container">
        <div className="password-reset-confirm-form">
          <h1>Reset Your Password</h1>
          <p className="password-reset-confirm-subtitle">
            Enter your new password below to complete the reset process.
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
              <label htmlFor="new_password1">New Password</label>
              <div className="password-input-container">
                <input
                  type={showPassword1 ? "text" : "password"}
                  id="new_password1"
                  value={newPassword1}
                  onChange={(e) => setNewPassword1(e.target.value)}
                  placeholder="Enter your new password"
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword1(!showPassword1)}
                >
                  {showPassword1 ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              
              {newPassword1 && (
                <div className="password-strength">
                  <div className="strength-bar">
                    <div 
                      className="strength-fill" 
                      style={{
                        width: `${(passwordStrength.strength / 5) * 100}%`,
                        backgroundColor: passwordStrength.color
                      }}
                    ></div>
                  </div>
                  <span className="strength-label" style={{color: passwordStrength.color}}>
                    {passwordStrength.label}
                  </span>
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="new_password2">Confirm New Password</label>
              <div className="password-input-container">
                <input
                  type={showPassword2 ? "text" : "password"}
                  id="new_password2"
                  value={newPassword2}
                  onChange={(e) => setNewPassword2(e.target.value)}
                  placeholder="Confirm your new password"
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword2(!showPassword2)}
                >
                  {showPassword2 ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              
              {newPassword2 && newPassword1 !== newPassword2 && (
                <div className="password-match-error">
                  Passwords do not match
                </div>
              )}
              
              {newPassword2 && newPassword1 === newPassword2 && newPassword1 && (
                <div className="password-match-success">
                  ✓ Passwords match
                </div>
              )}
            </div>

            <div className="password-requirements">
              <h4>Password Requirements:</h4>
              <ul>
                <li className={newPassword1.length >= 8 ? 'valid' : ''}>
                  At least 8 characters long
                </li>
                <li className={/[A-Z]/.test(newPassword1) ? 'valid' : ''}>
                  One uppercase letter
                </li>
                <li className={/[a-z]/.test(newPassword1) ? 'valid' : ''}>
                  One lowercase letter
                </li>
                <li className={/\d/.test(newPassword1) ? 'valid' : ''}>
                  One number
                </li>
              </ul>
            </div>

            <button
              type="submit"
              className="password-reset-confirm-button"
              disabled={isLoading || !newPassword1 || !newPassword2 || newPassword1 !== newPassword2}
            >
              {isLoading ? 'Resetting Password...' : 'Reset Password'}
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

export default PasswordResetConfirm;