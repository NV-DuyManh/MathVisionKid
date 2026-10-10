import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { resolveAppConfig } from './src/config/environment.ts'

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  const production = command === 'build';
  const config = resolveAppConfig(env, production);

  return {
    plugins: [react()],
    resolve: { dedupe: ['react', 'react-dom'] },
    define: {
      __APP_CONFIG__: JSON.stringify(config),
      'import.meta.env.VITE_SHOW_DEV_TOOLS': JSON.stringify(!production && env.VITE_SHOW_DEV_TOOLS === 'true' ? 'true' : 'false'),
      'import.meta.env.VITE_USE_MOCK': JSON.stringify(!production && env.VITE_USE_MOCK !== 'false' ? 'true' : 'false'),
    },
    server: {
      port: 5174,
      strictPort: true,
      host: true,
    },
  };
})
