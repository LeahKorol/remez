// import React, { useState, useEffect } from 'react';
// import { useNavigate, useLocation } from 'react-router-dom';
// import './LoadingPage.css';

// const LoadingPage = () => {
//     const navigate = useNavigate();
//     const location = useLocation();
//     const [progress, setProgress] = useState(0);
//     const [currentStep, setCurrentStep] = useState(0);
    
//     // Get query data from navigation state
//     const queryData = location.state?.queryData;
//     const isUpdate = location.state?.isUpdate || false;
    
//     const steps = [
//         "Validating query parameters...",
//         "Processing drug data...",
//         "Analyzing reactions...",
//         "Computing frequency analysis...",
//         "Generating visualization...",
//         "Preparing email notification..."
//     ];

//     useEffect(() => {
//         // Redirect if no query data provided
//         if (!queryData) {
//             navigate('/profile');
//             return;
//         }

//         // Generate random total duration between 15-30 minutes (900-1800 seconds)
//         const totalDurationMs = (900 + Math.random() * 900) * 1000; // 15-30 minutes in milliseconds
        
//         // Distribute time across steps with logical weighting
//         const stepWeights = [0.05, 0.15, 0.15, 0.35, 0.25, 0.05]; // Total = 1.0
//         const stepDurations = stepWeights.map(weight => totalDurationMs * weight);
        
//         console.log(`Total processing time: ${Math.round(totalDurationMs / 60000)} minutes`);
//         console.log('Step durations (minutes):', stepDurations.map(d => Math.round(d / 60000)));

//         let progressInterval;
//         let stepTimeouts = [];
//         let currentStepStartTime = Date.now();
//         let accumulatedTime = 0;

//         // Progress animation - smooth progress based on time
//         progressInterval = setInterval(() => {
//             const elapsed = Date.now() - currentStepStartTime;
//             const currentStepDuration = stepDurations[currentStep] || 1000;
//             const stepProgress = Math.min(elapsed / currentStepDuration, 1);
            
//             // Calculate overall progress
//             const overallProgress = (accumulatedTime + elapsed) / totalDurationMs * 100;
//             setProgress(Math.min(overallProgress, 100));
//         }, 1000); // Update every second

//         // Schedule each step
//         let cumulativeTime = 0;
//         stepDurations.forEach((duration, index) => {
//             cumulativeTime += duration;
            
//             const timeout = setTimeout(() => {
//                 if (index < steps.length - 1) {
//                     setCurrentStep(index + 1);
//                     currentStepStartTime = Date.now();
//                     accumulatedTime += duration;
//                 } else {
//                     // Final step completed
//                     setProgress(100);
//                     setTimeout(() => {
//                         navigate('/profile', { 
//                             state: { 
//                                 message: isUpdate ? 'Query updated successfully!' : 'Query saved successfully!',
//                                 type: 'success'
//                             }
//                         });
//                     }, 3000); // Wait 3 seconds after completion
//                 }
//             }, cumulativeTime);
            
//             stepTimeouts.push(timeout);
//         });

//         // Cleanup on unmount
//         return () => {
//             clearInterval(progressInterval);
//             stepTimeouts.forEach(timeout => clearTimeout(timeout));
//         };
//     }, [navigate, queryData, isUpdate, steps.length]);

//     if (!queryData) {
//         return <div>Redirecting...</div>;
//     }

//     return (
//         <div className="loading-page">
//             <div className="loading-container">
//                 <div className="loading-header">
//                     <div className="loading-icon">
//                         <div className="spinner"></div>
//                         <div className="spinner-ring"></div>
//                     </div>
//                     <h1 className="loading-title">
//                         {isUpdate ? 'Updating Your Query' : 'Processing Your Query'}
//                     </h1>
//                     <p className="loading-subtitle">
//                         Please wait while we analyze your data...
//                     </p>
//                 </div>

//                 <div className="progress-section">
//                     <div className="progress-bar-container">
//                         <div 
//                             className="progress-bar"
//                             style={{ width: `${Math.min(progress, 100)}%` }}
//                         ></div>
//                     </div>
//                     <div className="progress-text">
//                         {Math.min(Math.round(progress), 100)}% Complete
//                     </div>
//                 </div>

//                 <div className="steps-section">
//                     <div className="current-step">
//                         {currentStep < steps.length ? steps[currentStep] : "Finalizing..."}
//                     </div>
                    
//                     <div className="steps-list">
//                         {steps.map((step, index) => (
//                             <div 
//                                 key={index}
//                                 className={`step-item ${
//                                     index < currentStep ? 'completed' : 
//                                     index === currentStep ? 'active' : 'pending'
//                                 }`}
//                             >
//                                 <div className="step-indicator">
//                                     {index < currentStep ? '✓' : index + 1}
//                                 </div>
//                                 <span className="step-text">{step}</span>
//                             </div>
//                         ))}
//                     </div>
//                 </div>

//                 <div className="notification-info">
//                     <div className="info-card prominent-notice">
//                         <div className="info-icon">ℹ️</div>
//                         <div className="info-content">
//                             <h3>You can safely leave this page</h3>
//                             <p>
//                                 The analysis is running in the background. You can close this tab or navigate 
//                                 anywhere else - we'll send you an email notification with your results when 
//                                 the processing is complete.
//                             </p>
//                         </div>
//                     </div>
                    
//                     <div className="info-card">
//                         <div className="info-icon">📧</div>
//                         <div className="info-content">
//                             <h3>Email Notification</h3>
//                             <p>
//                                 We'll send you an email notification once your query analysis is complete. 
//                                 The email will include a link to view your results and download the generated chart.
//                             </p>
//                             <div className="email-indicator">
//                                 Notification will be sent to: <strong>{queryData.userEmail || 'your registered email'}</strong>
//                             </div>
//                         </div>
//                     </div>
//                 </div>

//                 <div className="query-summary">
//                     <h4>Query Summary</h4>
//                     <div className="summary-grid">
//                         <div className="summary-item">
//                             <span className="label">Query Name:</span>
//                             <span className="value">{queryData.name}</span>
//                         </div>
//                         <div className="summary-item">
//                             <span className="label">Time Period:</span>
//                             <span className="value">
//                                 {queryData.year_start} Q{queryData.quarter_start} - {queryData.year_end} Q{queryData.quarter_end}
//                             </span>
//                         </div>
//                         <div className="summary-item">
//                             <span className="label">Drugs:</span>
//                             <span className="value">{queryData.drugs?.length || 0} selected</span>
//                         </div>
//                         <div className="summary-item">
//                             <span className="label">Reactions:</span>
//                             <span className="value">{queryData.reactions?.length || 0} selected</span>
//                         </div>
//                     </div>
//                 </div>

//                 <div className="action-buttons">
//                     <button 
//                         className="primary-button"
//                         onClick={() => navigate('/profile')}
//                     >
//                         Continue Browsing
//                     </button>
//                     <p className="action-note">
//                         You'll receive an email when your analysis is ready
//                     </p>
//                 </div>
//             </div>
//         </div>
//     );
// };

// export default LoadingPage;


import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { fetchWithRefresh } from './tokenService';
import "./LoadingPage.css";

const LoadingPage = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const queryData = location.state?.queryData;
  const isUpdate = location.state?.isUpdate || false;

  const [progress, setProgress] = useState(10);
  const [statusText, setStatusText] = useState("Analysis submitted to server...");

  useEffect(() => {
    if (!queryData || !queryData.id) {
      console.error("No query data or ID provided");
      navigate("/profile");
      return;
    }

    console.log("Starting polling for query ID:", queryData.id);
    
    // התחל פולינג מיד
    pollForResults(queryData.id);
  }, [queryData, navigate]);

  const pollForResults = (queryId) => {
    let attempts = 0;
    const maxAttempts = 120; // 10 דקות (120 * 5 שניות)
    
    const interval = setInterval(async () => {
      try {
        attempts++;
        console.log(`Polling attempt ${attempts} for query ${queryId}`);

        const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/queries/${queryId}/`);
        
        if (!response) {
          console.error("No response from fetchWithRefresh");
          clearInterval(interval);
          navigate("/");
          return;
        }

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("Received data from server:", {
          id: data.id,
          name: data.name,
          hasRorValues: !!(data.ror_values && data.ror_values.length > 0),
          hasRorLower: !!(data.ror_lower && data.ror_lower.length > 0),
          hasRorUpper: !!(data.ror_upper && data.ror_upper.length > 0)
        });

        // עדכן פרוגרס ואת הסטטוס
        const progressValue = Math.min(90, 10 + (attempts * 1.5));
        setProgress(progressValue);

        if (attempts < 10) {
          setStatusText("Processing drug data...");
        } else if (attempts < 20) {
          setStatusText("Analyzing adverse reactions...");
        } else if (attempts < 40) {
          setStatusText("Computing statistical analysis...");
        } else {
          setStatusText("Finalizing results...");
        }

        // בדוק אם יש תוצאות אמיתיות
        if (data.ror_values && data.ror_values.length > 0 && 
            data.ror_lower && data.ror_lower.length > 0 &&
            data.ror_upper && data.ror_upper.length > 0) {
          
          console.log("Results are ready! Navigating to profile...");
          clearInterval(interval);
          setProgress(100);
          setStatusText("Analysis complete!");

          // חכה רגע ואז עבור לפרופיל עם הודעת הצלחה
          setTimeout(() => {
            navigate("/profile", {
              state: {
                message: isUpdate ? "Query updated and analysis completed!" : "Query analysis completed successfully!",
                type: "success",
                // כדי שהמשתמש יראה את הגרף החדש, נעדכן את השאילתה
                updatedQuery: data
              },
            });
          }, 1500);
          
          return; // חשוב - יוצאים מהפונקציה
        }

        // אם עברנו את המקסימום זמן
        if (attempts >= maxAttempts) {
          console.log("Max attempts reached, stopping polling");
          clearInterval(interval);
          setStatusText("Analysis is taking longer than expected...");
          
          setTimeout(() => {
            navigate("/profile", {
              state: {
                message: "Analysis is still in progress. Results will appear in your saved queries when ready.",
                type: "info",
              },
            });
          }, 3000);
        }

      } catch (err) {
        console.error("Error during polling:", err);
        attempts++; // Count failed attempts too
        
        if (attempts >= 5) { // אחרי 5 שגיאות רצופות, תפסיק
          clearInterval(interval);
          navigate("/profile", {
            state: {
              message: "Error occurred while checking results. Please check your saved queries later.",
              type: "error",
            },
          });
        }
      }
    }, 5000); // כל 5 שניות

    // Cleanup function
    return () => {
      console.log("Cleaning up polling interval");
      clearInterval(interval);
    };
  };

  if (!queryData) {
    return <div>Redirecting...</div>;
  }

  return (
    <div className="loading-page">
      <div className="loading-container">
        <div className="loading-header">
          <div className="loading-icon">
            <div className="spinner"></div>
            <div className="spinner-ring"></div>
          </div>
          <h1 className="loading-title">
            Processing Your Analysis
          </h1>
          <p className="loading-subtitle">{statusText}</p>
        </div>

        <div className="progress-section">
          <div className="progress-bar-container">
            <div
              className="progress-bar"
              style={{ width: `${Math.min(progress, 100)}%` }}
            ></div>
          </div>
          <div className="progress-text">
            {Math.min(Math.round(progress), 100)}% Complete
          </div>
        </div>

        <div className="notification-info">
          <div className="info-card">
            <div className="info-icon">ℹ️</div>
            <div className="info-content">
              <h3>Analysis in Progress</h3>
              <p>
                Your query is being processed on our servers. This may take several minutes 
                depending on the complexity of your data analysis.
              </p>
            </div>
          </div>
        </div>

        <div className="query-summary">
          <h4>Query Summary</h4>
          <div className="summary-grid">
            <div className="summary-item">
              <span className="label">Query Name:</span>
              <span className="value">{queryData?.name}</span>
            </div>
            <div className="summary-item">
              <span className="label">Time Period:</span>
              <span className="value">
                {queryData?.year_start} Q{queryData?.quarter_start} - {queryData?.year_end} Q{queryData?.quarter_end}
              </span>
            </div>
            <div className="summary-item">
              <span className="label">Drugs:</span>
              <span className="value">{queryData?.displayDrugs?.length || queryData?.drugs?.length || 0} selected</span>
            </div>
            <div className="summary-item">
              <span className="label">Reactions:</span>
              <span className="value">
                {queryData?.displayReactions?.length || queryData?.reactions?.length || 0} selected
              </span>
            </div>
          </div>
        </div>

        <div className="action-buttons">
          <button 
            className="secondary-button"
            onClick={() => navigate('/profile')}
          >
            Return to Profile
          </button>
          <p className="action-note">
            You can safely leave this page. Results will be saved to your profile when ready.
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoadingPage;