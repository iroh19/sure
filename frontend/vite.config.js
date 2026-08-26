import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// BASE_PATH is set by the Pages workflow ("/sure/"). Locally it stays "/" so the
// dev server and the Docker/nginx build are unaffected.
const base = process.env.BASE_PATH || '/'

export default defineConfig({
  base,
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
