import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  envDir: resolve(__dirname, '.'),
  plugins: [react()],
  resolve: {
    alias: {
      "@": "/src",
    },
  },
})
