import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // 增加请求头大小限制
            proxyReq.setHeader('connection', 'keep-alive');
          });
          proxy.on('error', (err, _req, res) => {
            console.log('proxy error', err);
            res.end();
          });
        }
      }
    }
  }
}) 