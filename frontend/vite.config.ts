import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      'clsx': path.resolve(__dirname, './node_modules/clsx'),
      'tailwind-merge': path.resolve(__dirname, './node_modules/tailwind-merge'),
      'lucide-react': path.resolve(__dirname, './node_modules/lucide-react'),
      'framer-motion': path.resolve(__dirname, './node_modules/framer-motion'),
      'echarts': path.resolve(__dirname, './node_modules/echarts'),
      'echarts-for-react': path.resolve(__dirname, './node_modules/echarts-for-react'),
      'recharts': path.resolve(__dirname, './node_modules/recharts'),
      'reactflow': path.resolve(__dirname, './node_modules/reactflow'),
      'react-markdown': path.resolve(__dirname, './node_modules/react-markdown'),
      'react-syntax-highlighter': path.resolve(__dirname, './node_modules/react-syntax-highlighter'),
    }
  },
  server: {
    port: 5180,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
        ws: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
        },
      }

    }
  }

})
