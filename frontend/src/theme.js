import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#0ea5e9', light: '#38bdf8', dark: '#0284c7' },
    secondary: { main: '#6366f1', light: '#818cf8', dark: '#4f46e5' },
    background: { default: '#f0f2f5', paper: '#ffffff' },
    text: { primary: '#0f172a', secondary: '#64748b' },
  },
  typography: {
    fontFamily: '"Inter", "Helvetica", "Arial", sans-serif',
    h4: { fontWeight: 800 },
    h5: { fontWeight: 700 },
    h6: { fontWeight: 600 },
    subtitle1: { fontWeight: 500 },
    body2: { fontWeight: 400, color: '#64748b' },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 1px 3px rgba(0,0,0,0.05), 0 4px 16px rgba(0,0,0,0.04)',
          border: '1px solid rgba(0,0,0,0.06)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 1px 3px rgba(0,0,0,0.05), 0 4px 16px rgba(0,0,0,0.04)',
          border: '1px solid rgba(0,0,0,0.06)',
        },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: {
          border: 'none',
          borderRadius: '10px !important',
          fontWeight: 600,
          fontSize: '0.85rem',
          padding: '8px 20px',
          textTransform: 'none',
          color: '#64748b',
          '&.Mui-selected': {
            backgroundColor: '#0ea5e9',
            color: '#fff',
            '&:hover': { backgroundColor: '#0284c7' },
          },
        },
      },
    },
    MuiToggleButtonGroup: {
      styleOverrides: {
        root: {
          backgroundColor: '#e2e8f0',
          borderRadius: 12,
          padding: 4,
          gap: 4,
        },
      },
    },
  },
});

export default theme;
