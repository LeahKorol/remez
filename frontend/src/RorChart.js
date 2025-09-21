// src/components/RorChart.js
import React, { useRef } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LineController,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import zoomPlugin from 'chartjs-plugin-zoom';

// רישום של כל הרכיבים והפלאגינים
ChartJS.register(
  LineElement,
  PointElement,
  LineController,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend,
  zoomPlugin
);

export default function RorChart({ query }) {
  const chartRef = useRef(null);

  const data = {
    labels: (() => {
      const length = query.ror_values?.length || 0;
      if (!length) return [];
      const labels = [];
      let year = query.year_start;
      let quarter = query.quarter_start;
      for (let i = 0; i < length; i++) {
        labels.push(`${year} Q${quarter}`);
        quarter++;
        if (quarter > 4) {
          quarter = 1;
          year++;
        }
      }
      return labels;
    })(),
    datasets: [
      {
        label: 'Lower CI',
        data: query.ror_lower.map(v => Math.log10(v || 0.1)),
        borderColor: '#7b61ff',
        borderDash: [3, 3],
        tension: 0.3,
        pointRadius: 0,
        fill: false,
      },
      {
        label: 'ROR (Log₁₀)',
        data: query.ror_values.map(v => Math.log10(v || 0.1)),
        borderColor: '#7b61ff',
        backgroundColor: 'rgba(123,97,255,0.2)',
        fill: '-1',
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Upper CI',
        data: query.ror_upper.map(v => Math.log10(v || 0.1)),
        borderColor: '#7b61ff',
        borderDash: [3, 3],
        tension: 0.3,
        pointRadius: 0,
        fill: '-1',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        title: { display: true, text: 'Time Period' },
        ticks: { font: { size: 11 } },
      },
      y: {
        title: { display: true, text: 'ROR (log₁₀)' },
        ticks: {
          callback: v => {
            const val = Math.pow(10, v);
            return val >= 1 ? val.toFixed(1) : val.toFixed(2);
          },
        },
      },
    },
    plugins: {
      legend: {
        position: 'top',
        labels: { usePointStyle: true, padding: 12 },
      },
      tooltip: {
        mode: 'index',
        intersect: false,
      },
      zoom: {
        pan: {
          enabled: true,
          mode: 'x',
          modifierKey: 'shift',
        },
        zoom: {
          wheel: { enabled: true },
          pinch: { enabled: true },
          mode: 'x',
        },
      },
    },
  };

  const zoomIn = () => chartRef.current?.zoom(1.3);
  const zoomOut = () => chartRef.current?.zoom(0.8);
  const resetZoom = () => chartRef.current?.resetZoom();

  return (
    <div style={{ height: 420 }}>
      <Line ref={chartRef} data={data} options={options} />
      <div style={{ marginTop: 8 }}>
        <button onClick={zoomIn}>🔍 Zoom In</button>
        <button onClick={zoomOut}>➖ Zoom Out</button>
        <button onClick={resetZoom}>🔄 Reset</button>
      </div>
    </div>
  );
}
