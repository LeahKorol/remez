import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { fetchWithRefresh } from "../utils/tokenService";
import { API_BASE } from "../utils/apiBase";
import { toast } from "react-toastify";
import "./LoadingPage.css";

const LoadingPage = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const queryData = location.state?.queryData;
    const isUpdate = location.state?.isUpdate || false;

    const [statusText, setStatusText] = useState("Analysis submitted to server...");
    const [videoLoaded, setVideoLoaded] = useState(false);
    const [fullQuery, setFullQuery] = useState(queryData);
    const isPollingCancelled = useRef(false);
    const timeoutRef = useRef(null);
    const pollingSessionRef = useRef(0);

    const clearPollingTimeout = () => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
        }
    };

    const isActiveSession = (sessionId) => {
        return !isPollingCancelled.current && pollingSessionRef.current === sessionId;
    };

    const extractStatus = (data) => {
        const status = data?.status || data?.result?.status || "";
        return typeof status === "string" ? status.toLowerCase().trim() : "";
    };

    const pollForResult = (queryId, sessionId) => {
        let attempts = 0;
        const maxAttempts = 120;
        let intervalTime = 5000;
        let pollingActive = true;

        const stopPolling = () => {
            pollingActive = false;
            clearPollingTimeout();
        };

        const scheduleNextPoll = () => {
            if (!pollingActive || !isActiveSession(sessionId)) return;
            clearPollingTimeout();
            timeoutRef.current = setTimeout(() => {
                if (!pollingActive || !isActiveSession(sessionId)) return;
                poll();
            }, intervalTime);
        };

        const poll = async () => {
            if (!pollingActive || !isActiveSession(sessionId)) return;

            attempts += 1;

            try {
                const response = await fetchWithRefresh(
                    `${API_BASE}/analysis/queries/${queryId}/?_t=${Date.now()}`
                );

                if (!isActiveSession(sessionId) || !pollingActive) return;
                if (!response) {
                    scheduleNextPoll();
                    return;
                }

                if (response.status === 500) {
                    setStatusText("Server encountered an error processing your analysis.");
                    stopPolling();
                    navigate("/500", {
                        state: {
                            message: "Server error occurred during analysis. Please try again later.",
                            type: "error",
                        },
                    });
                    return;
                }

                if (response.status === 404) {
                    setStatusText("Waiting for analysis to start on server...");
                    scheduleNextPoll();
                    return;
                }

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                if (!isActiveSession(sessionId) || !pollingActive) return;

                const status = extractStatus(data);

                if (status === "completed") {
                    stopPolling();
                    setStatusText("Analysis complete!");

                    clearPollingTimeout();
                    timeoutRef.current = setTimeout(() => {
                        if (!isActiveSession(sessionId)) return;
                        navigate("/analysis-email-notification", {
                            state: { queryData: data, isUpdate },
                        });
                    }, 1000);
                    return;
                }

                if (status === "failed") {
                    setStatusText("Analysis failed on server.");
                    stopPolling();
                    toast.error("Analysis failed. Please try again later.");
                    navigate("/profile", {
                        state: {
                            message: "Analysis failed. Please try again later.",
                            type: "error",
                        },
                    });
                    return;
                }

                if (status === "pending" || status === "") {
                    setStatusText("Processing analysis...");
                }

                if (attempts >= maxAttempts) {
                    stopPolling();
                    navigate("/profile", {
                        state: {
                            message: "Analysis is still in progress. Check again later.",
                            type: "info",
                        },
                    });
                    return;
                }

                if (attempts % 20 === 0 && intervalTime < 30000) {
                    intervalTime += 5000;
                }

                scheduleNextPoll();
            } catch (err) {
                if (!isActiveSession(sessionId) || !pollingActive) return;
                console.error("Polling error:", err);
                scheduleNextPoll();
            }
        };

        poll();
    };

    const pollForResultCreation = (queryId, sessionId) => {
        let attempts = 0;
        const maxAttempts = 60;
        const intervalTime = 5000;
        let pollingActive = true;

        const stopPolling = () => {
            pollingActive = false;
            clearPollingTimeout();
        };

        const scheduleNextPoll = () => {
            if (!pollingActive || !isActiveSession(sessionId)) return;
            clearPollingTimeout();
            timeoutRef.current = setTimeout(() => {
                if (!pollingActive || !isActiveSession(sessionId)) return;
                poll();
            }, intervalTime);
        };

        const poll = async () => {
            if (!pollingActive || !isActiveSession(sessionId)) return;

            attempts += 1;

            try {
                const response = await fetchWithRefresh(
                    `${API_BASE}/analysis/queries/${queryId}/?_t=${Date.now()}`
                );

                if (!isActiveSession(sessionId) || !pollingActive) return;
                if (!response) {
                    scheduleNextPoll();
                    return;
                }

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                if (!isActiveSession(sessionId) || !pollingActive) return;

                if (data?.result?.id) {
                    setStatusText("Result found. Starting analysis polling...");
                    stopPolling();
                    pollForResult(queryId, sessionId);
                    return;
                }

                if (attempts >= maxAttempts) {
                    stopPolling();
                    setStatusText("Analysis is still initializing...");
                    navigate("/profile", {
                        state: {
                            message: "Analysis is still initializing. Please check again later.",
                            type: "info",
                        },
                    });
                    return;
                }

                setStatusText("Waiting for server to start processing...");
                scheduleNextPoll();
            } catch (error) {
                if (!isActiveSession(sessionId) || !pollingActive) return;
                console.error("Error checking query:", error);
                scheduleNextPoll();
            }
        };

        poll();
    };

    useEffect(() => {
        const sessionId = pollingSessionRef.current + 1;
        pollingSessionRef.current = sessionId;
        isPollingCancelled.current = false;

        if (!queryData?.id) {
            navigate("/profile");
            return () => {};
        }

        if (queryData?.result?.id) {
            pollForResult(queryData.id, sessionId);
        } else {
            pollForResultCreation(queryData.id, sessionId);
        }

        return () => {
            isPollingCancelled.current = true;
            pollingSessionRef.current += 1;
            clearPollingTimeout();
        };
    }, []);

    useEffect(() => {
        const loadQueryDetails = async () => {
            if (!queryData?.id) return;

            try {
                const response = await fetchWithRefresh(
                    `${API_BASE}/analysis/queries/${queryData.id}/`
                );

                if (response?.ok) {
                    const fullData = await response.json();
                    setFullQuery(fullData);
                }
            } catch (err) {
                console.error("Error fetching query details:", err);
            }
        };

        if (!queryData?.displayDrugs && !queryData?.displayReactions) {
            loadQueryDetails();
        }
    }, []);

    if (!queryData) {
        return <div>Redirecting...</div>;
    }

    return (
        <div className="loading-page">
            <div className="loading-container">
                <div className="loading-header">
                    <div className="loading-icon">
                        <div className="video-wrapper">
                            <video
                                src="REMEZ_animation.mp4"
                                autoPlay
                                loop
                                muted
                                onCanPlay={() => setVideoLoaded(true)}
                                onError={() => setVideoLoaded(false)}
                                className={videoLoaded ? "visible" : "hidden"}
                            />
                        </div>
                        {!videoLoaded && (
                            <div className="spinner-wrapper" style={{ display: videoLoaded ? "none" : "flex" }}>
                                <div className="spinner"></div>
                                <div className="spinner-ring"></div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="notification-info">
                    <div className="info-card">
                        <div className="info-icon">i</div>
                        <div className="info-content">
                            <h3>Analysis in Progress</h3>
                            <p>
                                Your query is being processed on our servers. This may take several minutes
                                depending on the complexity of your data analysis.
                            </p>
                            <p className="status-text">{statusText}</p>
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
                            <span className="value">
                                {fullQuery?.displayDrugs?.length ||
                                    fullQuery?.drugs_details?.length ||
                                    fullQuery?.drugs?.length ||
                                    0} selected
                            </span>
                        </div>
                        <div className="summary-item">
                            <span className="label">Reactions</span>
                            <span className="value">
                                {fullQuery?.displayReactions?.length ||
                                    fullQuery?.reactions_details?.length ||
                                    fullQuery?.reactions?.length ||
                                    0} selected
                            </span>
                        </div>
                    </div>
                </div>

                <div className="action-buttons">
                    <button className="secondary-button" onClick={() => navigate("/profile")}>Return to Profile</button>
                    <p className="action-note">
                        You can safely leave this page. Results will be saved to your profile when ready.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default LoadingPage;
