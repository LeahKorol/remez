import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { fetchWithRefresh } from '../utils/tokenService';
import { API_BASE } from '../utils/apiBase';
import { toast } from "react-toastify";
import "./LoadingPage.css";

const LoadingPage = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const queryData = location.state?.queryData;
    console.log("LoadingPage received queryData:", queryData);
    const isUpdate = location.state?.isUpdate || false;

    const [progress, setProgress] = useState(10);
    const [statusText, setStatusText] = useState("Analysis submitted to server...");
    const [resultId, setResultId] = useState(queryData?.result?.id || null);
    const [videoLoaded, setVideoLoaded] = useState(false);
    const [fullQuery, setFullQuery] = useState(queryData);
    const [startTime] = useState(Date.now());
    const expectedDuration = 10 * 60 * 1000; // 3 minutes

    const updateProgress = () => {
        const elapsed = Date.now() - startTime;
        const ratio = Math.min(elapsed / expectedDuration, 0.9);
        setProgress(Math.round(ratio * 100));
    };

    const isPollingCancelled = useRef(false);
    const timeoutRef = useRef(null);

    // useEffect(() => {
    //     // if there is no queryData, redirect back to profile
    //     if (!queryData?.id) {
    //         console.error("No query ID provided");
    //         navigate("/profile");
    //         return;
    //     }

    //     if (queryData.result?.id) {
    //         const resId = queryData.result.id;
    //         console.log("✅ Result exists, polling Result ID:", resId);
    //         setResultId(resId);
    //         pollForResult(resId);
    //     }

    //     else {
    //         console.log("Starting polling for query ID:", queryData.id);
    //         // start the polling process
    //         pollForResultCreation(queryData.id);
    //     }

    //     // if the user navigates away, cancel polling
    //     return () => {
    //         console.log("🛑 Cancelling polling and clearing timeout");
    //         isPollingCancelled.current = true;
    //         if (timeoutRef.current) clearTimeout(timeoutRef.current);
    //     };
    // }, [queryData, navigate]);


    useEffect(() => {
        // Reset polling flag
        isPollingCancelled.current = false;
        
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
        } else {
            console.log("Starting polling for query ID:", queryData.id);
            pollForResultCreation(queryData.id);
        }
    
        // if the user navigates away, cancel polling
        return () => {
            console.log("🛑 Cancelling polling and clearing timeout");
            isPollingCancelled.current = true;
            if (timeoutRef.current) clearTimeout(timeoutRef.current);
        };
    }, []); 

    // useEffect(() => {
    //     const loadQueryDetails = async () => {
    //         if (!queryData?.id) return;
    //         try {
    //             const response = await fetchWithRefresh(`http://127.0.0.1:8000/api/v1/analysis/queries/${queryData.id}/`);
    //             if (response.ok) {
    //                 const fullData = await response.json();
    //                 setFullQuery(fullData);
    //             }
    //         } catch (err) {
    //             console.error("Error fetching query details:", err);
    //         }
    //     };

    //     if (!queryData?.displayDrugs && !queryData?.displayReactions) {
    //         loadQueryDetails();
    //     }
    // }, [queryData]);


    useEffect(() => {
        const loadQueryDetails = async () => {
            if (!queryData?.id) return;
            try {
                const response = await fetchWithRefresh(
                    `${API_BASE}/analysis/queries/${queryData.id}/`
                );
                if (response.ok) {
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
    }, []); // ← שינוי כאן! הסרתי את queryData

    const safeSetTimeout = (fn, delay) => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(fn, delay);
    };

    // const extractStatus = (data) => {
    //     const status =
    //         data?.result?.status ||
    //         data?.status ||
    //         data?.result?.analysis_status ||
    //         data?.analysis_status ||
    //         data?.result?.state ||
    //         "";

    //     const normalized = typeof status === "string" ? status.toLowerCase().trim() : "";

    //     console.log("🔍 extractStatus:", {
    //         raw: status,
    //         normalized,
    //         hasResult: !!data?.result,
    //         resultStatus: data?.result?.status
    //     });

    //     return normalized;
    // };

    const extractStatus = (data) => {
        const status = data?.status || data?.result?.status || "";
        const normalized = typeof status === "string" ? status.toLowerCase().trim() : "";

        console.log("🔍 extractStatus:", {
            dataStatus: data?.status,
            resultStatus: data?.result?.status,
            normalized
        });

        return normalized;
    };


    // Stage 1: Poll until the Result is created
    const pollForResultCreation = (queryId) => {
        let attempts = 0;
        const maxAttempts = 60; // e.g. 5 minutes at 5s intervals
        const intervalTime = 5000;
        let pollingActive = true;

        const poll = async () => {
            if (!pollingActive || isPollingCancelled.current) {
                console.log("⛔ Polling for result creation stopped.");
                return;
            }

            attempts++;
            console.log(`Checking if Result exists (attempt ${attempts})...`);

            try {
                const response = await fetchWithRefresh(
                    `${API_BASE}/analysis/queries/${queryId}/?_t=${Date.now()}`
                );

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                console.log("📦 Query data:", data);
                console.log("🔍 Data structure:", {
                    hasStatus: !!data?.status,
                    status: data?.status,
                    hasResult: !!data?.result,
                    resultStatus: data?.result?.status
                });

                if (data.result?.id) {
                    console.log("✅ Result found! ID:", data.result.id);
                    setResultId(data.result.id);
                    setStatusText("Result found. Starting analysis polling...");
                    stopPolling();
                    pollForResult(data.result.id);
                    console.log("🚀 Switched to polling result:", data.result.id);
                    return;
                }

                if (attempts >= maxAttempts) {
                    console.warn("⚠️ Timeout waiting for result creation.");
                    stopPolling();
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
                scheduleNextPoll();
            } catch (error) {
                console.error("Error checking query:", error);
                scheduleNextPoll();
            }
        };

        const scheduleNextPoll = () => {
            if (!pollingActive || isPollingCancelled.current) return;
            clearTimeout(timeoutRef.current);
            timeoutRef.current = setTimeout(poll, intervalTime);
        };

        const stopPolling = () => {
            pollingActive = false;
            clearTimeout(timeoutRef.current);
        };

        poll();
    };

    // Stage 2: Poll until the Result is completed
    const pollForResult = (resId) => {
        let attempts = 0;
        const maxAttempts = 120;
        let intervalTime = 5000;
        let pollingActive = true;

        const poll = async () => {
            updateProgress();

            if (!pollingActive || isPollingCancelled.current) {
                console.log("⛔ Polling stopped.");
                return;
            }

            attempts++;
            console.log(`Polling result ${resId}, attempt ${attempts}`);

            try {
                // ✅ בקשת API
                const response = await fetchWithRefresh(
                    `${API_BASE}/analysis/queries/${queryData.id}/?_t=${Date.now()}`
                );

                // בדיקת שגיאות
                if (response.status === 500) {
                    console.log("Server error (500) while polling...");
                    setStatusText("Server encountered an error processing your analysis.");
                    stopPolling();
                    navigate("/500", {
                        state: {
                            message: "Server error occurred during analysis. Please try again later.",
                            type: "error"
                        },
                    });
                    return;
                }

                if (response.status === 404) {
                    console.log("Result not ready yet (404)...");
                    setStatusText("Waiting for analysis to start on server...");
                    scheduleNextPoll();
                    return;
                }

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                // get ata
                const data = await response.json();
                console.log("📦 Query data:", data);
                console.log("🔍 Data structure:", {
                    hasStatus: !!data?.status,
                    status: data?.status,
                    hasResult: !!data?.result,
                    resultStatus: data?.result?.status
                });

                // Progress
                const progressValue = Math.min(90, 10 + attempts * 1.2);
                setProgress(progressValue);

                const status = extractStatus(data);
                console.log(`✨ Current status: "${status}"`);

                // completed
                if (status === "completed") {
                    console.log("🎉 Analysis COMPLETED!");
                    stopPolling();
                    setProgress(100);
                    setStatusText("Analysis complete!");

                    safeSetTimeout(() => {
                        navigate("/analysis-email-notification", {
                            state: { queryData: data, isUpdate }
                        });
                    }, 1000);
                    return;
                }

                // failed
                if (status === "failed") {
                    console.log("❌ Analysis FAILED");
                    setStatusText("Analysis failed on server.");
                    stopPolling();
                    toast.error("❌ Analysis failed. Please try again later.");
                    navigate("/profile", {
                        state: {
                            message: "Analysis failed. Please try again later.",
                            type: "error"
                        }
                    });
                    return;
                }

                // pending
                if (status === "pending" || status === "") {
                    console.log(`⏳ Status: "${status || "empty"}", continuing...`);
                    setStatusText("Processing analysis...");
                }

                // max attempts
                if (attempts >= maxAttempts) {
                    console.warn("⚠️ Max attempts reached");
                    stopPolling();
                    navigate("/profile", {
                        state: {
                            message: "Analysis is still in progress. Check again later.",
                            type: "info"
                        }
                    });
                    return;
                }

                // Backoff
                if (attempts % 20 === 0 && intervalTime < 30000) {
                    intervalTime += 5000;
                    console.log(`⏱️ Interval: ${intervalTime}ms`);
                }

                scheduleNextPoll();

            } catch (err) {
                console.error("Polling error:", err);
                scheduleNextPoll();
            }
        };

        const scheduleNextPoll = () => {
            if (!pollingActive || isPollingCancelled.current) return;
            clearTimeout(timeoutRef.current);
            timeoutRef.current = setTimeout(poll, intervalTime);
        };

        const stopPolling = () => {
            pollingActive = false;
            clearTimeout(timeoutRef.current);
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
                        <div className="video-wrapper">
                            <video
                                src="REMEZ_animation.mp4"
                                autoPlay
                                loop
                                muted
                                onCanPlay={() => setVideoLoaded(true)} // video is readiy
                                onError={() => setVideoLoaded(false)}  // if not loaded
                                className={videoLoaded ? "visible" : "hidden"}
                            />
                        </div>
                        {/* if animation not loaded --> view spinner-ring */}
                        {!videoLoaded && (
                            <>
                                <div className="spinner-wrapper" style={{ display: videoLoaded ? "none" : "flex" }}>
                                    <div className="spinner"></div>
                                    <div className="spinner-ring"></div>
                                </div>
                            </>
                        )}
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