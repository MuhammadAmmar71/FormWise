import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // The form schema is imported from ../backend so both sides share one source of truth.
  server: { fs: { allow: ['..'] } },
})
