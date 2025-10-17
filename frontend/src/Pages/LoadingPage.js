import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { fetchWithRefresh } from '../utils/tokenService';
import "./LoadingPage.css";

const LoadingPage = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const queryData = location.state?.queryData;
    const isUpdate = location.state?.isUpdate || false;

    const [progress, setProgress] = useState(10);
    const [statusText, setStatusText] = useState("Analysis submitted to server...");
    const [resultId, setResultId] = useState(queryData?.result?.id || null);

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
    }, [queryData, navigate]);

    // Stage 1: Poll until the Result is created
    const pollForResultCreation = (queryId) => {
        let attempts = 0;
        const maxAttempts = 60; // e.g. 5 minutes at 5s intervals
        const intervalTime = 5000;

        const poll = async () => {
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
                setTimeout(poll, intervalTime);
            } catch (error) {
                console.error("Error checking query:", error);
                setTimeout(poll, intervalTime);
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
            attempts++;
            console.log(`Polling result ${resId}, attempt ${attempts}`);

            try {
                const response = await fetchWithRefresh(
                    `http://127.0.0.1:8000/api/v1/analysis/results/${resId}/`
                );

                if (response.status === 404) {
                    console.log("Result not ready yet (404)...");
                    setStatusText("Waiting for analysis to start on server...");
                    setTimeout(poll, intervalTime);
                    return;
                }

                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const data = await response.json();

                // Simulate progress
                const progressValue = Math.min(90, 10 + attempts * 1.5);
                setProgress(progressValue);

                if (data?.status === "completed" && data?.ror_values) {
                    console.log("✅ Analysis complete!");
                    setProgress(100);
                    setStatusText("Analysis complete!");
                    setTimeout(() => {
                        navigate("/analysis-email-notification", {
                            state: { queryData: data, isUpdate }
                        });
                    }, 1500);
                    return;
                }

                if (attempts >= maxAttempts) {
                    setStatusText("Analysis is taking longer than expected...");
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

                setTimeout(poll, intervalTime);
            } catch (err) {
                console.error("Polling error:", err);
                setTimeout(poll, intervalTime);
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