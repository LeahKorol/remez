import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './pages/Login.css';

function AnalysisEmailNotification() {
  const navigate = useNavigate();
  const location = useLocation();
  const [countdown, setCountdown] = useState(10);

  const queryData = location.state?.queryData;
  const isUpdate = location.state?.isUpdate || false;

  useEffect(() => {
    if (!queryData) {
      navigate('/profile');
      return;
    }

    // Start countdown
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          // Auto-navigate to results after countdown
          handleViewResults();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [queryData, navigate]);

  const handleViewResults = () => {
    navigate('/results', {
      state: {
        queryData: queryData,
        message: isUpdate ? "Query updated and analysis completed!" : "Query analysis completed successfully!",
        type: "success"
      }
    });
  };

  const handleReturnToProfile = () => {
    navigate('/profile', {
      state: {
        message: "Analysis completed! Check your email for the notification.",
        type: "success",
        updatedQuery: queryData
      }
    });
  };

  if (!queryData) {
    return <div>Redirecting...</div>;
  }

  return (
    <div className="login-container">
      <div className="login-header">
        <div className="logo">REMEZ</div>
      </div>
      
      <div className="login-form-container">
        <div className="login-form">
          <div className="success-icon">📧</div>
          <h1>Analysis Complete!</h1>
          <p className="verification-message">
            Great news! Your analysis has been completed successfully. We've sent you an email notification with the summary.
          </p>
          
          <div className="verification-info">
            <h3>What happens next:</h3>
            <ol>
              <li>Check your email for the analysis summary</li>
              <li>Click the link in the email to view detailed results</li>
              <li>Or continue directly to view your results below</li>
              <li>Results are also saved in your profile for future reference</li>
            </ol>
          </div>

          <div className="verification-note">
            <p><strong>Query Summary</strong></p>
            <ul>
              <li><strong>Name:</strong> {queryData.name}</li>
              <li><strong>Period:</strong> {queryData.year_start} Q{queryData.quarter_start} - {queryData.year_end} Q{queryData.quarter_end}</li>
              <li><strong>Drugs:</strong> {queryData.displayDrugs?.length || queryData.drugs?.length || 0} selected</li>
              <li><strong>Reactions:</strong> {queryData.displayReactions?.length || queryData.reactions?.length || 0} selected</li>
            </ul>
          </div>
          
          <div className="button-group">
            <button 
              className="login-button primary"
              onClick={handleViewResults}
              type="button"
            >
              View Results Now
            </button>
            
            <button 
              className="login-button secondary"
              onClick={handleReturnToProfile}
              type="button"
            >
              Return to Profile
            </button>

            <p className="redirect-info">
              Auto-redirecting to results in {countdown} seconds...
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AnalysisEmailNotification;