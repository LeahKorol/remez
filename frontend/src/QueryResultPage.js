import React, { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { Line } from "react-chartjs-2";
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

const API_BASE = "/api/v1/analysis/queries";

const QueryResultPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { id } = useParams();

  const [queryData, setQueryData] = useState(location.state?.queryData || null);
  const [loading, setLoading] = useState(!queryData);
  const [error, setError] = useState(null);

  // אם אין נתונים ב-state, fetch לפי id
  useEffect(() => {
    if (!queryData && id) {
      const fetchData = async () => {
        try {
          const res = await fetch(`${API_BASE}/${id}/`);
          if (!res.ok) throw new Error("Failed to fetch query data");
          const data = await res.json();
          setQueryData(data);
          setLoading(false);
        } catch (err) {
          console.error(err);
          setError("Error loading query data.");
          setLoading(false);
        }
      };
      fetchData();
    }
  }, [id, queryData]);

  if (loading) return <p>Loading results...</p>;
  if (error) return <p>{error}</p>;
  if (!queryData) return <p>No data available.</p>;

  const labels = queryData.ror_values.map((_, idx) => `Q${idx + 1}`);
  const chartData = {
    labels,
    datasets: [
      {
        label: "ROR",
        data: queryData.ror_values,
        fill: false,
        borderColor: "rgb(75, 192, 192)",
        tension: 0.3,
      },
      {
        label: "Confidence Interval",
        data: queryData.ror_upper,
        fill: "-1", // ממלא בין ה-line הזה ל-line הקודם
        borderColor: "rgba(0,0,0,0)",
        backgroundColor: "rgba(75,192,192,0.2)",
        pointRadius: 0,
        tension: 0.3,
      },
      {
        label: "Confidence Interval Lower",
        data: queryData.ror_lower,
        fill: "-2", // כדי ליצור shading בין lower ל upper
        borderColor: "rgba(0,0,0,0)",
        backgroundColor: "rgba(75,192,192,0.2)",
        pointRadius: 0,
        tension: 0.3,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
      title: {
        display: true,
        text: `Query Results: ${queryData.name}`,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <div className="query-result-page">
      <h1>{queryData.name}</h1>
      <p>
        Period: {queryData.year_start} Q{queryData.quarter_start} - {queryData.year_end} Q{queryData.quarter_end}
      </p>
      <Line data={chartData} options={options} />
      <button onClick={() => navigate("/profile")}>Back to Profile</button>
    </div>
  );
};

export default QueryResultPage;
