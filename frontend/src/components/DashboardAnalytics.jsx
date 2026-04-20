import React, { useEffect, useRef } from 'react';
import { Box, Grid, Paper, Typography } from '@mui/material';

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {},
};

function ChartCard({ title, sub, height = 220, children }) {
  return (
    <Paper sx={{ p: 2.5, height: '100%' }}>
      <Typography variant="subtitle1" sx={{ color: '#0f172a', mb: 0.25 }}>{title}</Typography>
      {sub && <Typography variant="caption" sx={{ color: '#94a3b8' }}>{sub}</Typography>}
      <Box sx={{ position: 'relative', height, mt: 1.5 }}>
        {children}
      </Box>
    </Paper>
  );
}

export default function DashboardAnalytics({ data }) {
  const refs = {
    trend:    useRef(null),
    radar:    useRef(null),
    weather:  useRef(null),
    donut:    useRef(null),
    stack:    useRef(null),
    diurnal:  useRef(null),
  };
  const charts = useRef({});

  useEffect(() => {
    if (!data?.length) return;

    // CDN script may not be ready yet — poll until available
    let attempts = 0;
    const tryInit = () => {
      if (!window.Chart) {
        if (attempts++ < 20) setTimeout(tryInit, 250);
        return;
      }
      initCharts();
    };

    let cleanup = () => {};

    const initCharts = () => {
    Object.values(charts.current).forEach(c => c?.destroy());

    const C = window.Chart;
    const rev = [...data].reverse(); // oldest → newest
    const latest = data[0];

    // Hour labels for last 24 (formatted HH:00)
    const last24 = rev.slice(-24);
    const labels24 = last24.map(d => {
      const h = new Date(d.time).getHours();
      return `${String(h).padStart(2, '0')}:00`;
    });

    // --- 1. AQI Trend ---
    charts.current.trend = new C(refs.trend.current.getContext('2d'), {
      type: 'line',
      data: {
        labels: labels24,
        datasets: [{
          data: last24.map(d => d.aqi),
          borderColor: '#0ea5e9',
          backgroundColor: createGradient(refs.trend.current, '#0ea5e9'),
          borderWidth: 2, fill: true, tension: 0.35, pointRadius: 2,
        }],
      },
      options: {
        ...CHART_DEFAULTS,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 11 }, maxTicksLimit: 8 } },
          y: { grid: { color: '#f1f5f9' }, ticks: { color: '#94a3b8', font: { size: 11 } } },
        },
      },
    });

    // --- 2. Pollutant Polar Area ---
    charts.current.radar = new C(refs.radar.current.getContext('2d'), {
      type: 'polarArea',
      data: {
        labels: ['PM2.5', 'PM10', 'NO2', 'SO2', 'O3', 'CO×10'],
        datasets: [{
          data: [
            latest.pm2_5 ?? 0, latest.pm10 ?? 0,
            latest.no2  ?? 0, latest.so2  ?? 0,
            latest.o3   ?? 0, (latest.co ?? 0) * 10,
          ],
          backgroundColor: [
            'rgba(239,68,68,0.7)', 'rgba(249,115,22,0.7)',
            'rgba(168,85,247,0.7)', 'rgba(234,179,8,0.7)',
            'rgba(34,197,94,0.7)', 'rgba(14,165,233,0.7)',
          ],
          borderWidth: 0,
        }],
      },
      options: {
        ...CHART_DEFAULTS,
        plugins: { legend: { display: true, position: 'right', labels: { font: { size: 11 }, boxWidth: 12 } } },
      },
    });

    // --- 3. Temp vs Humidity (dual y-axis) ---
    const last48 = rev.slice(-48);
    const labels48 = last48.map(d => {
      const h = new Date(d.time).getHours();
      return `${String(h).padStart(2, '0')}:00`;
    });
    charts.current.weather = new C(refs.weather.current.getContext('2d'), {
      type: 'line',
      data: {
        labels: labels48,
        datasets: [
          {
            label: 'Temp (°C)',
            data: last48.map(d => d.temperature),
            borderColor: '#f97316',
            borderWidth: 2, tension: 0.4, pointRadius: 0,
            yAxisID: 'y',
          },
          {
            label: 'Humidity (%)',
            data: last48.map(d => d.humidity),
            borderColor: '#0ea5e9',
            borderWidth: 2, tension: 0.4, pointRadius: 0,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        ...CHART_DEFAULTS,
        plugins: { legend: { display: true, position: 'top', labels: { font: { size: 11 }, boxWidth: 12 } } },
        scales: {
          x:  { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 }, maxTicksLimit: 8 } },
          y:  { grid: { color: '#f1f5f9' }, ticks: { color: '#f97316', font: { size: 11 } }, position: 'left' },
          y1: { ticks: { color: '#0ea5e9', font: { size: 11 } }, position: 'right', grid: { drawOnChartArea: false } },
        },
      },
    });

    // --- 4. AQI Category Doughnut ---
    const cats = { Good: 0, Moderate: 0, Poor: 0, Severe: 0 };
    data.forEach(d => {
      if (d.aqi <= 50) cats.Good++;
      else if (d.aqi <= 100) cats.Moderate++;
      else if (d.aqi <= 200) cats.Poor++;
      else cats.Severe++;
    });
    charts.current.donut = new C(refs.donut.current.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: Object.keys(cats),
        datasets: [{
          data: Object.values(cats),
          backgroundColor: ['#22c55e', '#f59e0b', '#ef4444', '#a855f7'],
          borderWidth: 0,
          hoverOffset: 6,
        }],
      },
      options: {
        ...CHART_DEFAULTS,
        cutout: '68%',
        plugins: { legend: { display: true, position: 'right', labels: { font: { size: 11 }, boxWidth: 12 } } },
      },
    });

    // --- 5. Stacked trace gases (NO2, SO2, O3) ---
    charts.current.stack = new C(refs.stack.current.getContext('2d'), {
      type: 'bar',
      data: {
        labels: labels24,
        datasets: [
          { label: 'NO2', data: last24.map(d => d.no2 ?? 0), backgroundColor: 'rgba(99,102,241,0.8)', stack: 'a', borderRadius: 3 },
          { label: 'SO2', data: last24.map(d => d.so2 ?? 0), backgroundColor: 'rgba(168,85,247,0.8)', stack: 'a', borderRadius: 3 },
          { label: 'O3',  data: last24.map(d => d.o3  ?? 0), backgroundColor: 'rgba(20,184,166,0.8)', stack: 'a', borderRadius: 3 },
        ],
      },
      options: {
        ...CHART_DEFAULTS,
        plugins: { legend: { display: true, position: 'top', labels: { font: { size: 11 }, boxWidth: 12 } } },
        scales: {
          x: { stacked: true, grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 }, maxTicksLimit: 8 } },
          y: { stacked: true, grid: { color: '#f1f5f9' }, ticks: { color: '#94a3b8', font: { size: 11 } } },
        },
      },
    });

    // --- 6. Diurnal average by hour ---
    const byHour = {};
    data.forEach(d => {
      const hr = new Date(d.time).getHours();
      if (!byHour[hr]) byHour[hr] = [];
      byHour[hr].push(d.aqi);
    });
    const hourKeys = Array.from({ length: 24 }, (_, i) => i);
    const diurnalAvg = hourKeys.map(h => {
      const arr = byHour[h] ?? [];
      return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null;
    });
    charts.current.diurnal = new C(refs.diurnal.current.getContext('2d'), {
      type: 'bar',
      data: {
        labels: hourKeys.map(h => `${String(h).padStart(2, '0')}:00`),
        datasets: [{
          label: 'Avg AQI',
          data: diurnalAvg,
          backgroundColor: hourKeys.map(h => {
            const avg = diurnalAvg[h] ?? 0;
            if (avg <= 50)  return 'rgba(34,197,94,0.75)';
            if (avg <= 100) return 'rgba(245,158,11,0.75)';
            if (avg <= 200) return 'rgba(239,68,68,0.75)';
            return 'rgba(168,85,247,0.75)';
          }),
          borderRadius: 4,
        }],
      },
      options: {
        ...CHART_DEFAULTS,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 }, maxTicksLimit: 12 } },
          y: { grid: { color: '#f1f5f9' }, ticks: { color: '#94a3b8', font: { size: 11 } } },
        },
      },
    });

    };

    tryInit();
    return () => Object.values(charts.current).forEach(c => c?.destroy());
  }, [data]);

  return (
    <Grid container spacing={2.5}>
      <Grid item xs={12} md={8}>
        <ChartCard title="AQI Trend" sub="Last 24 hours" height={220}>
          <canvas ref={refs.trend} style={{ width: '100%', height: '100%' }} />
        </ChartCard>
      </Grid>
      <Grid item xs={12} md={4}>
        <ChartCard title="Pollutant Profile" sub="Current snapshot" height={220}>
          <canvas ref={refs.radar} style={{ width: '100%', height: '100%' }} />
        </ChartCard>
      </Grid>
      <Grid item xs={12} md={6}>
        <ChartCard title="Climatological Matrix" sub="Temperature & humidity over 48h" height={220}>
          <canvas ref={refs.weather} style={{ width: '100%', height: '100%' }} />
        </ChartCard>
      </Grid>
      <Grid item xs={12} md={6}>
        <ChartCard title="AQI Distribution" sub="Category breakdown (72h)" height={220}>
          <canvas ref={refs.donut} style={{ width: '100%', height: '100%' }} />
        </ChartCard>
      </Grid>
      <Grid item xs={12} md={6}>
        <ChartCard title="Trace Gas Stack" sub="NO₂, SO₂, O₃ — last 24h" height={220}>
          <canvas ref={refs.stack} style={{ width: '100%', height: '100%' }} />
        </ChartCard>
      </Grid>
      <Grid item xs={12} md={6}>
        <ChartCard title="Diurnal Pattern" sub="Average AQI by hour of day" height={220}>
          <canvas ref={refs.diurnal} style={{ width: '100%', height: '100%' }} />
        </ChartCard>
      </Grid>
    </Grid>
  );
}

// Helper: vertical gradient for area charts
function createGradient(canvas, color) {
  const ctx = canvas?.getContext('2d');
  if (!ctx) return `${color}20`;
  const grad = ctx.createLinearGradient(0, 0, 0, 250);
  grad.addColorStop(0,   `${color}35`);
  grad.addColorStop(1,   `${color}02`);
  return grad;
}
