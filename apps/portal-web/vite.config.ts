import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { existsSync, statSync } from 'node:fs'
import { resolve, sep } from 'node:path'
import { resolveAppConfig } from './src/config/environment.ts'

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  const production = command === 'build';
  const config = resolveAppConfig(env, production);
  const studentWebRoot = resolve(process.cwd(), 'public/study');

  return {
    plugins: [react(), {
      name: 'local-student-web-routes',
      configureServer(server) {
        server.middlewares.use((request, _response, next) => {
          const pathname = new URL(request.url || '/', 'http://localhost').pathname;
          if (pathname === '/study' || pathname.startsWith('/study/')) {
            let requestedFile = studentWebRoot;
            try {
              const relativePath = decodeURIComponent(pathname.slice('/study'.length)).replace(/^\/+/, '');
              requestedFile = resolve(studentWebRoot, relativePath);
            } catch {
              request.url = '/study/index.html';
              next();
              return;
            }
            if ((requestedFile !== studentWebRoot && !requestedFile.startsWith(`${studentWebRoot}${sep}`)) ||
                !existsSync(requestedFile) || statSync(requestedFile).isDirectory()) {
              request.url = '/study/index.html';
            }
          }
          next();
        });
      },
    }],
    resolve: { dedupe: ['react', 'react-dom'] },
    define: {
      __APP_CONFIG__: JSON.stringify(config),
      'import.meta.env.VITE_SHOW_DEV_TOOLS': JSON.stringify(!production && env.VITE_SHOW_DEV_TOOLS === 'true' ? 'true' : 'false'),
      'import.meta.env.VITE_USE_MOCK': JSON.stringify(!production && env.VITE_USE_MOCK === 'true' ? 'true' : 'false'),
    },
    server: {
      port: 5172,
      strictPort: true,
      host: true,
    },
  };
})
