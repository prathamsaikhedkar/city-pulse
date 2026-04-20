import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Makes the API base URL available as import.meta.env.VITE_API_URL
  // Set VITE_API_URL in Vercel's environment variables for production.
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
})
