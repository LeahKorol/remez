import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'react-toastify';

// Google OAuth Configuration
const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || 'YOUR_GOOGLE_CLIENT_ID';
const GOOGLE_REDIRECT_URI = process.env.REACT_APP_GOOGLE_REDIRECT_URI || 'http://localhost:3000/auth/google/callback';

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
      const endpoint = isRegistration 
        ? 'http://127.0.0.1:8000/api/v1/auth/google/register'
        : 'http://127.0.0.1:8000/api/v1/auth/google/login';

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
        throw new Error(data.message || data.detail || 'Authentication failed');
      }
    } catch (error) {
      throw new Error(`Backend authentication failed: ${error.message}`);
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
      const loadingToast = toast.loading('מתחבר עם Google...');

      // Get user data from Google
      const googleUser = await googleAuthService.signInWithPopup();
      
      // Update loading message
      toast.update(loadingToast, {
        render: 'מאמת נתונים...',
        type: 'loading'
      });

      // Authenticate with your backend
      const authResult = await googleAuthService.authenticateWithBackend(googleUser, isRegistration);

      // Store token
      if (authResult.access) {
        localStorage.setItem('token', authResult.access);
      }

      // Success toast
      toast.update(loadingToast, {
        render: isRegistration ? 'נרשמת בהצלחה!' : 'התחברת בהצלחה!',
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
      
      toast.error(error.message || 'שגיאה בהתחברות עם Google', {
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

      // Try login first, then registration if user doesn't exist
      try {
        const authResult = await googleAuthService.authenticateWithBackend(googleUser, false);
        
        if (authResult.access) {
          localStorage.setItem('token', authResult.access);
          toast.success('התחברת בהצלחה!');
          navigate('/profile');
        }
      } catch (loginError) {
        // If login fails, try registration
        if (loginError.message.includes('not found') || loginError.message.includes('404')) {
          try {
            const registerResult = await googleAuthService.authenticateWithBackend(googleUser, true);
            
            if (registerResult.access) {
              localStorage.setItem('token', registerResult.access);
              toast.success('נרשמת והתחברת בהצלחה!');
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
      toast.error('שגיאה בהתחברות מהירה');
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

  const buttonText = isRegistration ? 'הרשמה עם Google' : 'התחברות עם Google';
  const loadingText = isRegistration ? 'נרשם...' : 'מתחבר...';

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

// Google Auth Callback Handler (for redirect method)
export const GoogleAuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [status, setStatus] = useState('processing');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const urlParams = new URLSearchParams(location.search);
        const code = urlParams.get('code');
        const error = urlParams.get('error');

        if (error) {
          throw new Error(error);
        }

        if (!code) {
          throw new Error('No authorization code received');
        }

        // Send code to your backend
        const response = await fetch('http://127.0.0.1:8000/api/v1/auth/google/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code }),
        });

        const data = await response.json();

        if (response.ok && data.access) {
          localStorage.setItem('token', data.access);
          setStatus('success');
          toast.success('התחברת בהצלחה!');
          setTimeout(() => navigate('/profile'), 2000);
        } else {
          throw new Error(data.message || 'Authentication failed');
        }

      } catch (error) {
        console.error('Callback error:', error);
        setStatus('error');
        toast.error('שגיאה בהתחברות');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleCallback();
  }, [location, navigate]);

  return (
    <div className="auth-callback-container">
      <div className="auth-callback-content">
        {status === 'processing' && (
          <>
            <div className="loading-spinner large">
              <div className="spinner"></div>
            </div>
            <h2>מעבד התחברות...</h2>
            <p>אנא המתן בזמן שאנו מאמתים את הנתונים שלך</p>
          </>
        )}
        
        {status === 'success' && (
          <>
            <div className="success-icon">✓</div>
            <h2>התחברות הושלמה!</h2>
            <p>מעביר אותך לפרופיל...</p>
          </>
        )}
        
        {status === 'error' && (
          <>
            <div className="error-icon">✗</div>
            <h2>שגיאה בהתחברות</h2>
            <p>מעביר אותך חזרה לעמוד ההתחברות...</p>
          </>
        )}
      </div>
    </div>
  );
};

export default GoogleAuthService;