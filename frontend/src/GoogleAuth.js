import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'react-toastify';

// Google OAuth Configuration
const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;
const GOOGLE_REDIRECT_URI = process.env.REACT_APP_GOOGLE_REDIRECT_URI;

class GoogleAuthService {
  constructor() {
    this.isGoogleLoaded = false;
    this.loadGoogleAPI();
  }

  // Load Google API Script
  loadGoogleAPI() {
    return new Promise((resolve, reject) => {
      if (window.google && window.google.accounts) {
        this.isGoogleLoaded = true;
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        this.isGoogleLoaded = true;
        resolve();
      };
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  // Initialize Google One Tap
  async initializeGoogleOneTap(callback) {
    try {
      await this.loadGoogleAPI();
      
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: callback,
        auto_select: false,
        cancel_on_tap_outside: false,
      });

      // Show One Tap prompt
      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          console.log('One Tap not displayed:', notification.getNotDisplayedReason());
        }
      });
    } catch (error) {
      console.error('Failed to initialize Google One Tap:', error);
    }
  }

  // Sign in with popup
  async signInWithPopup() {
    try {
      await this.loadGoogleAPI();

      return new Promise((resolve, reject) => {
        window.google.accounts.oauth2.initTokenClient({
          client_id: GOOGLE_CLIENT_ID,
          scope: 'email profile',
          callback: (response) => {
            if (response.access_token) {
              this.getUserProfile(response.access_token)
                .then(resolve)
                .catch(reject);
            } else {
              reject(new Error('No access token received'));
            }
          },
          error_callback: reject
        }).requestAccessToken();
      });
    } catch (error) {
      throw new Error(`Google sign-in failed: ${error.message}`);
    }
  }

  // Get user profile from Google
  async getUserProfile(accessToken) {
    try {
      const response = await fetch(`https://www.googleapis.com/oauth2/v2/userinfo?access_token=${accessToken}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch user profile');
      }

      return await response.json();
    } catch (error) {
      throw new Error(`Failed to get user profile: ${error.message}`);
    }
  }

  // Send Google user data to your backend
  async authenticateWithBackend(googleUser, isRegistration = false) {
    try {
      // Updated endpoints to match your backend URLs
      const endpoint = isRegistration 
        ? 'http://127.0.0.1:8000/api/v1/auth/google/register/'
        : 'http://127.0.0.1:8000/api/v1/auth/google/login/';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          google_id: googleUser.id,
          email: googleUser.email,
          name: googleUser.name,
          picture: googleUser.picture,
          verified_email: googleUser.verified_email,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        return data;
      } else {
        // Better error handling for different HTTP status codes
        if (response.status === 404) {
          throw new Error('User not found. Please register first.');
        } else if (response.status === 409) {
          throw new Error('Account already exists. Please try logging in instead.');
        } else {
          throw new Error(data.error || data.detail || data.message || 'Authentication failed');
        }
      }
    } catch (error) {
      // Handle network errors
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Network error. Please check your connection.');
      }
      throw error;
    }
  }
}

// Google Auth Hook
export const useGoogleAuth = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const googleAuthService = new GoogleAuthService();

  const signInWithGoogle = async (isRegistration = false) => {
    setIsLoading(true);
    setError(null);

    try {
      // Show loading toast
      const loadingToast = toast.loading('login with Google...');

      // Get user data from Google
      const googleUser = await googleAuthService.signInWithPopup();
      
      // Update loading message
      toast.update(loadingToast, {
        render: 'Data Validator...',
        type: 'loading'
      });

      // Authenticate with your backend
      const authResult = await googleAuthService.authenticateWithBackend(googleUser, isRegistration);

      // Store token
      if (authResult.access) {
        localStorage.setItem('token', authResult.access);
        console.log('Google auth successful, token saved');
      }

      // Success toast
      toast.update(loadingToast, {
        render: isRegistration ? 'You have successfully registered!' : 'You have successfully logged in!',
        type: 'success',
        isLoading: false,
        autoClose: 2000
      });

      // Navigate to profile
      setTimeout(() => {
        navigate('/profile');
      }, 1000);

    } catch (error) {
      console.error('Google auth error:', error);
      setError(error.message);
      
      // Show appropriate error message
      let errorMessage = 'Error login to Google';
      
      if (error.message.includes('User not found')) {
        errorMessage = 'User not found. Please register first.';
      } else if (error.message.includes('already exists')) {
        errorMessage = 'The account already exists. Try logging in instead of signing up.';
      } else if (error.message.includes('Network error')) {
        errorMessage = 'Network problem. Check your internet connection.';
      }
      
      toast.error(errorMessage, {
        autoClose: 5000
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleOneTapCallback = async (response) => {
    try {
      setIsLoading(true);
      
      // Decode JWT token from Google One Tap
      const userObject = JSON.parse(atob(response.credential.split('.')[1]));
      
      const googleUser = {
        id: userObject.sub,
        email: userObject.email,
        name: userObject.name,
        picture: userObject.picture,
        verified_email: userObject.email_verified
      };

      // Try login first
      try {
        const authResult = await googleAuthService.authenticateWithBackend(googleUser, false);
        
        if (authResult.access) {
          localStorage.setItem('token', authResult.access);
          toast.success('You have successfully connected!');
          navigate('/profile');
        }
      } catch (loginError) {
        // If login fails with "User not found", try registration
        if (loginError.message.includes('User not found') || loginError.message.includes('404')) {
          try {
            const registerResult = await googleAuthService.authenticateWithBackend(googleUser, true);
            
            if (registerResult.access) {
              localStorage.setItem('token', registerResult.access);
              toast.success('You have successfully registered and logged in!');
              navigate('/profile');
            }
          } catch (registerError) {
            throw registerError;
          }
        } else {
          throw loginError;
        }
      }
    } catch (error) {
      console.error('One Tap error:', error);
      toast.error('Quick connect error');
    } finally {
      setIsLoading(false);
    }
  };

  const initializeOneTap = () => {
    googleAuthService.initializeGoogleOneTap(handleOneTapCallback);
  };

  return {
    signInWithGoogle,
    initializeOneTap,
    isLoading,
    error
  };
};

// Google Auth Button Component
export const GoogleAuthButton = ({ 
  isRegistration = false, 
  className = '', 
  disabled = false,
  size = 'large' 
}) => {
  const { signInWithGoogle, isLoading } = useGoogleAuth();

  const handleClick = () => {
    signInWithGoogle(isRegistration);
  };

  const buttonText = isRegistration ? 'Registration with Google' : 'login with Google';
  const loadingText = isRegistration ? 'Registering...' : 'Connecting...';

  return (
    <button
      className={`google-auth-button ${className} ${size} ${isLoading ? 'loading' : ''}`}
      onClick={handleClick}
      disabled={disabled || isLoading}
      type="button"
    >
      <div className="google-button-content">
        {!isLoading && (
          <svg className="google-icon" viewBox="0 0 24 24" width="20" height="20">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
        )}
        
        {isLoading && (
          <div className="loading-spinner">
            <div className="spinner"></div>
          </div>
        )}
        
        <span className="button-text">
          {isLoading ? loadingText : buttonText}
        </span>
      </div>
    </button>
  );
};

// One Tap Component
export const GoogleOneTap = () => {
  const { initializeOneTap } = useGoogleAuth();

  useEffect(() => {
    // Initialize One Tap when component mounts
    const timer = setTimeout(() => {
      initializeOneTap();
    }, 1000); // Small delay to ensure page is loaded

    return () => clearTimeout(timer);
  }, []);

  return null; // This component doesn't render anything visible
};

export default GoogleAuthService;