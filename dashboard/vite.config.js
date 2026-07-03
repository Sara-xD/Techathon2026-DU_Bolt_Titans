import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The dashboard talks to the FastAPI backend on :8000 (REST + WebSocket).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
})
