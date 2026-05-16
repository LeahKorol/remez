import React from 'react';
import { useGoogleAuth } from './GoogleAuth';

const GoogleAuthWrapper = () => {
  const { signInWithGoogle, isLoading } = useGoogleAuth();

  const handleGoogleClick = () => {
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
