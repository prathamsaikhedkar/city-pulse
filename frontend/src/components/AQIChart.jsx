import React, { useEffect, useRef } from 'react';
import { Box, Typography } from '@mui/material';

export default function AQIChart({ data, locationName, chartColor = '#2e7d32', backgroundColor = 'rgba(46, 125, 50, 0.1)' }) {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!data || data.length === 0 || !window.Chart) return;

    const ctx = chartRef.current.getContext('2d');
    
    const sortedData = [...data].reverse();

    const labels = sortedData.map(d => {
      const date = new Date(d.time);
      return `${date.getHours()}:00`;
    });

    const aqiValues = sortedData.map(d => d.aqi);

    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    chartInstance.current = new window.Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: `AQI - ${locationName}`,
          data: aqiValues,
          borderColor: chartColor,
          backgroundColor: backgroundColor,
          borderWidth: 2,
          fill: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
          }
        },
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [data, locationName, chartColor, backgroundColor]);

  return (
    <Box sx={{ height: '350px', width: '100%', mt: 2 }}>
      <canvas ref={chartRef}></canvas>
    </Box>
  );
}
