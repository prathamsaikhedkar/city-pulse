import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, CircularProgress, ToggleButtonGroup, ToggleButton } from '@mui/material';
import MapRoundedIcon from '@mui/icons-material/MapRounded';
import BarChartRoundedIcon from '@mui/icons-material/BarChartRounded';
import { gwaliorLocations } from '../mockData/gwaliorData';
import CityMap from '../components/CityMap';
import MetricCards from '../components/MetricCards';
import DashboardAnalytics from '../components/DashboardAnalytics';
import LocationSelector from '../components/LocationSelector';

export default function Dashboard() {
  const [selectedLocationId, setSelectedLocationId] = useState(gwaliorLocations[0].id);
  const [dataMap, setDataMap]     = useState({});
  const [loading, setLoading]     = useState(true);
  const [view, setView]           = useState('map'); // 'map' | 'charts'

  useEffect(() => {
    fetch('http://localhost:8000/api/history')
      .then(r => r.json())
      .then(d => { setDataMap(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const selectedLocation    = gwaliorLocations.find(l => l.id === selectedLocationId);
  const selectedDataHistory = dataMap[selectedLocationId] ?? [];
  const currentData         = selectedDataHistory[0] ?? null;

  if (loading) return (
    <Box display="flex" alignItems="center" justifyContent="center" height="60vh" flexDirection="column" gap={2}>
      <CircularProgress sx={{ color: '#0ea5e9' }} />
      <Typography variant="body2" sx={{ color: '#94a3b8' }}>Loading live data…</Typography>
    </Box>
  );

  return (
    <Box>
      {/* Metric Cards */}
      <MetricCards selectedLocation={selectedLocation} currentData={currentData} />

      {/* Full-width Map / Charts toggle */}
      <Box
        sx={{
          mx: { xs: -2, md: -3 },
          px: { xs: 2, md: 3 },
          py: 0.75,
          bgcolor: 'transparent',
          borderTop: '1px solid rgba(0,0,0,0.06)',
          borderBottom: '1px solid rgba(0,0,0,0.06)',
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
              color: '#64748b',
              textTransform: 'none',
              '&.Mui-selected': {
                bgcolor: '#f0f9ff',
                color: '#0ea5e9',
              },
            },
          }}
        >
          <ToggleButton value="map">
            <MapRoundedIcon sx={{ fontSize: 18, mr: 1 }} /> Map
          </ToggleButton>
          <ToggleButton value="charts">
            <BarChartRoundedIcon sx={{ fontSize: 18, mr: 1 }} /> Analytics
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Map View — full width, no selector */}
      {view === 'map' && (
        <Paper sx={{ p: 0, overflow: 'hidden' }}>
          <Box sx={{ px: 2.5, pt: 2, pb: 1 }}>
            <Typography variant="h6">Live Air Quality Map</Typography>
            <Typography variant="caption" sx={{ color: '#94a3b8' }}>
              Click a marker for a quick snapshot
            </Typography>
          </Box>
          <Box sx={{ height: 520, px: 2, pb: 2 }}>
            <CityMap dataMap={dataMap} selectedLocationId={selectedLocationId} />
          </Box>
        </Paper>
      )}

      {/* Analytics View — charts + right selector */}
      {view === 'charts' && (
        <Box sx={{ display: 'flex', gap: 2.5, alignItems: 'flex-start' }}>
          {/* Left: charts */}
          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <DashboardAnalytics data={selectedDataHistory} />
          </Box>
          {/* Right: sticky sensor selector */}
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
