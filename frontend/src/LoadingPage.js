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

        // start the polling process
        pollForResults(queryData.id);
    }, [queryData, navigate]);

    //   const pollForResults = (queryId) => {
    //     let attempts = 0;
    //     const maxAttempts = 120; // 10 minutes max (120 attempts every 5 seconds)

    //     const interval = setInterval(async () => {
    //       try {
    //         attempts++;
    //         console.log(`Polling attempt ${attempts} for query ${queryId}`);

    //         const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/queries/${queryId}/`);

    //         if (!response) {
    //           console.error("No response from fetchWithRefresh");
    //           clearInterval(interval);
    //           navigate("/");
    //           return;
    //         }

    //         if (!response.ok) {
    //           throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    //         }

    //         const data = await response.json();
    //         console.log("Received data from server:", {
    //           id: data.id,
    //           name: data.name,
    //           hasRorValues: !!(data.ror_values && data.ror_values.length > 0),
    //           hasRorLower: !!(data.ror_lower && data.ror_lower.length > 0),
    //           hasRorUpper: !!(data.ror_upper && data.ror_upper.length > 0)
    //         });

    //         // update progress and status text
    //         const progressValue = Math.min(90, 10 + (attempts * 1.5));
    //         setProgress(progressValue);

    //         if (attempts < 10) {
    //           setStatusText("Processing drug data...");
    //         } else if (attempts < 20) {
    //           setStatusText("Analyzing adverse reactions...");
    //         } else if (attempts < 40) {
    //           setStatusText("Computing statistical analysis...");
    //         } else {
    //           setStatusText("Finalizing results...");
    //         }

    //         // check if results are ready
    //         if (data.ror_values && data.ror_values.length > 0 && 
    //             data.ror_lower && data.ror_lower.length > 0 &&
    //             data.ror_upper && data.ror_upper.length > 0) {

    //           console.log("Results are ready! Navigating to profile...");
    //           clearInterval(interval);
    //           setProgress(100);
    //           setStatusText("Analysis complete!");

    //           // wait a moment before navigating to show 100% completion
    //           setTimeout(() => {
    //             navigate("/profile", {
    //               state: {
    //                 message: isUpdate ? "Query updated and analysis completed!" : "Query analysis completed successfully!",
    //                 type: "success",
    //                 // update the profile page with new data for user
    //                 updatedQuery: data
    //               },
    //             });
    //           }, 1500);

    //           return; 
    //         }

    //         // if max attempts reached, stop polling
    //         if (attempts >= maxAttempts) {
    //           console.log("Max attempts reached, stopping polling");
    //           clearInterval(interval);
    //           setStatusText("Analysis is taking longer than expected...");

    //           setTimeout(() => {
    //             navigate("/profile", {
    //               state: {
    //                 message: "Analysis is still in progress. Results will appear in your saved queries when ready.",
    //                 type: "info",
    //               },
    //             });
    //           }, 3000);
    //         }

    //       } catch (err) {
    //         console.error("Error during polling:", err);
    //         attempts++; // Count failed attempts too

    //         if (attempts >= 5) { // after 5 consecutive errors, give up
    //           clearInterval(interval);
    //           navigate("/profile", {
    //             state: {
    //               message: "Error occurred while checking results. Please check your saved queries later.",
    //               type: "error",
    //             },
    //           });
    //         }
    //       }
    //     }, 5000); // every 5 seconds

    //     // Cleanup function
    //     return () => {
    //       console.log("Cleaning up polling interval");
    //       clearInterval(interval);
    //     };
    //   };

    const pollForResults = (queryId) => {
        let attempts = 0;
        const maxAttempts = 120;

        const interval = setInterval(async () => {
            try {
                attempts++;
                console.log(`Polling attempt ${attempts} for query ${queryId}`);

                const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/queries/${queryId}/`);

                if (!response) {
                    console.error("No response from fetchWithRefresh");
                    clearInterval(interval);
                    navigate("/", {
                        state: {
                            message: "Authentication failed. Please log in again.",
                            type: "error"
                        }
                    });
                    return;
                }

                if (response.status === 404) {
                    clearInterval(interval);
                    navigate("/profile", {
                        state: {
                            message: "Query not found. It may have been deleted.",
                            type: "error"
                        }
                    });
                    return;
                }

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                // Validate data structure
                if (!data || !data.id) {
                    throw new Error("Invalid data structure received from server");
                }

                // ... rest of polling logic

            } catch (err) {
                console.error("Error during polling:", err);

                // Count consecutive failures
                if (attempts >= 5) {
                    clearInterval(interval);
                    navigate("/profile", {
                        state: {
                            message: "Unable to check analysis status. Please try refreshing the page later.",
                            type: "error"
                        }
                    });
                }
            }
        }, 5000);

        return () => clearInterval(interval);
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