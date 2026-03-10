import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

const devProxyTarget = 'http://localhost:8080'

export default defineConfig({
  plugins: [uni()],
  css: {
    preprocessorOptions: {
      scss: {
        silenceDeprecations: ['legacy-js-api', 'import'],
      },
    },
  },
  server: {
    open: false,
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: devProxyTarget,
        changeOrigin: true,
      },
      '/uploads': {
        target: devProxyTarget,
        changeOrigin: true,
      },
    },
  },
})
