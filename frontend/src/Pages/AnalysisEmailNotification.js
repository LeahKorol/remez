import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./AnalysisEmailNotification.css";

const AnalysisEmailNotification = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryData = location.state?.queryData;

  return (
    <div className="analysis-notification-page">
      <div className="analysis-card">
        <div className="header-section">
          <div className="icon-wrapper">
            <div className="email-icon">📬</div>
          </div>
          <h1 className="title">Your Analysis Is Ready!</h1>
          <p className="subtitle">
            We’ve sent you an email with a link to view your analysis results.
          </p>
          <p className="subtitle secondary">
            You can also view the results directly here.
          </p>
        </div>

        <div className="divider"></div>

        <div className="summary-section">
          <h3 className="summary-title">Query Summary</h3>
          <div className="summary-grid">
            <div className="summary-item">
              <span className="label">Name:</span>
              <span className="value">{queryData?.name || "—"}</span>
            </div>
            <div className="summary-item">
              <span className="label">Time Period:</span>
              <span className="value">
                {queryData?.year_start} Q{queryData?.quarter_start} –{" "}
                {queryData?.year_end} Q{queryData?.quarter_end}
              </span>
            </div>
            <div className="summary-item">
              <span className="label">Drugs:</span>
              <span className="value">
                {queryData?.displayDrugs?.length ||
                  queryData?.drugs?.length ||
                  0}{" "}
                selected
              </span>
            </div>
            <div className="summary-item">
              <span className="label">Reactions:</span>
              <span className="value">
                {queryData?.displayReactions?.length ||
                  queryData?.reactions?.length ||
                  0}{" "}
                selected
              </span>
            </div>
          </div>
        </div>

        <div className="actions-section">
          <button
            className="primary-button"
            onClick={() =>
              navigate(`/queries/${queryData?.query}`, { state: { queryData } })
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

        <div className="footer-note">
          Didn’t receive the email? Check your spam folder or verify your
          registered address.
        </div>
      </div>
    </div>
  );
};

export default AnalysisEmailNotification;
