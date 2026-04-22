import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, CircularProgress, ToggleButtonGroup, ToggleButton } from '@mui/material';
import MapRoundedIcon from '@mui/icons-material/MapRounded';
import BarChartRoundedIcon from '@mui/icons-material/BarChartRounded';
import { gwaliorLocations } from '../mockData/gwaliorData';
import { api } from '../api';
import CityMap from '../components/CityMap';
import MetricCards from '../components/MetricCards';
import DashboardAnalytics from '../components/DashboardAnalytics';
import LocationSelector from '../components/LocationSelector';

export default function Dashboard() {
  const [selectedLocationId, setSelectedLocationId] = useState(gwaliorLocations[0].id);
  const [dataMap, setDataMap]     = useState({});
  const [loading, setLoading]     = useState(true);
  const [view, setView]           = useState('map');

  useEffect(() => {
    api.history()
      .then(r => r.json())
      .then(d => { setDataMap(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const selectedLocation    = gwaliorLocations.find(l => l.id === selectedLocationId);
  const selectedDataHistory = dataMap[selectedLocationId] ?? [];
  const currentData         = selectedDataHistory[0] ?? null;

  if (loading) return (
    <Box display="flex" alignItems="center" justifyContent="center" minHeight="calc(100vh - 200px)" flexDirection="column" gap={3}>
      <CircularProgress size={64} thickness={4.5} sx={{ color: '#0ea5e9', animationDuration: '0.8s' }} />
      <Box textAlign="center">
        <Typography variant="h6" sx={{ color: '#64748b', fontWeight: 600 }}>Loading live data…</Typography>
      </Box>
    </Box>
  );

  return (
    <Box>
      <MetricCards selectedLocation={selectedLocation} currentData={currentData} />

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
              '&:hover': { bgcolor: '#f1f5f9' },
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

      {view === 'charts' && (
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column-reverse', md: 'row' }, gap: 2.5, alignItems: 'flex-start' }}>
          <Box sx={{ flexGrow: 1, width: '100%', minWidth: 0 }}>
            <DashboardAnalytics data={selectedDataHistory} />
          </Box>
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
