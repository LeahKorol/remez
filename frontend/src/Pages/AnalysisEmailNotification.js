import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./AnalysisEmailNotification.css";

const AnalysisEmailNotification = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryData = location.state?.queryData;

  return (
    <div className="analysis-notification-page">
      <div className="notification-container">
        <div className="notification-header">
          <div className="notification-icon">📬</div>
          <h1 className="notification-title">Your Analysis Is Ready!</h1>
          <p className="notification-subtitle">
            We’ve sent you an email with a direct link to your analysis results.
          </p>
          <p className="notification-subtitle">
            You can check your inbox or view the results right here.
          </p>
        </div>

        <div className="notification-actions">
          <button
            className="primary-button"
            onClick={() =>
              navigate(`/profile`, { state: { queryData } })
            }
          >
            View Results Now
          </button>

          <button
            className="secondary-button"
            onClick={() => navigate("/profile")}
          >
            Back to Profile
          </button>
        </div>

        <div className="notification-footer">
          <p>
            Didn’t receive the email? Check your spam folder or verify your
            account email address.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AnalysisEmailNotification;
