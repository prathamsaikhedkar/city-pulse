import React from 'react';
import { Box, Typography, Grid } from '@mui/material';
import AirRoundedIcon from '@mui/icons-material/AirRounded';
import ThermostatRoundedIcon from '@mui/icons-material/ThermostatRounded';
import WaterDropRoundedIcon from '@mui/icons-material/WaterDropRounded';
import ScatterPlotRoundedIcon from '@mui/icons-material/ScatterPlotRounded';

const AQI_META = (aqi) => {
  if (aqi <= 50)  return { label: 'Good',     color: '#22c55e', bg: '#f0fdf4', badge: '#dcfce7' };
  if (aqi <= 100) return { label: 'Moderate',  color: '#f59e0b', bg: '#fffbeb', badge: '#fef3c7' };
  if (aqi <= 200) return { label: 'Poor',      color: '#ef4444', bg: '#fef2f2', badge: '#fee2e2' };
  return            { label: 'Severe',  color: '#a855f7', bg: '#faf5ff', badge: '#f3e8ff' };
};

function StatCard({ icon: Icon, iconColor, label, value, unit, sub }) {
  return (
    <Box sx={{
      bgcolor: '#fff',
      borderRadius: 3,
      border: '1px solid rgba(0,0,0,0.06)',
      p: 2.5,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      textAlign: 'center',
      gap: 1.5,
      boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      height: '100%',
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
        <Box sx={{
          bgcolor: `${iconColor}15`,
          borderRadius: 2,
          p: 1,
          display: 'flex',
          alignItems: 'center',
        }}>
          <Icon sx={{ fontSize: 20, color: iconColor }} />
        </Box>
        <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {label}
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: 0.5 }}>
        <Typography sx={{ fontSize: '1.7rem', fontWeight: 800, color: '#0f172a', lineHeight: 1 }}>
          {value}
        </Typography>
        {unit && <Typography variant="body2" sx={{ color: '#94a3b8', fontWeight: 500 }}>{unit}</Typography>}
      </Box>
      {sub && <Typography variant="caption" sx={{ color: '#64748b' }}>{sub}</Typography>}
    </Box>
  );
}

export default function MetricCards({ selectedLocation, currentData, isForecast = false }) {
  if (!currentData || !selectedLocation) return null;

  const aqiVal = Math.round(currentData.aqi ?? 0);
  const meta   = AQI_META(aqiVal);
  const mdCols = isForecast ? 4 : 3;

  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 4, '& > *': { flex: 1, minWidth: { xs: '100%', sm: 220 } } }}>
      <Box>
        <Box sx={{
          bgcolor: meta.bg,
          borderRadius: 3,
          border: `1px solid ${meta.badge}`,
          p: 2.5,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: 1.5,
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
            <Box sx={{ bgcolor: meta.badge, borderRadius: 2, p: 0.75, display: 'flex' }}>
              <AirRoundedIcon sx={{ fontSize: 20, color: meta.color }} />
            </Box>
            <Typography variant="caption" sx={{ color: meta.color, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Air Quality Index
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: 1 }}>
            <Typography sx={{ fontSize: '2.4rem', fontWeight: 800, color: meta.color, lineHeight: 1 }}>
              {aqiVal}
            </Typography>
            <Box sx={{ bgcolor: meta.badge, borderRadius: '20px', px: 1.5, py: 0.25 }}>
              <Typography variant="caption" sx={{ fontWeight: 700, color: meta.color }}>
                {meta.label}
              </Typography>
            </Box>
          </Box>
          <Typography variant="caption" sx={{ color: '#64748b' }}>
            {selectedLocation.name}
          </Typography>
        </Box>
      </Box>

      {!isForecast && (
        <Box>
          <StatCard
            icon={ScatterPlotRoundedIcon}
            iconColor="#6366f1"
            label="Particulates"
            value={currentData.pm2_5 !== undefined ? `${currentData.pm2_5.toFixed(1)} / ${currentData.pm10?.toFixed(1)}` : 'N/A'}
            unit={currentData.pm2_5 !== undefined ? 'µg/m³' : ''}
            sub={currentData.pm2_5 !== undefined ? 'PM2.5 / PM10' : 'No data'}
          />
        </Box>
      )}

      <Box>
        <StatCard
          icon={ThermostatRoundedIcon}
          iconColor="#ef4444"
          label="Temperature"
          value={currentData.temperature?.toFixed(1) ?? '—'}
          unit="°C"
          sub="Current ambient temperature"
        />
      </Box>

      <Box>
        <StatCard
          icon={WaterDropRoundedIcon}
          iconColor="#0ea5e9"
          label="Humidity"
          value={currentData.humidity?.toFixed(0) ?? '—'}
          unit="%"
          sub="Relative humidity"
        />
      </Box>
    </Box>
  );
}
