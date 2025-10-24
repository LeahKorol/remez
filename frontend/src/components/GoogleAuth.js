import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import axios from '../axiosConfig';

// Google OAuth Configuration
const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;

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
  async initializeOneTap(callback) {
    try {
      await this.loadGoogleAPI();

      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: callback,
        auto_select: false,
        cancel_on_tap_outside: false,
      });

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
      const response = await axios.get(
        `https://www.googleapis.com/oauth2/v2/userinfo?access_token=${accessToken}`
      );
      // if (!response.ok) throw new Error('Failed to fetch user profile');
      // return await response.json();
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get user profile: ${error.message}`);
    }
  }

  // Send Google user data to backend
  async authenticateWithBackend(googleUser, isRegistration = false) {
    try {
      const endpoint = isRegistration
        ? 'http://127.0.0.1:8000/api/v1/auth/google/register/'
        : 'http://127.0.0.1:8000/api/v1/auth/google/login/';

      const response = await axios.post(endpoint, {
        google_id: googleUser.id,
        email: googleUser.email,
        name: googleUser.name,
        picture: googleUser.picture,
        verified_email: googleUser.verified_email,
      });

      return response.data;

    } catch (error) {
      if (error.response?.status === 404) {
        throw new Error("User not found. Please register first.");
      }
      if (error.response?.status === 409) {
        throw new Error("Account already exists. Please try logging in instead.");
      }
      if (error.message.includes("Network Error")) {
        throw new Error("Network error. Please check your connection.");
      }
      throw error;
    }
  }
}

// Hook for Google Auth
export const useGoogleAuth = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const googleAuthService = new GoogleAuthService();

  const signInWithGoogle = async (isRegistration = false) => {
    setIsLoading(true);
    setError(null);

    try {
      const loadingToast = toast.loading('Login with Google...');
      const googleUser = await googleAuthService.signInWithPopup();

      toast.update(loadingToast, { render: 'Data Validator...', type: 'loading' });

      const authResult = await googleAuthService.authenticateWithBackend(googleUser, isRegistration);

      if (authResult.access) localStorage.setItem('token', authResult.access);

      toast.update(loadingToast, {
        render: isRegistration ? 'You have successfully registered!' : 'You have successfully logged in!',
        type: 'success',
        isLoading: false,
        autoClose: 2000
      });

      setTimeout(() => navigate('/profile'), 1000);

    } catch (err) {
      console.error('Google auth error:', err);
      setError(err.message);

      toast.dismiss(); 

      let msg = 'Error login to Google';
      if (err.message.includes('User not found')) msg = 'User not found. Please register first.';
      else if (err.message.includes('already exists')) msg = 'The account already exists. Try logging in instead of signing up.';
      else if (err.message.includes('Network error')) msg = 'Network problem. Check your internet connection.';

      toast.error(msg, { autoClose: 5000 });
    } finally {
      setIsLoading(false);
    }

  };

  const handleOneTapCallback = async (response) => {
    try {
      setIsLoading(true);
      const userObject = JSON.parse(atob(response.credential.split('.')[1]));
      const googleUser = {
        id: userObject.sub,
        email: userObject.email,
        name: userObject.name,
        picture: userObject.picture,
        verified_email: userObject.email_verified
      };

      try {
        const authResult = await googleAuthService.authenticateWithBackend(googleUser, false);
        if (authResult.access) {
          localStorage.setItem('token', authResult.access);
          toast.success('You have successfully connected!');
          navigate('/profile');
        }
      } catch (loginError) {
        if (loginError.message.includes('User not found') || loginError.message.includes('404')) {
          const registerResult = await googleAuthService.authenticateWithBackend(googleUser, true);
          if (registerResult.access) {
            localStorage.setItem('token', registerResult.access);
            toast.success('You have successfully registered and logged in!');
            navigate('/profile');
          }
        } else throw loginError;
      }
    } catch (err) {
      console.error('One Tap error:', err);
      toast.error('Quick connect error');
    } finally {
      setIsLoading(false);
    }
  };

  // const initializeOneTap = () => {
  //   googleAuthService.initializeOneTap(handleOneTapCallback);
  // };

  return { signInWithGoogle, isLoading, error };
};

// Google Auth Button
export const GoogleAuthButton = ({ isRegistration = false, className = '', disabled = false, size = 'large' }) => {
  const { signInWithGoogle, isLoading } = useGoogleAuth();
  const handleClick = () => signInWithGoogle(isRegistration);
  const buttonText = isRegistration ? 'Registration with Google' : 'Login with Google';
  const loadingText = isRegistration ? 'Registering...' : 'Connecting...';

  return (
    <button className={`google-auth-button ${className} ${size} ${isLoading ? 'loading' : ''}`} onClick={handleClick} disabled={disabled || isLoading} type="button">
      <div className="google-button-content">
        {!isLoading && (
          <svg className="images/google-icon" viewBox="0 0 24 24" width="20" height="20">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
          </svg>
        )}
        {isLoading && <div className="loading-spinner"><div className="spinner"></div></div>}
        <span className="button-text">{isLoading ? loadingText : buttonText}</span>
      </div>
    </button>
  );
};

// // One Tap Component
// export const GoogleOneTap = () => {
//   const { initializeOneTap } = useGoogleAuth();
//   useEffect(() => {
//     const timer = setTimeout(() => initializeOneTap(), 1000);
//     return () => clearTimeout(timer);
//   }, []);
//   return null;
// };

// Default export
export default GoogleAuthService;
