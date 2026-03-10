import React, { useRef, useState, useEffect } from "react";
import { FaTimes, FaFileImage, FaFileCsv, FaArrowDown, FaInfoCircle } from "react-icons/fa";
import RorChart from "./RorChart";
import { showToastMessage } from "../utils/toast";
import "../Pages/UserProfile.css";

const QUARTER_RANGE_TOOLTIP =
  "The selected period includes the start quarter and excludes the end quarter. Example: 2023 Q1 to 2023 Q4 includes Q1-Q3 only, and does not include Q4.";

const QueryDetailsView = ({ query, handleNewQuery, refreshQuery, onQueryUpdate }) => {
  const chartRef = useRef(null);
  const [showCsvModal, setShowCsvModal] = useState(false);
  const [currentQuery, setCurrentQuery] = useState(query);

  useEffect(() => {
    setCurrentQuery(query);
  }, [query]);

  console.log("Rendering QueryDetailsView for:", currentQuery);
  console.log("status: ", currentQuery?.result?.status);

  const isQueryLocked =
    currentQuery?.result?.status !== "completed" &&
    currentQuery?.result?.status !== "failed";

  const NO_CORRELATION_BASELINE = 0.1;
  const BASELINE_EPSILON = 1e-9;

  const toFiniteNumber = (value) => {
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  };

  const isApproximately = (value, target, epsilon = BASELINE_EPSILON) =>
    Math.abs(value - target) <= epsilon;

  const getExpectedPointsCount = (queryData) => {
    const ys = Number(queryData?.year_start);
    const ye = Number(queryData?.year_end);
    const qs = Number(queryData?.quarter_start);
    const qe = Number(queryData?.quarter_end);

    if (
      !Number.isInteger(ys) ||
      !Number.isInteger(ye) ||
      !Number.isInteger(qs) ||
      !Number.isInteger(qe)
    ) {
      return 0;
    }

    const startIndex = ys * 4 + (qs - 1);
    const endIndex = ye * 4 + (qe - 1);
    if (endIndex < startIndex) return 0;

    return endIndex - startIndex + 1;
  };

  const buildChartResult = (queryData) => {
    const result = queryData?.result || {};
    const rorValues = Array.isArray(result?.ror_values) ? result.ror_values : [];

    if (rorValues.length > 0) {
      return result;
    }

    if (queryData?.result?.status !== "completed") {
      return result;
    }

    const fallbackPointsCount = getExpectedPointsCount(queryData);
    if (fallbackPointsCount <= 0) {
      return result;
    }

    const baselineValues = Array(fallbackPointsCount).fill(NO_CORRELATION_BASELINE);
    return {
      ...result,
      ror_values: baselineValues,
      ror_lower: [...baselineValues],
      ror_upper: [...baselineValues],
    };
  };

  const isBaselineNoCorrelation = (queryData) => {
    const values = Array.isArray(queryData?.result?.ror_values)
      ? queryData.result.ror_values
      : [];
    const lower = Array.isArray(queryData?.result?.ror_lower)
      ? queryData.result.ror_lower
      : [];
    const upper = Array.isArray(queryData?.result?.ror_upper)
      ? queryData.result.ror_upper
      : [];

    if (values.length === 0) return false;

    const hasAtLeastOneBaselinePoint = values.some((value) => {
      const ror = toFiniteNumber(value);
      return ror !== null && isApproximately(ror, NO_CORRELATION_BASELINE);
    });

    if (!hasAtLeastOneBaselinePoint) return false;

    return values.every((value, index) => {
      const ror = toFiniteNumber(value);
      const low = toFiniteNumber(lower[index]);
      const high = toFiniteNumber(upper[index]);

      if (ror === null || !isApproximately(ror, NO_CORRELATION_BASELINE)) {
        return false;
      }

      const lowerMatches =
        low === null || isApproximately(low, NO_CORRELATION_BASELINE);
      const upperMatches =
        high === null || isApproximately(high, NO_CORRELATION_BASELINE);

      return lowerMatches && upperMatches;
    });
  };

  const hasMeaningfulSignal = (queryData) => {
    const values = Array.isArray(queryData?.result?.ror_values)
      ? queryData.result.ror_values
      : [];
    const lower = Array.isArray(queryData?.result?.ror_lower)
      ? queryData.result.ror_lower
      : [];
    const upper = Array.isArray(queryData?.result?.ror_upper)
      ? queryData.result.ror_upper
      : [];

    if (values.length === 0) return false;
    if (isBaselineNoCorrelation(queryData)) return false;

    return values.some((value, index) => {
      const ror = toFiniteNumber(value);
      const low = toFiniteNumber(lower[index]);
      const high = toFiniteNumber(upper[index]);
      return (
        (ror !== null && ror > 0) ||
        (low !== null && low > 0) ||
        (high !== null && high > 0)
      );
    });
  };

  const isCompleted = currentQuery?.result?.status === "completed";
  const chartResult = buildChartResult(currentQuery);
  const hasChartData =
    isCompleted &&
    Array.isArray(chartResult?.ror_values) &&
    chartResult.ror_values.length > 0;
  const hasResults =
    hasChartData && hasMeaningfulSignal({ ...currentQuery, result: chartResult });
  const isNoCorrelationResult = hasChartData && !hasResults;

  const selectedDrugsText =
    currentQuery?.drugs_details?.map((drug) => drug.name).join(", ") ||
    "selected drugs";
  const selectedReactionsText =
    currentQuery?.reactions_details?.map((reaction) => reaction.name).join(", ") ||
    "selected reactions";

  const handleRefreshStatus = async () => {
    if (!refreshQuery) return;
    try {
      const fullQuery = await refreshQuery(currentQuery.id);
      console.log("Refreshed query:", fullQuery);

      setCurrentQuery(fullQuery);

      if (onQueryUpdate) {
        onQueryUpdate(fullQuery);
      }

      if (fullQuery.result?.status === "completed") {
        const fullQueryChartResult = buildChartResult(fullQuery);
        if (hasMeaningfulSignal({ ...fullQuery, result: fullQueryChartResult })) {
          showToastMessage("Analysis completed! Results are now available.");
        } else {
          showToastMessage(
            "Analysis completed with no statistically meaningful signal.",
            "warning"
          );
        }
      } else if (fullQuery.result?.status === "failed") {
        showToastMessage(
          "Query failed during processing. Please try again.",
          "error"
        );
      } else {
        showToastMessage("Query still processing, try again soon.");
      }
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
    chartResult?.ror_values?.map((rorValue, index) => {
      const safeRor = toFiniteNumber(rorValue);
      const lowerCI = toFiniteNumber(chartResult?.ror_lower?.[index]);
      const upperCI = toFiniteNumber(chartResult?.ror_upper?.[index]);
      const logValue = safeRor && safeRor > 0 ? Math.log10(safeRor) : null;
      let currentYear = currentQuery.year_start;
      let currentQuarter = currentQuery.quarter_start + index;
      while (currentQuarter > 4) {
        currentQuarter -= 4;
        currentYear++;
      }
      const timePeriod = `${currentYear} Q${currentQuarter}`;
      return {
        timePeriod,
        logValue: logValue !== null ? logValue.toFixed(4) : "",
        rorValue: safeRor !== null ? safeRor.toFixed(4) : "",
        lowerCI: lowerCI !== null ? lowerCI.toFixed(4) : "",
        upperCI: upperCI !== null ? upperCI.toFixed(4) : "",
      };
    }) || [];

  const downloadChart = () => {
    const chartComponent = chartRef.current?.getChart?.();

    if (!chartComponent) {
      showToastMessage("Chart not ready yet.", "warning");
      return;
    }

    const chartImage = chartComponent.toBase64Image("image/png", 1.0);
    const image = new Image();
    image.src = chartImage;

    image.onload = () => {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      const padding = 80;
      const logoHeight = 40;
      canvas.width = image.width;
      canvas.height = image.height + padding + logoHeight;
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.drawImage(image, 0, 0);

      const gradient = ctx.createLinearGradient(
        canvas.width * 0.3,
        image.height + 10,
        canvas.width * 0.7,
        image.height + 10
      );
      gradient.addColorStop(0, "#7b42e0");
      gradient.addColorStop(1, "#5e68f1");

      ctx.font = "bold 36px Arial";
      ctx.fillStyle = gradient;
      ctx.textAlign = "center";
      ctx.shadowColor = "rgba(0, 0, 0, 0.2)";
      ctx.shadowBlur = 6;
      ctx.shadowOffsetY = 2;
      ctx.fillText("REMEZ", canvas.width / 2, image.height + logoHeight);

      ctx.shadowBlur = 0;
      ctx.font = "16px Arial";
      ctx.fillStyle = "#7b61ff";
      ctx.fillText(
        "REMEZ - Risk Evaluation & Monitoring of Emerging Signals",
        canvas.width / 2,
        image.height + logoHeight + 24
      );

      const finalURL = canvas.toDataURL("image/png");
      const link = document.createElement("a");
      link.download = `${currentQuery.name.replace(/[^a-z0-9]/gi, "_")}_REMEZ_chart.png`;
      link.href = finalURL;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      showToastMessage("Chart downloaded successfully!", "success");
    };
  };

  const downloadData = () => {
    const headers = csvHeaders;
    const csvData = [headers.join(",")];

    const labels = (() => {
      const actualDataLength = chartResult?.ror_values ? chartResult.ror_values.length : 0;
      const resultLabels = [];
      let currentYear = currentQuery.year_start;
      let currentQuarter = currentQuery.quarter_start;

      for (let i = 0; i < actualDataLength; i++) {
        resultLabels.push(`${currentYear} Q${currentQuarter}`);
        currentQuarter++;
        if (currentQuarter > 4) {
          currentQuarter = 1;
          currentYear++;
        }
      }
      return resultLabels;
    })();

    (chartResult?.ror_values || []).forEach((rorValue, index) => {
      const safeRor = toFiniteNumber(rorValue);
      const lowerCI = toFiniteNumber(chartResult?.ror_lower?.[index]);
      const upperCI = toFiniteNumber(chartResult?.ror_upper?.[index]);
      const logValue = safeRor && safeRor > 0 ? Math.log10(safeRor) : null;
      const timePeriod = labels[index] || `Period ${index + 1}`;

      csvData.push(
        [
          `"${timePeriod}"`,
          logValue !== null ? logValue.toFixed(4) : "",
          safeRor !== null ? safeRor.toFixed(4) : "",
          lowerCI !== null ? lowerCI.toFixed(4) : "",
          upperCI !== null ? upperCI.toFixed(4) : "",
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
          {hasChartData && <span className="results-badge">Results Ready</span>}
          <button type="button" className="cancel-button" onClick={handleNewQuery}>
            <FaTimes /> Close
          </button>
        </div>
      </div>

      <div className="query-info-section">
        <h3>Query Information</h3>
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label info-label-with-tooltip">
              <span>Time Period:</span>
              <button
                type="button"
                className="info-tooltip-trigger"
                data-tooltip={QUARTER_RANGE_TOOLTIP}
                aria-label="Time period uses an exclusive end quarter"
              >
                <FaInfoCircle />
              </button>
            </span>
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
              className={`info-value ${
                currentQuery.result.status === "completed"
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

      <div className="query-section">
        <h3>Drugs ({currentQuery.drugs_details?.length || 0})</h3>
        {currentQuery.drugs_details && currentQuery.drugs_details.length > 0 ? (
          currentQuery.drugs_details.map((drug, index) => (
            <div key={index} className="item-tag drug-tag">
              {drug.name}
            </div>
          ))
        ) : (
          <p className="no-items">No drugs specified</p>
        )}
      </div>

      <div className="query-section">
        <h3>Reactions ({currentQuery.reactions_details?.length || 0})</h3>
        {currentQuery.reactions_details && currentQuery.reactions_details.length > 0 ? (
          currentQuery.reactions_details.map((reaction, index) => (
            <div key={index} className="item-tag reaction-tag">
              {reaction.name}
            </div>
          ))
        ) : (
          <p className="no-items">No reactions specified</p>
        )}
      </div>

      <div className="query-section">
        <div className="results-header">
          <h3>Statistical Analysis Results</h3>
          {hasChartData && (
            <div className="chart-actions">
              <button
                className="download-button"
                onClick={downloadChart}
                disabled={isQueryLocked}
                title={
                  isQueryLocked
                    ? "Query is still processing. Download disabled."
                    : "Download Chart"
                }
              >
                <FaFileImage style={{ marginRight: "6px" }} /> Download Chart
              </button>
              <button
                className="download-button"
                onClick={downloadData}
                disabled={isQueryLocked}
                title={
                  isQueryLocked
                    ? "Query is still processing. Download disabled."
                    : "Download CSV"
                }
              >
                <FaFileCsv style={{ marginRight: "6px" }} /> Download CSV
              </button>
              <button
                className="download-button"
                onClick={() => setShowCsvModal(true)}
                title={
                  isQueryLocked
                    ? "Query is still processing. View CSV disabled."
                    : "View CSV"
                }
                disabled={isQueryLocked}
              >
                <FaArrowDown style={{ marginRight: "6px" }} /> View CSV
              </button>
            </div>
          )}
        </div>

        {showCsvModal && (
          <div className="csv-modal-overlay">
            <div className="csv-modal">
              <div className="csv-modal-header">
                <h3>CSV Preview - {currentQuery.name}</h3>
                <button className="close-button" onClick={() => setShowCsvModal(false)}>
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
            {currentQuery?.result?.status === "completed" && hasChartData ? (
              <>
                <RorChart
                  key={`${currentQuery.id}-${currentQuery.result?.id}-${chartResult?.ror_values?.length || 0}`}
                  query={chartResult}
                  year_start={currentQuery.year_start}
                  quarter_start={currentQuery.quarter_start}
                  ref={chartRef}
                />
                {isNoCorrelationResult && (
                  <p className="no-correlation-note">
                    No statistical signal was found between the selected drugs ({selectedDrugsText}) and
                    reactions ({selectedReactionsText}) for the chosen time period.
                  </p>
                )}
              </>
            ) : currentQuery?.result?.status === "completed" && !hasChartData ? (
              <div className="placeholder-content empty-state">
                <div className="placeholder-icon">📊</div>
                <h4>Analysis Completed</h4>
                <p>
                  The analysis finished successfully, but no statistical results were generated.
                  This may happen when no significant data was found for the selected parameters.
                </p>
                <div className="refresh-button">
                  <button className="secondary-button" onClick={handleRefreshStatus}>
                    Refresh Again
                  </button>
                </div>
              </div>
            ) : currentQuery?.result?.status === "failed" ? (
              <div className="placeholder-content error-state">
                <div className="placeholder-icon">❌</div>
                <h4>Analysis Failed</h4>
                <p>
                  Unfortunately, your query processing failed. You can try refreshing the status,
                  or go back and re-run the query with different parameters.
                </p>
                <div className="refresh-button">
                  <button className="secondary-button" onClick={handleRefreshStatus}>
                    Retry Refresh
                  </button>
                </div>
              </div>
            ) : (
              <div className="placeholder-content">
                <div className="placeholder-icon">⏳</div>
                <h4>Analysis in Progress</h4>
                <p>Your query is being processed. Results will appear here when ready.</p>
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


