import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { existsSync, statSync, readdirSync, readFileSync, writeFileSync, createReadStream } from 'node:fs'
import { resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createRequire } from 'node:module'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import { createHash } from 'node:crypto'
import { resolveAppConfig } from './src/config/environment.ts'

const portalRoot = fileURLToPath(new URL('.', import.meta.url));
const { lookup: contentType } = createRequire(import.meta.url)('mime-types');
function inputVersion(path: string): string {
  if (!existsSync(path)) return '';
  const stat = statSync(path);
  return stat.isDirectory() ? readdirSync(path).filter(name => !['node_modules', 'dist', 'build', '.git', '.expo'].includes(name))
    .sort().map(name => inputVersion(resolve(path, name))).join('|')
    : `${path}:${stat.size}:${stat.mtimeMs}`;
}

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, portalRoot, 'VITE_');
  const production = command === 'build';
  const config = resolveAppConfig(env, production);
  const studentWebRoot = resolve(portalRoot, '../../infra/local-runtime/student-web-preview');
  const api = new URL(config.apiBaseUrl);

  return {
    plugins: [react(), {
      name: 'local-student-web-routes',
      async configureServer(server) {
        // Use the same Student screens and same-origin session as deployment.
        // This generated preview is refreshed whenever the local portal starts.
        const studentRoot = resolve(portalRoot, '../student-mobile');
        const inputs = ['src', 'assets', 'public', 'app.config.js', 'app.json', 'package.json', 'babel.config.js', 'metro.config.js', 'metroCache.cjs']
          .map(path => inputVersion(resolve(studentRoot, path)));
        inputs.push(inputVersion(fileURLToPath(import.meta.url)), inputVersion(resolve(portalRoot, '../../package-lock.json')), inputVersion(resolve(portalRoot, '../../packages')));
        const signature = createHash('sha256').update(JSON.stringify([inputs, config.teacherOrigin, config.adminOrigin])).digest('hex');
        const stamp = resolve(studentWebRoot, '.source-hash');
        if (!existsSync(resolve(studentWebRoot, 'index.html')) || !existsSync(stamp) || readFileSync(stamp, 'utf8') !== signature) {
          server.config.logger.info('Preparing the shared Student web interface…');
          const started = Date.now();
          await promisify(execFile)(process.execPath, [createRequire(import.meta.url).resolve('expo/bin/cli'),
          'export', '--platform', 'web', '--max-workers', '2', '--output-dir', studentWebRoot], {
          cwd: studentRoot, timeout: 180000, maxBuffer: 4 * 1024 * 1024,
          env: { ...process.env, EXPO_NO_DOTENV: '1', MATHVISION_WEB_EXPORT: 'true', MATHVISION_WEB_PREVIEW: 'true',
            EXPO_PUBLIC_API_BASE_URL: '/api/v1', EXPO_PUBLIC_USE_MOCK: 'false',
            EXPO_PUBLIC_TEACHER_URL: config.teacherOrigin, EXPO_PUBLIC_ADMIN_URL: config.adminOrigin },
          });
          if (!existsSync(resolve(studentWebRoot, 'index.html'))) throw new Error('Student web export is missing its entry page.');
          writeFileSync(stamp, signature);
          server.config.logger.info(`Student web ready in ${((Date.now() - started) / 1000).toFixed(1)}s.`);
        }
        server.middlewares.use((request, response, next) => {
          const pathname = new URL(request.url || '/', 'http://localhost').pathname;
          if (pathname === '/study' || pathname.startsWith('/study/')) {
            response.setHeader('Cache-Control', 'no-store');
            let requestedFile = studentWebRoot;
            try {
              const relativePath = decodeURIComponent(pathname.slice('/study'.length)).replace(/^\/+/, '');
              requestedFile = resolve(studentWebRoot, relativePath);
            } catch {
              response.statusCode = 400;
              response.end();
              return;
            }
            if (requestedFile !== studentWebRoot && !requestedFile.startsWith(`${studentWebRoot}${sep}`)) {
              response.statusCode = 404; response.end(); return;
            }
            if (!existsSync(requestedFile) || statSync(requestedFile).isDirectory()) {
              if (/\.[^/]+$/.test(pathname)) { response.statusCode = 404; response.end(); return; }
              requestedFile = resolve(studentWebRoot, 'index.html');
            }
            // Serve outside Vite's cached public-file list and production publicDir.
            response.setHeader('Content-Type', contentType(requestedFile) || 'application/octet-stream');
            const stream = createReadStream(requestedFile);
            stream.on('error', () => { response.statusCode = 404; response.end(); });
            stream.pipe(response);
            return;
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
      proxy: {
        '/api/v1': { target: api.origin, changeOrigin: true,
          rewrite: path => path.replace(/^\/api\/v1/, api.pathname.replace(/\/$/, '')) },
        '/actuator/health': { target: api.origin, changeOrigin: true },
      },
    },
  };
})
