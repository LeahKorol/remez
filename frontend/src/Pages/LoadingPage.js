import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { fetchWithRefresh } from '../utils/tokenService';
import { toast } from "react-toastify";
import "./LoadingPage.css";

const LoadingPage = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const queryData = location.state?.queryData;
    const isUpdate = location.state?.isUpdate || false;

    const [progress, setProgress] = useState(10);
    const [statusText, setStatusText] = useState("Analysis submitted to server...");
    const [resultId, setResultId] = useState(queryData?.result?.id || null);

    const isPollingCancelled = useRef(false);
    const timeoutRef = useRef(null);

    useEffect(() => {
        // if there is no queryData, redirect back to profile
        if (!queryData?.id) {
            console.error("No query ID provided");
            navigate("/profile");
            return;
        }

        if (queryData.result?.id) {
            const resId = queryData.result.id;
            console.log("✅ Result exists, polling Result ID:", resId);
            setResultId(resId);
            pollForResult(resId);
        }

        else {
            console.log("Starting polling for query ID:", queryData.id);
            // start the polling process
            pollForResultCreation(queryData.id);
        }

        // if the user navigates away, cancel polling
        return () => {
            console.log("🛑 Cancelling polling and clearing timeout");
            isPollingCancelled.current = true;
            if (timeoutRef.current) clearTimeout(timeoutRef.current);
        };
    }, [queryData, navigate]);

    const safeSetTimeout = (fn, delay) => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(fn, delay);
    };

    // Stage 1: Poll until the Result is created
    const pollForResultCreation = (queryId) => {
        let attempts = 0;
        const maxAttempts = 60; // e.g. 5 minutes at 5s intervals
        const intervalTime = 5000;

        const poll = async () => {
            if (isPollingCancelled.current) return;

            attempts++;
            console.log(`Checking if Result exists (attempt ${attempts})...`);

            try {
                const response = await fetchWithRefresh(
                    `http://127.0.0.1:8000/api/v1/analysis/queries/${queryId}/`
                );

                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const data = await response.json();

                if (data.result?.id) {
                    console.log("✅ Result found! ID:", data.result.id);
                    setResultId(data.result.id);
                    setStatusText("Result found. Starting analysis polling...");
                    pollForResult(data.result.id);
                    return;
                }

                if (attempts >= maxAttempts) {
                    setStatusText("Analysis is still initializing...");
                    navigate("/profile", {
                        state: {
                            message: "Analysis is still initializing. Please check again later.",
                            type: "info"
                        }
                    });
                    return;
                }

                setStatusText("Waiting for server to start processing...");
                if (!isPollingCancelled.current) safeSetTimeout(poll, intervalTime);
            } catch (error) {
                console.error("Error checking query:", error);
                if (!isPollingCancelled.current) safeSetTimeout(poll, intervalTime);
            }
        };

        poll();
    };

    // Stage 2: Poll until the Result is completed
    const pollForResult = (resId) => {
        let attempts = 0;
        const maxAttempts = 120;
        let intervalTime = 5000;

        const poll = async () => {
            if (isPollingCancelled.current) return;

            attempts++;
            console.log(`Polling result ${resId}, attempt ${attempts}`);

            try {
                const response = await fetchWithRefresh(
                    `http://127.0.0.1:8000/api/v1/analysis/results/${resId}/`
                );

                if (response.status === 500) {
                    console.log("Server error (500) while polling...");
                    setStatusText("Server encountered an error processing your analysis.");
                    isPollingCancelled.current = true;
                    clearTimeout(timeoutRef.current);
                    navigate("/500", {
                        state: {
                            message: "Server error occurred during analysis. Please try again later.",
                            type: "error"
                        }
                    });
                    return;
                }

                if (response.status === 404) {
                    console.log("Result not ready yet (404)...");
                    setStatusText("Waiting for analysis to start on server...");
                    if (!isPollingCancelled.current) safeSetTimeout(poll, intervalTime);
                    return;
                }

                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const data = await response.json();
                console.log("query status : ", data?.status);

                // Simulate progress
                const progressValue = Math.min(90, 10 + attempts * 1.5);
                setProgress(progressValue);

                if (data?.status === "failed") {
                    console.log("❌ Analysis failed.");
                    setStatusText("Analysis failed on server.");

                    // stop the polling 
                    isPollingCancelled.current = true;
                    clearTimeout(timeoutRef.current);
                    toast.error("❌ Analysis failed. Please try again later.");
                    navigate("/profile", {
                        state: {
                            message: "Analysis failed. Please try again later.",
                            type: "error"
                        }
                    }, 1500);
                    return;
                }

                if (data?.status === "completed" && data?.ror_values) {
                    console.log("✅ Analysis complete!");
                    setProgress(100);
                    setStatusText("Analysis complete!");
                    isPollingCancelled.current = true;
                    clearTimeout(timeoutRef.current);

                    // get the full query data with results
                    const fullQueryResponse = await fetchWithRefresh(
                        `http://127.0.0.1:8000/api/v1/analysis/queries/${queryData.id}/`
                    );
                    const fullQueryData = await fullQueryResponse.json();

                    safeSetTimeout(() => {
                        navigate("/analysis-email-notification", {
                            state: { queryData: fullQueryData, isUpdate }
                        });
                    }, 1500);
                    return;
                }

                if (attempts >= maxAttempts) {
                    setStatusText("Analysis is taking longer than expected...");
                    isPollingCancelled.current = true;
                    clearTimeout(timeoutRef.current);
                    navigate("/profile", {
                        state: {
                            message: "Analysis is still in progress. Check again later.",
                            type: "info"
                        }
                    });
                    return;
                }

                // Backoff logic
                if (attempts % 20 === 0 && intervalTime < 30000) {
                    intervalTime += 5000;
                }

                if (!isPollingCancelled.current) safeSetTimeout(poll, intervalTime);
            } catch (err) {
                console.error("Polling error:", err);
                if (!isPollingCancelled.current) safeSetTimeout(poll, intervalTime);
            }
        };

        poll();
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
                            <span className="label">Query Name</span>
                            <span className="value">{queryData?.name}</span>
                        </div>
                        <div className="summary-item">
                            <span className="label">Time Period</span>
                            <span className="value">
                                {queryData?.year_start} Q{queryData?.quarter_start} - {queryData?.year_end} Q{queryData?.quarter_end}
                            </span>
                        </div>
                        <div className="summary-item">
                            <span className="label">Drugs</span>
                            <span className="value">{queryData?.displayDrugs?.length || queryData?.drugs?.length || 0} selected</span>
                        </div>
                        <div className="summary-item">
                            <span className="label">Reactions</span>
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