import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/analysis': 'http://localhost:8000',
      '/reports': 'http://localhost:8000',
      '/repository': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    }
  }
})
