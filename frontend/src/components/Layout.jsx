import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  AppBar, Box, Toolbar, Typography, ToggleButton, ToggleButtonGroup,
} from '@mui/material';
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded';
import TimelineRoundedIcon from '@mui/icons-material/TimelineRounded';
import logo from '../assets/logo.png';

export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();

  const currentTab = location.pathname.includes('/forecasts') ? '/forecasts' : '/dashboard';

  const handleRouteToggle = (_, newRoute) => {
    if (newRoute) navigate(newRoute);
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f0f2f5', display: 'flex', flexDirection: 'column' }}>
      <AppBar
        position="sticky"
        elevation={0}
        sx={{
          bgcolor: '#ffffff',
          borderBottom: '1px solid rgba(0,0,0,0.07)',
          color: '#0f172a',
          zIndex: 1200,
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-evenly', alignItems: 'center', px: { xs: 2, md: 4 }, minHeight: '64px !important' }}>
          <Box
            component="img"
            src={logo}
            alt="CityPulse"
            sx={{ height: 54, width: 'auto', objectFit: 'contain' }}
          />

          <ToggleButtonGroup
            value={currentTab}
            exclusive
            onChange={handleRouteToggle}
            aria-label="page navigation"
          >
            <ToggleButton value="/dashboard" aria-label="Live Dashboard">
              <DashboardRoundedIcon sx={{ fontSize: 17, mr: 0.75 }} />
              Live Dashboard
            </ToggleButton>
            <ToggleButton value="/forecasts" aria-label="AI Forecast">
              <TimelineRoundedIcon sx={{ fontSize: 17, mr: 0.75 }} />
              AI Forecast
            </ToggleButton>
          </ToggleButtonGroup>
        </Toolbar>
      </AppBar>

      <Box component="main" sx={{ flexGrow: 1, px: { xs: 2, md: 3 }, py: { xs: 2, md: 2.5 } }}>
        {children}
      </Box>
    </Box>
  );
}
