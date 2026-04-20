// Central API base URL — reads from Vite env var.
// Set VITE_API_URL in Vercel's dashboard for production.
// In local dev it reads from frontend/.env.local  →  http://localhost:8000
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  history:    () => fetch(`${API_BASE}/api/history`),
  predictAll: () => fetch(`${API_BASE}/api/predict_all`),
  predict:    (locationId) => fetch(`${API_BASE}/api/predict/${locationId}`),
};
