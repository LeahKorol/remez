// import React, { useEffect, useState } from 'react';
// import { useNavigate, useParams } from 'react-router-dom';
// import { toast } from 'react-toastify';
// import './Login.css'; 

// function EmailVerify() {
//   const [isVerifying, setIsVerifying] = useState(true);
//   const [isSuccess, setIsSuccess] = useState(false);
//   const [error, setError] = useState('');
//   const navigate = useNavigate();
//   const { key } = useParams();

//   useEffect(() => {
//     if (key) {
//       verifyEmail(key);
//     } else {
//       setError('Invalid verification link');
//       setIsVerifying(false);
//     }
//   }, [key]);

//   const verifyEmail = async (verificationKey) => {
//     try {
//       const response = await fetch(`http://127.0.0.1:8000/api/v1/auth/email-verify/${verificationKey}/`);

//       if (response.ok) {
//         setIsSuccess(true);
//         toast.success('Email verified successfully! You can now log in.');
//         setTimeout(() => {
//           navigate('/login');
//         }, 3000);
//       } else {
//         const data = await response.json();
//         setError(data.detail || 'Email verification failed');
//         toast.error('Email verification failed');
//       }
//     } catch (err) {
//       console.error('Verification error:', err);
//       setError('Network error during verification');
//       toast.error('Network error during verification');
//     } finally {
//       setIsVerifying(false);
//     }
//   };

//   const handleBackToLogin = () => {
//     navigate('/login');
//   };

//   if (isVerifying) {
//     return (
//       <div className="login-container">
//         <div className="login-header">
//           <div className="logo">REMEZ</div>
//         </div>
        
//         <div className="login-form-container">
//           <div className="login-form">
//             <div className="loading-icon">⏳</div>
//             <h1>Verifying Email...</h1>
//             <p>Please wait while we verify your email address.</p>
//           </div>
//         </div>
//       </div>
//     );
//   }

//   if (isSuccess) {
//     return (
//       <div className="login-container">
//         <div className="login-header">
//           <div className="logo">REMEZ</div>
//         </div>
        
//         <div className="login-form-container">
//           <div className="login-form">
//             <div className="success-icon">✅</div>
//             <h1>Email Verified Successfully!</h1>
//             <p>Your email has been verified. You can now log in to your account.</p>
//             <p className="redirect-info">You will be redirected to the login page in a few seconds.</p>
            
//             <button 
//               className="login-button"
//               onClick={handleBackToLogin}
//               type="button"
//             >
//               Go to Login
//             </button>
//           </div>
//         </div>
//       </div>
//     );
//   }

//   return (
//     <div className="login-container">
//       <div className="login-header">
//         <div className="logo">REMEZ</div>
//       </div>
      
//       <div className="login-form-container">
//         <div className="login-form">
//           <div className="error-icon">❌</div>
//           <h1>Email Verification Failed</h1>
//           <p className="error-message">{error}</p>
//           <p>The verification link may have expired or is invalid.</p>
          
//           <button 
//             className="login-button"
//             onClick={handleBackToLogin}
//             type="button"
//           >
//             Back to Login
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// }

// export default EmailVerify;



import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import './Login.css';

function EmailVerify() {
  const [isVerifying, setIsVerifying] = useState(true);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  const [errorType, setErrorType] = useState('');
  const [showResendButton, setShowResendButton] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const navigate = useNavigate();
  const { key } = useParams();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    // Check if this is a redirect from backend with URL parameters
    const verified = searchParams.get('verified');
    const urlError = searchParams.get('error');

    if (verified !== null) {
      setIsVerifying(false);
      
      if (verified === 'true') {
        setIsSuccess(true);
        toast.success('Email verified successfully! You can now log in.');
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else if (verified === 'false') {
        handleVerificationError(urlError);
      }
    } else if (key) {
      // Direct verification with key
      verifyEmail(key);
    } else {
      setError('Invalid verification link');
      setErrorType('invalid');
      setIsVerifying(false);
    }
  }, [key, searchParams]);

  const handleVerificationError = (errorType) => {
    if (errorType === 'expired') {
      setError('קישור האימות פג תוקפו. הקישור תקף למשך 24 שעות בלבד.');
      setErrorType('expired');
      setShowResendButton(true);
      toast.error('קישור האימות פג תוקפו. אנא בקש קישור חדש');
    } else if (errorType === 'notfound') {
      setError('קישור אימות לא תקין או לא נמצא במערכת.');
      setErrorType('notfound');
      toast.error('קישור אימות לא תקין');
    } else if (errorType === 'invalid') {
      setError('שגיאה באימות המייל. הקישור עלול להיות פגום.');
      setErrorType('invalid');
      toast.error('שגיאה באימות המייל. נסה שוב');
    } else {
      setError('שגיאה לא צפויה באימות המייל.');
      setErrorType('general');
      toast.error('שגיאה באימות המייל');
    }
  };

  const verifyEmail = async (verificationKey) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/auth/email-verify/${verificationKey}/`);

      if (response.ok) {
        setIsSuccess(true);
        toast.success('Email verified successfully! You can now log in.');
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Email verification failed');
        setErrorType('api_error');
        toast.error('Email verification failed');
      }
    } catch (err) {
      console.error('Verification error:', err);
      setError('Network error during verification');
      setErrorType('network');
      toast.error('Network error during verification');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleResendVerification = async () => {
    setIsResending(true);
    try {
      // You'll need to implement this endpoint or use your existing resend logic
      const response = await fetch('http://127.0.0.1:8000/api/v1/auth/resend-verification/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          // Add email or other identifier if needed
        })
      });

      if (response.ok) {
        toast.success('קישור אימות חדש נשלח למייל שלך');
        setShowResendButton(false);
        navigate('/login?message=verification_sent');
      } else {
        toast.error('שגיאה בשליחת קישור האימות החדש');
      }
    } catch (err) {
      console.error('Resend error:', err);
      toast.error('שגיאה בחיבור לשרת');
    } finally {
      setIsResending(false);
    }
  };

  const handleBackToLogin = () => {
    navigate('/login');
  };

  const getErrorIcon = () => {
    switch (errorType) {
      case 'expired':
        return '⏰';
      case 'notfound':
        return '🔍';
      case 'invalid':
        return '❌';
      case 'network':
        return '🌐';
      default:
        return '❌';
    }
  };

  const getErrorTitle = () => {
    switch (errorType) {
      case 'expired':
        return 'Verification Link Expired';
      case 'notfound':
        return 'Verification Link Not Found';
      case 'invalid':
        return 'Invalid Verification Link';
      case 'network':
        return 'Network Error';
      default:
        return 'Email Verification Failed';
    }
  };

  if (isVerifying) {
    return (
      <div className="login-container">
        <div className="login-header">
          <div className="logo">REMEZ</div>
        </div>
        
        <div className="login-form-container">
          <div className="login-form">
            <div className="loading-icon">⏳</div>
            <h1>Verifying Email...</h1>
            <p>Please wait while we verify your email address.</p>
          </div>
        </div>
      </div>
    );
  }

  if (isSuccess) {
    return (
      <div className="login-container">
        <div className="login-header">
          <div className="logo">REMEZ</div>
        </div>
        
        <div className="login-form-container">
          <div className="login-form">
            <div className="success-icon">✅</div>
            <h1>Email Verified Successfully!</h1>
            <p>Your email has been verified. You can now log in to your account.</p>
            <p className="redirect-info">You will be redirected to the login page in a few seconds.</p>
            
            <button 
              className="login-button"
              onClick={handleBackToLogin}
              type="button"
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-header">
        <div className="logo">REMEZ</div>
      </div>
      
      <div className="login-form-container">
        <div className="login-form">
          <div className="error-icon">{getErrorIcon()}</div>
          <h1>{getErrorTitle()}</h1>
          <p className="error-message">{error}</p>
          
          {errorType === 'expired' && (
            <p>Verification links expire after 24 hours for security reasons.</p>
          )}
          
          {errorType === 'notfound' && (
            <p>The verification link may have been used already or doesn't exist.</p>
          )}
          
          {errorType === 'invalid' && (
            <p>The verification link appears to be corrupted or malformed.</p>
          )}
          
          {errorType === 'network' && (
            <p>Please check your internet connection and try again.</p>
          )}
          
          <div className="button-group" style={{ marginTop: '20px' }}>
            {showResendButton && (
              <button 
                className="login-button resend-button"
                onClick={handleResendVerification}
                disabled={isResending}
                type="button"
                style={{ 
                  marginBottom: '10px',
                  backgroundColor: isResending ? '#ccc' : '#007bff',
                  cursor: isResending ? 'not-allowed' : 'pointer'
                }}
              >
                {isResending ? 'Sending...' : 'Send New Verification Link'}
              </button>
            )}
            
            <button 
              className="login-button"
              onClick={handleBackToLogin}
              type="button"
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EmailVerify;