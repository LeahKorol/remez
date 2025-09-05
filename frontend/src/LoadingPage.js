import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './LoadingPage.css';

const LoadingPage = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [progress, setProgress] = useState(0);
    const [currentStep, setCurrentStep] = useState(0);
    
    // Get query data from navigation state
    const queryData = location.state?.queryData;
    const isUpdate = location.state?.isUpdate || false;
    
    const steps = [
        "Validating query parameters...",
        "Processing drug data...",
        "Analyzing reactions...",
        "Computing frequency analysis...",
        "Generating visualization...",
        "Preparing email notification..."
    ];

    useEffect(() => {
        // Redirect if no query data provided
        if (!queryData) {
            navigate('/profile');
            return;
        }

        // Generate random total duration between 15-30 minutes (900-1800 seconds)
        const totalDurationMs = (900 + Math.random() * 900) * 1000; // 15-30 minutes in milliseconds
        
        // Distribute time across steps with logical weighting
        const stepWeights = [0.05, 0.15, 0.15, 0.35, 0.25, 0.05]; // Total = 1.0
        const stepDurations = stepWeights.map(weight => totalDurationMs * weight);
        
        console.log(`Total processing time: ${Math.round(totalDurationMs / 60000)} minutes`);
        console.log('Step durations (minutes):', stepDurations.map(d => Math.round(d / 60000)));

        let progressInterval;
        let stepTimeouts = [];
        let currentStepStartTime = Date.now();
        let accumulatedTime = 0;

        // Progress animation - smooth progress based on time
        progressInterval = setInterval(() => {
            const elapsed = Date.now() - currentStepStartTime;
            const currentStepDuration = stepDurations[currentStep] || 1000;
            const stepProgress = Math.min(elapsed / currentStepDuration, 1);
            
            // Calculate overall progress
            const overallProgress = (accumulatedTime + elapsed) / totalDurationMs * 100;
            setProgress(Math.min(overallProgress, 100));
        }, 1000); // Update every second

        // Schedule each step
        let cumulativeTime = 0;
        stepDurations.forEach((duration, index) => {
            cumulativeTime += duration;
            
            const timeout = setTimeout(() => {
                if (index < steps.length - 1) {
                    setCurrentStep(index + 1);
                    currentStepStartTime = Date.now();
                    accumulatedTime += duration;
                } else {
                    // Final step completed
                    setProgress(100);
                    setTimeout(() => {
                        navigate('/profile', { 
                            state: { 
                                message: isUpdate ? 'Query updated successfully!' : 'Query saved successfully!',
                                type: 'success'
                            }
                        });
                    }, 3000); // Wait 3 seconds after completion
                }
            }, cumulativeTime);
            
            stepTimeouts.push(timeout);
        });

        // Cleanup on unmount
        return () => {
            clearInterval(progressInterval);
            stepTimeouts.forEach(timeout => clearTimeout(timeout));
        };
    }, [navigate, queryData, isUpdate, steps.length]);

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
                        {isUpdate ? 'Updating Your Query' : 'Processing Your Query'}
                    </h1>
                    <p className="loading-subtitle">
                        Please wait while we analyze your data...
                    </p>
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

                <div className="steps-section">
                    <div className="current-step">
                        {currentStep < steps.length ? steps[currentStep] : "Finalizing..."}
                    </div>
                    
                    <div className="steps-list">
                        {steps.map((step, index) => (
                            <div 
                                key={index}
                                className={`step-item ${
                                    index < currentStep ? 'completed' : 
                                    index === currentStep ? 'active' : 'pending'
                                }`}
                            >
                                <div className="step-indicator">
                                    {index < currentStep ? '✓' : index + 1}
                                </div>
                                <span className="step-text">{step}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="notification-info">
                    <div className="info-card prominent-notice">
                        <div className="info-icon">ℹ️</div>
                        <div className="info-content">
                            <h3>You can safely leave this page</h3>
                            <p>
                                The analysis is running in the background. You can close this tab or navigate 
                                anywhere else - we'll send you an email notification with your results when 
                                the processing is complete.
                            </p>
                        </div>
                    </div>
                    
                    <div className="info-card">
                        <div className="info-icon">📧</div>
                        <div className="info-content">
                            <h3>Email Notification</h3>
                            <p>
                                We'll send you an email notification once your query analysis is complete. 
                                The email will include a link to view your results and download the generated chart.
                            </p>
                            <div className="email-indicator">
                                Notification will be sent to: <strong>{queryData.userEmail || 'your registered email'}</strong>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="query-summary">
                    <h4>Query Summary</h4>
                    <div className="summary-grid">
                        <div className="summary-item">
                            <span className="label">Query Name:</span>
                            <span className="value">{queryData.name}</span>
                        </div>
                        <div className="summary-item">
                            <span className="label">Time Period:</span>
                            <span className="value">
                                {queryData.year_start} Q{queryData.quarter_start} - {queryData.year_end} Q{queryData.quarter_end}
                            </span>
                        </div>
                        <div className="summary-item">
                            <span className="label">Drugs:</span>
                            <span className="value">{queryData.drugs?.length || 0} selected</span>
                        </div>
                        <div className="summary-item">
                            <span className="label">Reactions:</span>
                            <span className="value">{queryData.reactions?.length || 0} selected</span>
                        </div>
                    </div>
                </div>

                <div className="action-buttons">
                    <button 
                        className="primary-button"
                        onClick={() => navigate('/profile')}
                    >
                        Continue Browsing
                    </button>
                    <p className="action-note">
                        You'll receive an email when your analysis is ready
                    </p>
                </div>
            </div>
        </div>
    );
};

export default LoadingPage;