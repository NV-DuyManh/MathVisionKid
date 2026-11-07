import { execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { dirname, extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

// Real Expo export, with no developer .env, backend, secrets or external model calls.
const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const output = resolve(root, '.local-artifacts/student-browser/export');
execFileSync(process.execPath, [resolve(root, 'node_modules/expo/bin/cli'), 'export', '--platform', 'web',
  '--max-workers', '2', '--output-dir', output], {
  cwd: resolve(root, 'apps/student-mobile'), timeout: 150000, maxBuffer: 10 * 1024 * 1024,
  env: { ...process.env, EXPO_NO_DOTENV: '1', EXPO_NO_TELEMETRY: '1',
    MATHVISION_WEB_EXPORT: 'true', MATHVISION_WEB_PREVIEW: 'true',
    EXPO_PUBLIC_API_BASE_URL: '/api/v1', EXPO_PUBLIC_USE_MOCK: 'false',
    EXPO_PUBLIC_TEACHER_URL: 'https://teacher.mathvision.test', EXPO_PUBLIC_ADMIN_URL: 'https://admin.mathvision.test' },
});
const types = { '.html': 'text/html', '.js': 'application/javascript', '.json': 'application/json', '.css': 'text/css',
  '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
  '.ttf': 'font/ttf', '.woff': 'font/woff', '.woff2': 'font/woff2' };
createServer(async (request, response) => {
  try {
    const url = new URL(request.url, 'http://127.0.0.1');
    if (!url.pathname.startsWith('/study/')) { response.writeHead(404).end(); return; }
    let file = resolve(output, decodeURIComponent(url.pathname.slice('/study/'.length)));
    if (file !== output && !file.startsWith(output + sep)) { response.writeHead(403).end(); return; }
    if (!(await stat(file).catch(() => null))?.isFile()) {
      if (extname(file)) { response.writeHead(404).end(); return; }
      file = resolve(output, 'index.html');
    }
    response.writeHead(200, { 'Content-Type': types[extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    response.end(await readFile(file));
  } catch { response.writeHead(500).end(); }
}).listen(43173, '127.0.0.1', () => process.stdout.write('Real Student export ready\n'));
