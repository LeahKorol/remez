import React, { useEffect, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import axios from "../axiosConfig";
import RorChart from "../components/RorChart";
import "./QueryResultPage.css";

export default function QueryResultPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const { queryId } = useParams();

    const [queryData, setQueryData] = useState(location.state?.queryData || null);
    const [loading, setLoading] = useState(!queryData);
    const [showDrugsModal, setShowDrugsModal] = useState(false);
    const [showReactionsModal, setShowReactionsModal] = useState(false);

    useEffect(() => {
        if (queryData) return;

        const token = localStorage.getItem("token");
        if (!token) {
            navigate("/login", { state: { from: `/queries/${queryId}/` } });
            return;
        }

        const fetchQueryData = async () => {
            try {
                const startTime = Date.now();
                const res = await axios.get(`/analysis/queries/${queryId}/`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                const elapsed = Date.now() - startTime;
                const minLoadingTime = 1000; // Minimum loading time in ms
                setTimeout(() => {
                    setQueryData(res.data);
                    setLoading(false);
                }, Math.max(0, minLoadingTime - elapsed));
            } catch (err) {
                console.error("Error fetching query:", err);
                if (err.response?.status === 401) {
                    // Token expired or invalid - redirect to login
                    localStorage.removeItem("token");
                    navigate("/login", { state: { from: `/queries/${queryId}/` } });
                } else if (err.response?.status === 404) {
                    navigate("/404");
                } else if (err.response?.status === 500) {
                    navigate("/500");
                } else {
                    setLoading(false);
                }
            }
        };

        fetchQueryData();
    }, [queryData, queryId, navigate]);

    if (loading) {
        return (
            <div className="loading-page">
                <div className="spinner"></div>
                <p>Loading analysis results...</p>
            </div>
        );
    }

    if (!queryData) return <p>No query data found.</p>;

    const drugs = Array.isArray(queryData.drugs_details)
        ? queryData.drugs_details
        : queryData.drugs_details?.split(",").map(d => ({ name: d.trim() })) || [];

    const reactions = Array.isArray(queryData.reactions_details)
        ? queryData.reactions_details
        : queryData.reactions_details?.split(",").map(r => ({ name: r.trim() })) || [];

    return (
        <div className="query-result-page">
            <header className="query-header">
                <button className="back-button" onClick={() => navigate("/profile")}>← Back to Profile</button>
                <div className="logo" onClick={() => navigate("/")}>REMEZ</div>
                <div className="placeholder"></div>
            </header>

            <main className="query-content">
                <h1>{queryData.name}</h1>

                <div className="query-info-card">
                    <div>
                        <strong>Period:</strong>{" "}
                        {queryData.year_start} Q{queryData.quarter_start} →{" "}
                        {queryData.year_end} Q{queryData.quarter_end}
                    </div>

                    <div>
                        <strong>Drugs:</strong>{" "}
                        {drugs?.slice(0, 3).map(d => d.name).join(", ")}
                        {drugs?.length > 3 && (
                            <button
                                className="view-more-btn"
                                onClick={() => setShowDrugsModal(true)}
                            >
                                View all
                            </button>
                        )}
                    </div>

                    <div>
                        <strong>Reactions:</strong>{" "}
                        {reactions?.slice(0, 3).map(r => r.name).join(", ")}
                        {reactions?.length > 3 && (
                            <button
                                className="view-more-btn"
                                onClick={() => setShowReactionsModal(true)}
                            >
                                View all
                            </button>
                        )}
                    </div>

                    <div>
                        <strong>Created:</strong>{" "}
                        {queryData.created_at
                            ? new Date(queryData.created_at).toLocaleDateString()
                            : "Unknown"}
                    </div>
                </div>

                <div className="chart-container-query-result">
                    {queryData?.result?.status === "completed" &&
                        Array.isArray(queryData?.result?.ror_values) &&
                        queryData.result.ror_values.length > 0 ? (
                        <RorChart
                            query={queryData.result}
                            year_start={queryData.year_start}
                            quarter_start={queryData.quarter_start}
                        />
                    ) : queryData?.result?.status === "completed" ? (
                        <div className="placeholder-content empty-state">
                            <div className="placeholder-icon">📊</div>
                            <h4>Analysis Completed</h4>
                            <p>
                                The analysis finished successfully, but no statistical results were found.
                                Try adjusting the filters or selecting different parameters.
                            </p>
                        </div>
                    ) : queryData?.result?.status === "failed" ? (
                        <div className="placeholder-content error-state">
                            <div className="placeholder-icon">❌</div>
                            <h4>Analysis Failed</h4>
                            <p>
                                Unfortunately, this query failed to process. Please try again or modify
                                your selection.
                            </p>
                        </div>
                    ) : (
                        <div className="placeholder-content">
                            <div className="placeholder-icon">⏳</div>
                            <h4>Analysis in Progress</h4>
                            <p>Results will appear here once analysis is complete.</p>
                        </div>
                    )}
                </div>
            </main>

            <footer className="query-footer">
                <p>© {new Date().getFullYear()} REMEZ — All rights reserved.</p>
            </footer>


            {
                showDrugsModal && (
                    <div className="modal-overlay" onClick={() => setShowDrugsModal(false)}>
                        <div
                            className="modal-content"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <h2>Drugs Used in Analysis</h2>
                            <ul>
                                {drugs.map((d, idx) => (
                                    <li key={idx}>{d.name}</li>
                                ))}
                            </ul>
                            <button
                                className="close-modal-btn"
                                onClick={() => setShowDrugsModal(false)}
                            >
                                Close
                            </button>
                        </div>
                    </div>
                )
            }

            {
                showReactionsModal && (
                    <div className="modal-overlay" onClick={() => setShowReactionsModal(false)}>
                        <div
                            className="modal-content"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <h2>Reactions Analyzed</h2>
                            <ul>
                                {reactions.map((r, idx) => (
                                    <li key={idx}>{r.name}</li>
                                ))}
                            </ul>
                            <button
                                className="close-modal-btn"
                                onClick={() => setShowReactionsModal(false)}
                            >
                                Close
                            </button>
                        </div>
                    </div>
                )
            }
        </div >
    );
}
