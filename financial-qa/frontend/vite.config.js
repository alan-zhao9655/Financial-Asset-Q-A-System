import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://localhost:8000' } },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          three:  ['three', '@react-three/fiber', '@react-three/drei'],
          charts: ['lightweight-charts'],
        },
      },
    },
  },
})
