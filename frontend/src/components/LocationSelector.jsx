import React from 'react';
import { Box, Typography, Radio, RadioGroup, FormControlLabel, FormControl } from '@mui/material';
import SensorsRoundedIcon from '@mui/icons-material/SensorsRounded';
import { gwaliorLocations } from '../mockData/gwaliorData';

const AQI_COLOR = (aqi) => {
  if (!aqi)       return '#94a3b8';
  if (aqi <= 50)  return '#22c55e';
  if (aqi <= 100) return '#f59e0b';
  if (aqi <= 200) return '#ef4444';
  return '#a855f7';
};

export default function LocationSelector({ selectedLocationId, onChange, dataMap }) {
  return (
    <Box sx={{
      bgcolor: '#f8fafc',
      borderRadius: 3,
      border: '1px dashed #cbd5e1',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
    }}>
      {/* Header */}
      <Box sx={{
        px: 2,
        py: 1.5,
        bgcolor: '#f1f5f9',
        borderBottom: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'center',
        gap: 1,
      }}>
        <SensorsRoundedIcon sx={{ fontSize: 16, color: '#64748b' }} />
        <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.6px' }}>
          City Sensors
        </Typography>
      </Box>

      {/* Scrollable list */}
      <FormControl component="fieldset" sx={{ flexGrow: 1, minHeight: 0, overflowY: 'auto', overflowX: { xs: 'auto', md: 'hidden' }, px: { xs: 0, md: 1.5 }, py: 1 }}>
        <RadioGroup
          value={selectedLocationId}
          onChange={(e) => onChange(Number(e.target.value))}
          sx={{ display: 'flex', flexDirection: { xs: 'row', md: 'column' }, flexWrap: 'nowrap', px: { xs: 1.5, md: 0 } }}
        >
          {gwaliorLocations.map((loc) => {
            const locData  = dataMap?.[loc.id];
            const aqi      = locData?.[0]?.aqi;
            const color    = AQI_COLOR(aqi);
            const selected = selectedLocationId === loc.id;

            return (
              <FormControlLabel
                key={loc.id}
                value={loc.id}
                control={
                  <Radio
                    size="small"
                    sx={{
                      p: '5px',
                      color: '#cbd5e1',
                      '&.Mui-checked': { color: '#0ea5e9' },
                    }}
                  />
                }
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', gap: 1 }}>
                    <Typography sx={{
                      fontSize: '0.78rem',
                      fontWeight: selected ? 600 : 400,
                      color: selected ? '#0f172a' : '#64748b',
                      lineHeight: 1.3,
                    }}>
                      {loc.name}
                    </Typography>
                    {aqi !== undefined && (
                      <Typography sx={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        color,
                        minWidth: 26,
                        textAlign: 'right',
                        fontVariantNumeric: 'tabular-nums',
                      }}>
                        {Math.round(aqi)}
                      </Typography>
                    )}
                  </Box>
                }
                sx={{
                  mx: 0,
                  px: 0.75,
                  py: 0.25,
                  borderRadius: 1.5,
                  width: { xs: 'auto', md: '100%' },
                  minWidth: { xs: 'fit-content', md: 'auto' },
                  bgcolor: selected ? '#e0f2fe' : 'transparent',
                  transition: 'background-color 0.15s ease',
                  '&:hover': { bgcolor: selected ? '#e0f2fe' : '#f1f5f9' },
                  '& .MuiFormControlLabel-label': { flexGrow: 1, minWidth: 0 },
                }}
              />
            );
          })}
        </RadioGroup>
      </FormControl>
    </Box>
  );
}
