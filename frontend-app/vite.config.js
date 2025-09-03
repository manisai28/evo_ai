import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // ✅ ADD THIS SERVER CONFIGURATION BLOCK
  server: {
    preview: {
      host: '0.0.0.0',
      port: 4173,
      allowedHosts: ['personal-ai-frontend.onrender.com'] // ✅ Add your live frontend URL here
    }
  }
})