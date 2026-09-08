import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    // Ensure only one copy of React is used (prevents "Invalid hook call" errors)
    dedupe: ['react', 'react-dom'],
  },
})
