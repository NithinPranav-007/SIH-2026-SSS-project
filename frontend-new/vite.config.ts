import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 5173,
    host: '127.0.0.1',
    // Proxy /api/* to the FastAPI backend during development
    // This avoids CORS issues and matches the production nginx setup
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path,
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-map': ['maplibre-gl'],
          'vendor-icons': ['lucide-react'],
          'vendor-http': ['axios'],
        }
      }
    },
    chunkSizeWarningLimit: 900,
  }
})
