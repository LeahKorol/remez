import React, { useEffect } from 'react';
import { useGoogleAuth } from './GoogleAuth';

const GoogleAuthWrapper = () => {
  const { initializeOneTap, signInWithGoogle, isLoading } = useGoogleAuth();

  useEffect(() => {
    // try to initialize One Tap on component mount
    initializeOneTap();
  }, []);

  const handleGoogleClick = () => {
    // allways enable to try to sign in with Google on button click
    signInWithGoogle();
  };

  return (
    <div>
      <button
        onClick={handleGoogleClick}
        disabled={isLoading}
        className="google-auth-button"
      >
        {isLoading ? 'Connecting...' : 'Login with Google'}
      </button>
    </div>
  );
};

export default GoogleAuthWrapper;
