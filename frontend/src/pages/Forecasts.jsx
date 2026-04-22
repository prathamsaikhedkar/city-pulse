import React, { useState, useEffect, useRef } from 'react';
import { Box, Paper, Typography, CircularProgress, ToggleButtonGroup, ToggleButton } from '@mui/material';
import MapRoundedIcon from '@mui/icons-material/MapRounded';
import TimelineRoundedIcon from '@mui/icons-material/TimelineRounded';
import { gwaliorLocations } from '../mockData/gwaliorData';
import { api } from '../api';
import CityMap from '../components/CityMap';
import MetricCards from '../components/MetricCards';
import LocationSelector from '../components/LocationSelector';

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
  const [view, setView]         = useState('map');

  useEffect(() => {
    api.predictAll()
      .then(r => r.json())
      .then(d => { setDataMap(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const selectedLocation    = gwaliorLocations.find(l => l.id === selectedLocationId);
  const selectedDataHistory = dataMap[selectedLocationId] ?? [];
  const currentData         = selectedDataHistory[0] ?? null;

  if (loading) return (
    <Box display="flex" alignItems="center" justifyContent="center" minHeight="calc(100vh - 200px)" flexDirection="column" gap={3}>
      <CircularProgress size={64} thickness={4.5} sx={{ color: '#6366f1', animationDuration: '0.8s' }} />
      <Box textAlign="center">
        <Typography variant="h6" sx={{ color: '#64748b', fontWeight: 600 }}>Analyzing Air Quality Trends…</Typography>
        <Typography variant="body2" sx={{ color: '#94a3b8', mt: 0.5 }}>Forecasting 24 × 15 location-hours</Typography>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ bgcolor: '#faf5ff', borderRadius: 4, border: '1px solid #ede9fe', p: { xs: 2, md: 3 }, minHeight: '85vh' }}>
      <Box sx={{
        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        borderRadius: 3, p: 3, color: '#fff', mb: 3,
      }}>
        <Typography variant="h5" sx={{ fontWeight: 800 }}>AI Air Quality Forecast</Typography>
      </Box>

      <MetricCards selectedLocation={selectedLocation} currentData={currentData} isForecast />

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
              '&:hover': { bgcolor: '#f1f5f9' },
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

      {view === 'chart' && (
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column-reverse', md: 'row' }, gap: 2.5, alignItems: 'flex-start' }}>
          <Paper sx={{ flexGrow: 1, width: '100%', minWidth: 0, p: { xs: 2, md: 3 }, border: '1px solid #ede9fe' }}>
            <Typography variant="h6" sx={{ color: '#4f46e5', mb: 0.25 }}>
              24-Hour AQI Projection — {selectedLocation?.name}
            </Typography>
            <Box mt={3}>
              <ForecastChart data={selectedDataHistory} />
            </Box>
          </Paper>
          <Box sx={{ 
            width: { xs: '100%', md: 256 }, 
            flexShrink: 0, 
            position: { md: 'sticky' }, 
            top: 80, 
            maxHeight: { xs: 80, md: 'calc(100vh - 96px)' } 
          }}>
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
