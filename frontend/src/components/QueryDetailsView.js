import React, { useRef, useState } from "react";
import { FaTimes, FaFileImage, FaFileCsv, FaArrowDown } from "react-icons/fa";
import RorChart from "./RorChart";
import "../Pages/UserProfile.css";
import { showToastMessage } from "../utils/toast";

const QueryDetailsView = ({ query, handleNewQuery }) => {
  const chartRef = useRef(null);
  const [showCsvModal, setShowCsvModal] = useState(false);

  console.log("Rendering QueryDetailsView for:", query);

  const hasResults =
    query.result &&
    query.result.ror_values &&
    query.result.ror_values.length > 0 &&
    query.result.ror_lower &&
    query.result.ror_upper;

  const csvHeaders = [
    "Time Period",
    "ROR (Log10)",
    "ROR (Original)",
    "Lower CI",
    "Upper CI",
  ];

  const csvRows =
    query.result?.ror_values?.map((rorValue, index) => {
      const logValue = Math.log10(rorValue || 0.1);
      const lowerCI = query.result.ror_lower[index] || "";
      const upperCI = query.result.ror_upper[index] || "";
      let currentYear = query.year_start;
      let currentQuarter = query.quarter_start + index;
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
      link.download = `${query.name.replace(/[^a-z0-9]/gi, "_")}_analysis.png`;
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
      const actualDataLength = query.result.ror_values ? query.result.ror_values.length : 0;
      const labels = [];
      let currentYear = query.year_start;
      let currentQuarter = query.quarter_start;

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

    query.result.ror_values.forEach((rorValue, index) => {
      const logValue = Math.log10(rorValue || 0.1);
      const lowerCI = query.result.ror_lower[index] || "";
      const upperCI = query.result.ror_upper[index] || "";
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
      `${query.name.replace(/[^a-z0-9]/gi, "_")}_data.csv`
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
        <h2>{query.name}</h2>
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
              {query.year_start} Q{query.quarter_start} - {query.year_end} Q
              {query.quarter_end}
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Created:</span>
            <span className="info-value">
              {new Date(query.created_at).toLocaleDateString()}
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Status:</span>
            <span className="info-value">
              {hasResults ? "Analysis Complete" : "Processing..."}
            </span>
          </div>
        </div>
      </div>

      {/* Drugs */}
      <div className="query-section">
        <h3>Drugs ({query.drugs_details?.length || 0})</h3>
        {query.drugs_details && query.drugs_details.length > 0 ? (
          query.drugs_details.map((drug, index) => (
            <div key={index} className="item-tag drug-tag">{drug.name}</div>
          ))
        ) : (
          <p className="no-items">No drugs specified</p>
        )}
      </div>

      {/* Reactions */}
      <div className="query-section">
      <h3>Reactions ({query.reactions_details?.length || 0})</h3>
        {query.reactions_details && query.reactions_details.length > 0 ? (
          query.reactions_details.map((reaction, index) => (
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
              <button className="download-button" onClick={downloadChart}>
                <FaFileImage style={{ marginRight: "6px" }} /> Download Chart
              </button>
              <button className="download-button" onClick={downloadData}>
                <FaFileCsv style={{ marginRight: "6px" }} /> Download CSV
              </button>
              <button
                className="download-button"
                onClick={() => setShowCsvModal(true)}
                title="View CSV"
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
                <h3>CSV Preview - {query.name}</h3>
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
            {hasResults ? (
              <RorChart query={query} ref={chartRef} />
            ) : (
              <div className="placeholder-content">
                <div className="placeholder-icon">⏳</div>
                <h4>Analysis in Progress</h4>
                <p>
                  Your query is being processed. Results will appear here when ready.
                </p>
                <div className="refresh-button">
                  <button
                    className="secondary-button"
                    onClick={() => window.location.reload()}
                  >
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
