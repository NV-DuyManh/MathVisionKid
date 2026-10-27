const http = require('node:http'), fs = require('node:fs'), path = require('node:path');
const root = path.resolve(__dirname, '../../runtime/student-voice-replay-20261022/web');
const types = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.ttf': 'font/ttf', '.woff2': 'font/woff2' };
http.createServer((req, res) => {
  const relative = decodeURIComponent(new URL(req.url, 'http://127.0.0.1:8093').pathname).replace(/^\/study\/?/, '').replace(/^\/+/, '');
  const file = path.resolve(root, relative);
  if (!file.startsWith(root + path.sep) && file !== root) { res.writeHead(403).end(); return; }
  const candidate = [file, file + '.html', path.join(file, 'index.html')].find(f => fs.existsSync(f) && fs.statSync(f).isFile());
  if (!candidate) { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'content-type': types[path.extname(candidate)] || 'application/octet-stream' });
  fs.createReadStream(candidate).pipe(res);
}).listen(8093, '127.0.0.1', () => console.log('Student voice replay review ready.'));
