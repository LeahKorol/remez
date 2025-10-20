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
import './RorChart.css';

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

export default function RorChart({ query, year_start, quarter_start }) {
    const chartRef = useRef(null);

    if (!query || !query.ror_values) return null;

    const labels = (() => {
        const length = query.ror_values.length;
        const arr = [];
        let year = year_start;
        let q = quarter_start;
        for (let i = 0; i < length; i++) {
            arr.push(`${year} Q${q}`);
            q++;
            if (q > 4) {
                q = 1;
                year++;
            }
        }
        return arr;
    })();

    const data = {
        labels,
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
                backgroundColor: 'rgba(123,97,255,0.2)',
                borderDash: [3, 3],
                tension: 0.3,
                pointRadius: 0,
                fill: '-1',
            },
        ],
    };

    // Chart configuration
    const options = {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
            padding: {
                left: 0,
                right: 20,
                top: 20,
                bottom: 0
            }
        },
        animation: {
            duration: 500,
            easing: 'easeOutCubic'
        },
        plugins: {
            legend: {
                position: 'top',
                labels: { usePointStyle: true, padding: 12 },
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                callbacks: {
                    label: ctx => {
                        const raw = Math.pow(10, ctx.parsed.y);
                        return `${ctx.dataset.label}: ${raw.toFixed(3)} (log₁₀: ${ctx.parsed.y.toFixed(3)})`;
                    },
                },
            },
            zoom: {
                pan: {
                    enabled: true,
                    mode: 'x',
                    speed: 8,
                    threshold: 5,
                    decelerate: true
                },
                zoom: {
                    wheel: { enabled: false },
                    pinch: { enabled: false },
                    mode: 'x',
                    drag: { enabled: false }
                },
            },
        },
        scales: {
            x: {
                title: { display: true, text: 'Time Period' },
                ticks: { font: { size: 11 } },
                offset: false,
                grid: {
                    offset: false,
                    drawOnChartArea: true,
                },
                border: {
                    display: true,
                },
            },
            y: {
                title: { display: true, text: 'ROR (log₁₀)' },
                ticks: {
                    callback: v => {
                        const val = Math.pow(10, v);
                        return val.toFixed(2);
                    },
                },
                grid: {
                    offset: false,
                    drawOnChartArea: true,
                },
                border: {
                    display: true,
                },
            },
        },
    };

    // Zoom controls - With smooth animation
    const zoomIn = () => {
        const chart = chartRef.current;
        if (!chart) return;

        const scale = chart.scales.x;
        const currentMin = scale.min;
        const currentMax = scale.max;
        const centerValue = (currentMax + currentMin) / 2;
        const currentRange = (currentMax - currentMin) / 2;
        const newRange = currentRange / 1.5; // zoom factor

        // Set new zoom level with animation
        scale.options.min = centerValue - newRange;
        scale.options.max = centerValue + newRange;
        chart.update('active'); // 'active' gives smooth animation
    };

    const resetZoom = () => {
        const chart = chartRef.current;
        if (!chart) return;

        // Reset with smooth animation
        chart.resetZoom('active');
    };

    return (
        <div className="ror-chart-wrapper">
            <Line ref={chartRef} data={data} options={options} />
            <div className="zoom-controls">
                <button className="zoom-btn primary" onClick={zoomIn}>
                    Zoom
                </button>
                <button className="zoom-btn secondary" onClick={resetZoom}>
                    Reset
                </button>
            </div>
            <p className="drag-hint">Click and drag to move the chart</p>
        </div>
    );
}