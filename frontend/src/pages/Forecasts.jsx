import React, { useState, useEffect, useRef } from 'react';
import { Box, Paper, Typography, CircularProgress, ToggleButtonGroup, ToggleButton } from '@mui/material';
import MapRoundedIcon from '@mui/icons-material/MapRounded';
import TimelineRoundedIcon from '@mui/icons-material/TimelineRounded';
import { gwaliorLocations } from '../mockData/gwaliorData';
import CityMap from '../components/CityMap';
import MetricCards from '../components/MetricCards';
import LocationSelector from '../components/LocationSelector';

// Inline forecast-specific chart
function ForecastChart({ data }) {
  const canvasRef = useRef(null);
  const chartRef  = useRef(null);

  useEffect(() => {
    if (!data?.length) return;
    const tryInit = (n = 0) => {
      if (!window.Chart) { if (n < 20) setTimeout(() => tryInit(n + 1), 250); return; }
      chartRef.current?.destroy();
      const ctx  = canvasRef.current.getContext('2d');
      const grad = ctx.createLinearGradient(0, 0, 0, 300);
      grad.addColorStop(0, 'rgba(99,102,241,0.28)');
      grad.addColorStop(1, 'rgba(99,102,241,0.02)');
      chartRef.current = new window.Chart(ctx, {
        type: 'line',
        data: {
          labels: data.map(d => `${String(new Date(d.time).getHours()).padStart(2,'0')}:00`),
          datasets: [{
            data: data.map(d => d.aqi),
            borderColor: '#6366f1',
            backgroundColor: grad,
            borderWidth: 2.5, fill: true, tension: 0.4,
            pointRadius: 3, pointBackgroundColor: '#6366f1', pointBorderColor: '#fff', pointBorderWidth: 1.5,
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 11 }, maxTicksLimit: 12 } },
            y: { grid: { color: '#f1f5f9' }, ticks: { color: '#94a3b8', font: { size: 11 } }, beginAtZero: false },
          },
        },
      });
    };
    tryInit();
    return () => chartRef.current?.destroy();
  }, [data]);

  return (
    <Box sx={{ position: 'relative', height: 340 }}>
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%' }} />
    </Box>
  );
}

export default function Forecasts() {
  const [selectedLocationId, setSelectedLocationId] = useState(gwaliorLocations[0].id);
  const [dataMap, setDataMap]   = useState({});
  const [loading, setLoading]   = useState(true);
  const [view, setView]         = useState('map'); // 'map' | 'chart'

  useEffect(() => {
    fetch('http://localhost:8000/api/predict_all')
      .then(r => r.json())
      .then(d => { setDataMap(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const selectedLocation    = gwaliorLocations.find(l => l.id === selectedLocationId);
  const selectedDataHistory = dataMap[selectedLocationId] ?? [];
  const currentData         = selectedDataHistory[0] ?? null;

  if (loading) return (
    <Box display="flex" alignItems="center" justifyContent="center" height="60vh" flexDirection="column" gap={2}>
      <CircularProgress size={52} sx={{ color: '#6366f1' }} />
      <Typography variant="h6" sx={{ color: '#64748b', fontWeight: 600 }}>Running XGBoost Predictions…</Typography>
      <Typography variant="body2" sx={{ color: '#94a3b8' }}>Forecasting 24 × 15 location-hours</Typography>
    </Box>
  );

  return (
    <Box sx={{ bgcolor: '#faf5ff', borderRadius: 4, border: '1px solid #ede9fe', p: { xs: 2, md: 3 }, minHeight: '85vh' }}>
      {/* Banner */}
      <Box sx={{
        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        borderRadius: 3, p: 3, color: '#fff', mb: 3,
      }}>
        <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>AI Air Quality Forecast</Typography>
        <Typography variant="body2" sx={{ opacity: 0.85 }}>
          XGBoost autoregressive model · 24-hour horizon · {gwaliorLocations.length} sensor locations
        </Typography>
      </Box>

      {/* Metric Cards */}
      <MetricCards selectedLocation={selectedLocation} currentData={currentData} isForecast />

      {/* Full-width Map / Chart toggle */}
      <Box
        sx={{
          mx: { xs: -2, md: -3 },
          px: { xs: 2, md: 3 },
          py: 0.75,
          bgcolor: 'transparent',
          borderTop: '1px solid #ddd6fe',
          borderBottom: '1px solid #ddd6fe',
          mb: 1.5,
        }}
      >
        <ToggleButtonGroup
          value={view}
          exclusive
          onChange={(_, v) => v && setView(v)}
          fullWidth
          sx={{
            '& .MuiToggleButton-root': {
              border: 'none',
              borderRadius: '8px !important',
              py: 0.75,
              fontWeight: 600,
              fontSize: '0.85rem',
              textTransform: 'none',
              color: '#7c3aed',
              '&.Mui-selected': {
                bgcolor: '#f3e8ff',
                color: '#6d28d9',
              },
            },
          }}
        >
          <ToggleButton value="map">
            <MapRoundedIcon sx={{ fontSize: 18, mr: 1 }} /> Map
          </ToggleButton>
          <ToggleButton value="chart">
            <TimelineRoundedIcon sx={{ fontSize: 18, mr: 1 }} /> Projection
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Map View — full width, no selector */}
      {view === 'map' && (
        <Paper sx={{ p: 0, overflow: 'hidden', border: '1px solid #ede9fe' }}>
          <Box sx={{ px: 2.5, pt: 2, pb: 1 }}>
            <Typography variant="h6" sx={{ color: '#4f46e5' }}>Forecast Heatmap</Typography>
            <Typography variant="caption" sx={{ color: '#a78bfa' }}>
              Predicted AQI for the first projected hour across all sensors
            </Typography>
          </Box>
          <Box sx={{ height: 520, px: 2, pb: 2 }}>
            <CityMap dataMap={dataMap} selectedLocationId={selectedLocationId} />
          </Box>
        </Paper>
      )}

      {/* Chart view — projection + right selector */}
      {view === 'chart' && (
        <Box sx={{ display: 'flex', gap: 2.5, alignItems: 'flex-start' }}>
          {/* Left: chart */}
          <Paper sx={{ flexGrow: 1, minWidth: 0, p: 3, border: '1px solid #ede9fe' }}>
            <Typography variant="h6" sx={{ color: '#4f46e5', mb: 0.25 }}>
              24-Hour AQI Projection — {selectedLocation?.name}
            </Typography>
            <Typography variant="caption" sx={{ color: '#a78bfa' }}>
              {selectedLocation?.description}
            </Typography>
            <Box mt={2}>
              <ForecastChart data={selectedDataHistory} />
            </Box>
          </Paper>
          {/* Right: sticky selector */}
          <Box sx={{ width: 256, flexShrink: 0, position: 'sticky', top: 80, maxHeight: 'calc(100vh - 96px)' }}>
            <LocationSelector
              selectedLocationId={selectedLocationId}
              onChange={setSelectedLocationId}
              dataMap={dataMap}
            />
          </Box>
        </Box>
      )}
    </Box>
  );
}
