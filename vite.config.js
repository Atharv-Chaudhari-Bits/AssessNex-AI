import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({mode}) => {
  const isProd = mode === 'production' || process.env.NODE_ENV === 'production'
  return {
    base: isProd ? '/AssessNex-AI/' : '/',
    plugins: [react()],
    server: {
      port: 5173
    }
  }
})
