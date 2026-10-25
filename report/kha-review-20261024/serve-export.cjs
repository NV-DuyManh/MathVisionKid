const http = require('node:http'), fs = require('node:fs'), path = require('node:path');
const root = path.resolve(__dirname, 'student-export');
const types = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png', '.webp': 'image/webp', '.ttf': 'font/ttf', '.wav': 'audio/wav', '.mp4': 'video/mp4' };
http.createServer((req, res) => {
  const file = path.resolve(root, decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname).replace(/^\/study\/?/, '').replace(/^\/+/, ''));
  if (file !== root && !file.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
  const candidate = [file, file + '.html', path.join(file, 'index.html')].find(p => fs.existsSync(p) && fs.statSync(p).isFile());
  if (!candidate) { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'content-type': types[path.extname(candidate)] || 'application/octet-stream' }); fs.createReadStream(candidate).pipe(res);
}).listen(4178, '127.0.0.1', () => console.log('Review export ready.'));
