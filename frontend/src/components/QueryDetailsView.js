import React, { useRef, useState } from "react";
import { FaTimes, FaFileImage, FaFileCsv, FaArrowDown } from "react-icons/fa";
import RorChart from "./RorChart";
import { showToastMessage } from "../utils/toast";
import "../Pages/UserProfile.css";

const QueryDetailsView = ({ query, handleNewQuery, refreshQuery }) => {
  const chartRef = useRef(null);
  const [showCsvModal, setShowCsvModal] = useState(false);
  const [currentQuery, setCurrentQuery] = useState(query);

  console.log("Rendering QueryDetailsView for:", currentQuery);
  console.log("status: ", currentQuery.result.status);

  const isQueryLocked = currentQuery?.result?.status !== "completed" && currentQuery?.result?.status !== "failed";

  const hasResults =
    currentQuery?.result?.status === "completed" &&
    Array.isArray(currentQuery?.result?.ror_values) &&
    currentQuery.result.ror_values.length > 0;

  const handleRefreshStatus = async () => {
    if (!refreshQuery) return;
    try {
      const fullQuery = await refreshQuery(currentQuery.id);
      console.log("Refreshed query:", fullQuery);

      setCurrentQuery(fullQuery);

      if (fullQuery.result?.status === "completed") {
        showToastMessage("✅ Analysis completed! Results are now available.");
      } else if (fullQuery.result?.status === "failed") {
        showToastMessage("⚠️ Query failed during processing. Please try again.", "error");
      } else {
        showToastMessage("⏳ Query still processing, try again soon.");
      }

      // const mergedQuery = {
      //   ...currentQuery,
      //   ...fullQuery,
      //   result: {
      //     ...currentQuery.result,
      //     ...fullQuery.result,
      //     ror_values: fullQuery.result?.ror_values || [],
      //     ror_lower: fullQuery.result?.ror_lower || [],
      //     ror_upper: fullQuery.result?.ror_upper || [],
      //   },
      // };

      // console.log("mergedQuery: ", mergedQuery);
      // setCurrentQuery(mergedQuery);
    } catch (err) {
      console.error("Error refreshing query:", err);
      alert("Failed to refresh query. Please try again.");
    }
  };

  const csvHeaders = [
    "Time Period",
    "ROR (Log10)",
    "ROR (Original)",
    "Lower CI",
    "Upper CI",
  ];

  const csvRows =
    currentQuery?.result.ror_values?.map((rorValue, index) => {
      const logValue = Math.log10(rorValue || 0.1);
      const lowerCI = currentQuery.result.ror_lower[index] || "";
      const upperCI = currentQuery.result.ror_upper[index] || "";
      let currentYear = currentQuery.year_start;
      let currentQuarter = currentQuery.quarter_start + index;
      while (currentQuarter > 4) {
        currentQuarter -= 4;
        currentYear++;
      }
      const timePeriod = `${currentYear} Q${currentQuarter}`;
      return {
        timePeriod,
        logValue: logValue.toFixed(4),
        rorValue: rorValue.toFixed(4),
        lowerCI: lowerCI ? lowerCI.toFixed(4) : "",
        upperCI: upperCI ? upperCI.toFixed(4) : "",
      };
    }) || [];

  // download chart as PNG
  const downloadChart = () => {
    const chart = chartRef.current;
    if (chart) {
      const url = chart.toBase64Image("image/png", 1.0);
      const link = document.createElement("a");
      link.download = `${currentQuery.name.replace(/[^a-z0-9]/gi, "_")}_analysis.png`;
      link.href = url;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      showToastMessage("Chart downloaded successfully!");
    }
  };

  // download data as CSV
  const downloadData = () => {
    const headers = csvHeaders;
    const csvData = [headers.join(",")];

    const labels = (() => {
      const actualDataLength = currentQuery.result.ror_values ? currentQuery.result.ror_values.length : 0;
      const labels = [];
      let currentYear = currentQuery.year_start;
      let currentQuarter = currentQuery.quarter_start;

      for (let i = 0; i < actualDataLength; i++) {
        labels.push(`${currentYear} Q${currentQuarter}`);
        currentQuarter++;
        if (currentQuarter > 4) {
          currentQuarter = 1;
          currentYear++;
        }
      }
      return labels;
    })();

    currentQuery.result.ror_values.forEach((rorValue, index) => {
      const logValue = Math.log10(rorValue || 0.1);
      const lowerCI = currentQuery.result.ror_lower[index] || "";
      const upperCI = currentQuery.result.ror_upper[index] || "";
      const timePeriod = labels[index] || `Period ${index + 1}`;

      csvData.push(
        [
          `"${timePeriod}"`,
          logValue.toFixed(4),
          rorValue.toFixed(4),
          lowerCI ? lowerCI.toFixed(4) : "",
          upperCI ? upperCI.toFixed(4) : "",
        ].join(",")
      );
    });

    const csvContent = csvData.join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `${currentQuery.name.replace(/[^a-z0-9]/gi, "_")}_data.csv`
    );
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    showToastMessage("Data downloaded as CSV successfully!");
  };

  return (
    <div className="query-details-container">
      <div className="form-header">
        <h2>{currentQuery.name}</h2>
        <div className="query-details-actions">
          {hasResults && <span className="results-badge">✓ Results Ready</span>}
          <button type="button" className="cancel-button" onClick={handleNewQuery}>
            <FaTimes /> Close
          </button>
        </div>
      </div>

      {/* Query Information */}
      <div className="query-info-section">
        <h3>Query Information</h3>
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Time Period:</span>
            <span className="info-value">
              {currentQuery.year_start} Q{currentQuery.quarter_start} - {currentQuery.year_end} Q
              {currentQuery.quarter_end}
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Created:</span>
            <span className="info-value">
              {new Date(currentQuery.created_at).toLocaleDateString()}
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Status:</span>
            <span
              className={`info-value ${currentQuery.result.status === "completed"
                ? "status-completed"
                : currentQuery.result.status === "failed"
                  ? "status-failed"
                  : "status-pending"
                }`}
            >
              {currentQuery.result.status === "completed"
                ? "Analysis Complete"
                : currentQuery.result.status === "failed"
                  ? "Analysis Failed"
                  : "Processing..."}
            </span>
          </div>
        </div>
      </div>

      {/* Drugs */}
      <div className="query-section">
        <h3>Drugs ({currentQuery.drugs_details?.length || 0})</h3>
        {currentQuery.drugs_details && currentQuery.drugs_details.length > 0 ? (
          currentQuery.drugs_details.map((drug, index) => (
            <div key={index} className="item-tag drug-tag">{drug.name}</div>
          ))
        ) : (
          <p className="no-items">No drugs specified</p>
        )}
      </div>

      {/* Reactions */}
      <div className="query-section">
        <h3>Reactions ({currentQuery.reactions_details?.length || 0})</h3>
        {currentQuery.reactions_details && currentQuery.reactions_details.length > 0 ? (
          currentQuery.reactions_details.map((reaction, index) => (
            <div key={index} className="item-tag reaction-tag">{reaction.name}</div>
          ))
        ) : (
          <p className="no-items">No reactions specified</p>
        )}
      </div>

      {/* Results */}
      <div className="query-section">
        <div className="results-header">
          <h3>Statistical Analysis Results</h3>
          {hasResults && (
            <div className="chart-actions">
              <button
                className="download-button"
                onClick={downloadChart}
                disabled={isQueryLocked}
                title={isQueryLocked ? "Query is still processing. Download disabled." : "Download Chart"}
              >
                <FaFileImage style={{ marginRight: "6px" }} /> Download Chart
              </button>
              <button
                className="download-button"
                onClick={downloadData}
                disabled={isQueryLocked}
                title={isQueryLocked ? "Query is still processing. Download disabled." : "Download CSV"}
              >
                <FaFileCsv style={{ marginRight: "6px" }} /> Download CSV
              </button>
              <button
                className="download-button"
                onClick={() => setShowCsvModal(true)}
                title={isQueryLocked ? "Query is still processing. View CSV disabled." : "View CSV"}
                disabled={isQueryLocked}
              >
                <FaArrowDown style={{ marginRight: "6px" }} /> View CSV
              </button>
            </div>
          )}
        </div>

        {/* CSV Modal */}
        {showCsvModal && (
          <div className="csv-modal-overlay">
            <div className="csv-modal">
              <div className="csv-modal-header">
                <h3>CSV Preview - {currentQuery.name}</h3>
                <button
                  className="close-button"
                  onClick={() => setShowCsvModal(false)}
                >
                  <FaTimes />
                </button>
              </div>
              <div className="csv-modal-content">
                <table className="csv-table">
                  <thead>
                    <tr>
                      {csvHeaders.map((header, i) => (
                        <th key={i}>{header}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {csvRows.map((row, i) => (
                      <tr key={i}>
                        <td>{row.timePeriod}</td>
                        <td>{row.logValue}</td>
                        <td>{row.rorValue}</td>
                        <td>{row.lowerCI}</td>
                        <td>{row.upperCI}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        <div className="chart-placeholder">
          <div className="chart-container">
            {currentQuery?.result?.status === "completed" && hasResults ? (
              <RorChart
                query={currentQuery.result}
                year_start={currentQuery.year_start}
                quarter_start={currentQuery.quarter_start}
                ref={chartRef}
              />
            ) : currentQuery?.result?.status === "failed" ? (
              <div className="placeholder-content error-state">
                <div className="placeholder-icon">❌</div>
                <h4>Analysis Failed</h4>
                <p>
                  Unfortunately, your query processing failed. You can try refreshing the status,
                  or go back and re-run the query with different parameters.
                </p>
                <div className="refresh-button">
                  <button
                    className="secondary-button" onClick={handleRefreshStatus}
                  >
                    Retry Refresh
                  </button>
                </div>
              </div>
            ) : (
              <div className="placeholder-content">
                <div className="placeholder-icon">⏳</div>
                <h4>Analysis in Progress</h4>
                <p>
                  Your query is being processed. Results will appear here when ready.
                </p>
                <div className="refresh-button">
                  <button className="secondary-button" onClick={handleRefreshStatus}>
                    Refresh Status
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default QueryDetailsView;
