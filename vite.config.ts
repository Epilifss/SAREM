import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    server: {
      allowedHosts: ["api.tidelli.com.br"],
      proxy: {
        '/api/protheus/bos': {
          target: 'http://api.tidelli.com.br',
          changeOrigin: true,
          rewrite: () => '/pedidos/bos',
          headers: {
            'X-API-Key': env.PROTHEUS_API_KEY,
          },
        },
      },
    },
  }
})
