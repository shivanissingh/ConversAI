import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Alias @talkinghead → src/vendor/talkinghead so Vite finds it correctly
      '@talkinghead': path.resolve(__dirname, 'src/vendor/talkinghead'),
    },
  },
  optimizeDeps: {
    // Exclude TalkingHead from bundling — it uses runtime dynamic imports for
    // lipsync-en.mjs, dynamicbones.mjs etc. that must remain as separate files
    exclude: ['@met4citizen/talkinghead'],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'framer': ['framer-motion'],
          'lucide': ['lucide-react'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
})
