import React, { useEffect, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { Line } from "react-chartjs-2";
import axios from "../axiosConfig";
import RorChart from "../components/RorChart";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from "chart.js";
import "./QueryResultPage.css";

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

export default function QueryResultPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const { queryId } = useParams();

    const [queryData, setQueryData] = useState(location.state?.queryData || null);
    const [loading, setLoading] = useState(!queryData);

    console.log(queryData);

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
                if (err.response?.status === 404) navigate("/404");
                else if (err.response?.status === 500) navigate("/500");
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

    const labels = queryData.result?.ror_values?.map((_, queryIdx) => `Q${queryIdx + 1}`) || [];
    const chartData = {
        labels,
        datasets: [
            {
                label: "ROR",
                data: queryData.result?.ror_values || [],
                fill: false,
                borderColor: "rgb(75, 192, 192)",
                tension: 0.3,
                borderWqueryIdth: 2,
            },
            {
                label: "ConfqueryIdence Interval Upper",
                data: queryData.result?.ror_upper || [],
                borderColor: "rgba(0,0,0,0)",
                backgroundColor: "rgba(75,192,192,0.2)",
                pointRadius: 0,
                tension: 0.3,
                fill: "+1",
            },
            {
                label: "ConfqueryIdence Interval Lower",
                data: queryData.result?.ror_lower || [],
                borderColor: "rgba(0,0,0,0)",
                backgroundColor: "rgba(75,192,192,0.2)",
                pointRadius: 0,
                tension: 0.3,
                fill: "-1",
            },
        ],
    };

    const options = {
        responsive: true,
        plugins: {
            legend: { position: "top" },
            title: { display: true, text: `Analysis Results: ${queryData.name}`, font: { size: 18 } },
        },
        scales: { y: { beginAtZero: true } },
    };

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
                    <div><strong>Period:</strong> {queryData.year_start} Q{queryData.quarter_start} → {queryData.year_end} Q{queryData.quarter_end}</div>
                    <div><strong>Drugs:</strong> {queryData.drugs_details?.length || 0}</div>
                    <div><strong>Reactions:</strong> {queryData.reactions_details?.length || 0}</div>
                    <div><strong>Created:</strong> {new Date(queryData.created_at).toLocaleDateString()}</div>
                </div>

                <div className="chart-container-query-result">
                    <RorChart query={queryData.result} />
                </div>
            </main>

            <footer className="query-footer">
                <p>© {new Date().getFullYear()} REMEZ — All rights reserved.</p>
            </footer>
        </div>
    );
}
