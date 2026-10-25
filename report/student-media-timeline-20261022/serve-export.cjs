const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../../runtime/student-media-timeline-20261022/web');
const types={'.html':'text/html; charset=utf-8','.js':'application/javascript','.css':'text/css','.png':'image/png','.webp':'image/webp','.ttf':'font/ttf','.woff2':'font/woff2','.mp4':'video/mp4','.wav':'audio/wav'};
http.createServer((req,res)=>{const relative=decodeURIComponent(new URL(req.url,'http://127.0.0.1:8094').pathname).replace(/^\/study\/?/,'').replace(/^\/+/,''),file=path.resolve(root,relative);
 if(!file.startsWith(root+path.sep)&&file!==root){res.writeHead(403).end();return;}
 const candidate=[file,file+'.html',path.join(file,'index.html')].find(p=>fs.existsSync(p)&&fs.statSync(p).isFile());if(!candidate){res.writeHead(404).end();return;}
 res.writeHead(200,{'content-type':types[path.extname(candidate)]||'application/octet-stream'});fs.createReadStream(candidate).pipe(res);
}).listen(8094,'127.0.0.1',()=>console.log('Timeline review ready.'));
