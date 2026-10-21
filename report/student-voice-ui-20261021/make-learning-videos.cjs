const fs = require('node:fs'), path = require('node:path'), { spawn } = require('node:child_process');
const { chromium } = require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out = path.resolve(__dirname, '../../apps/student-mobile/assets/videos');
fs.mkdirSync(out, { recursive: true });
const clipIds = ['fraction-intro', 'common-parts', 'problem-summary'];
(async () => {
 const browser = await chromium.launch({ headless: true });
 try {
  const page = await browser.newPage({ viewport: { width: 960, height: 540 }, deviceScaleFactor: 1 });
  await page.goto('file:///E:/MathVisionKid/report/student-ui-integration-20261021/index.html');
  await page.setContent(`<style>@font-face{font-family:Nunito;src:url('file:///E:/MathVisionKid/apps/student-mobile/assets/fonts/Nunito-ExtraBold.ttf')}body{margin:0}canvas{display:block}</style><canvas width="960" height="540"></canvas>`);
  await page.evaluate(async () => { await document.fonts.load('800 32px Nunito'); });
  const mascot = 'data:image/png;base64,' + fs.readFileSync('E:/MathVisionKid/apps/student-mobile/assets/illustrations/mathvision-star.png').toString('base64');
  await page.evaluate(async src => { window.star = new Image(); window.star.src = src; await window.star.decode(); }, mascot);
  await page.evaluate(() => {
   const ctx = document.querySelector('canvas').getContext('2d');
   window.drawClip = (id, t) => {
    const purple = '#7042DD', ink = '#261B53', muted = '#796C91', gold = '#F2B943';
    const box = (x,y,w,h,r,fill,stroke) => { ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fillStyle=fill;ctx.fill();if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=2;ctx.stroke();} };
    const text = (s,x,y,size=26,color=ink,align='left') => {ctx.font=`800 ${size}px Nunito`;ctx.fillStyle=color;ctx.textAlign=align;ctx.fillText(s,x,y);};
    const line = (x1,y1,x2,y2) => {ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();};
    const fraction = (n,d,x,y,size=44) => {text(String(n),x,y-12,size,purple,'center');ctx.strokeStyle=purple;ctx.lineWidth=3;line(x-23,y,x+23,y);text(String(d),x,y+47,size,purple,'center');};
    ctx.clearRect(0,0,960,540);const bg=ctx.createLinearGradient(0,0,960,540);bg.addColorStop(0,'#FAF8FF');bg.addColorStop(1,'#EEE7FD');ctx.fillStyle=bg;ctx.fillRect(0,0,960,540);
    box(32,28,896,484,28,'#FFFFFF');text('MATHVISIONKID',64,65,16,purple);text('VÍ DỤ MINH HỌA',895,65,13,muted,'right');ctx.drawImage(window.star,id==='common-parts'?814:752,id==='common-parts'?140:308+Math.sin(t*2)*3,id==='common-parts'?90:150,id==='common-parts'?90:150);
    let caption='';
    if(id==='fraction-intro'){
     text('Một phần ba nghĩa là gì?',64,117,32);const cx=277,cy=291,r=132,progress=Math.min(1,Math.max(0,(t-4)/1.2));
     for(let p=0;p<3;p++){const a=p*Math.PI*2/3-Math.PI/2,b=a+Math.PI*2/3;ctx.beginPath();ctx.moveTo(cx,cy);ctx.arc(cx,cy,r,a,b);ctx.closePath();ctx.fillStyle=p===0?`rgba(112,66,221,${.06+progress*.94})`:'#F1EBFC';ctx.fill();ctx.lineWidth=4;ctx.strokeStyle='white';ctx.stroke();}
     ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.strokeStyle='#B89CDF';ctx.lineWidth=2;ctx.stroke();
     if(t<4){text('Chia đều một hình',482,236,29);text('thành 3 phần bằng nhau.',482,278,26,muted);caption='Các phần có diện tích bằng nhau.';}
     else if(t<8){text('Chọn 1 phần.',482,236,31);text('Cả hình vẫn có 3 phần.',482,280,25,muted);caption='Tô một phần trong ba phần bằng nhau.';}
     else{fraction(1,3,500,260);text('1 phần được chọn',555,244,25);text('3 phần bằng nhau',555,303,25,muted);caption='Tử số đếm phần đã chọn. Mẫu số đếm phần của cả hình.';}
    }else if(id==='common-parts'){
     text('Vì sao cần phần cùng kích thước?',64,117,31);
     const subdivisions=t<4?[2,3]:[6,6];
     [[2,3,205],[3,2,330]].forEach(([d,n,y],i)=>{const units=subdivisions[i], selected=t<4?1:n;box(120,y,490,76,12,'#F1EBFC');for(let j=0;j<units;j++){box(120+j*490/units,y,490/units,76,2,j<selected?(i?'#E6B44F':purple):'#F0EBFA','white');}text(t<4?`1 phần ${d}`:`${n} phần 6`,651,y+48,27,i?'#AD7622':purple);});
     caption=t<4?'Nhìn hai hình bằng nhau: phần được chia đang khác kích thước.':t<8?'Chia nhỏ hơn để mỗi miếng có cùng kích thước.':'Chia lại không làm đổi lượng đã tô. Ta chỉ đổi cách đếm phần.';
     if(t>=8){text('Lượng đã tô vẫn giữ nguyên',120,174,20,muted);}
    }else{
     text('Tóm tắt đề, chưa cần tính',64,117,32);
     const sentences=['Lan có 12 chiếc bút.','Lan cho bạn 3 chiếc bút.','Hỏi Lan còn lại bao nhiêu chiếc bút?'];
     box(60,148,525,178,21,'#F7F3FD');sentences.forEach((s,i)=>{if(t>=i*2){text(s,83,191+i*47,24,i===2?purple:ink);}});
     if(t>=6){box(62,349,300,99,20,'#EEE6FB');text('ĐÃ BIẾT',81,377,14,purple);text('Có 12 bút · Cho 3 bút',81,418,24);}
     if(t>=9){box(380,349,300,99,20,'#E8F5EB');text('CẦN TÌM',399,377,14,'#4C8764');text('Số bút còn lại',399,418,24);}
     caption=t<6?'Đọc chậm từng câu, tìm số và điều đề đang hỏi.':t<9?'Ghi điều đề cho biết vào phần Đã biết.':'Ghi câu hỏi vào phần Cần tìm. Giờ em mới chọn cách làm.';
    }
    box(53,470,854,30,13,'#F4EFFB');text(caption,480,492,17,muted,'center');box(64,519,832,4,2,'#DDD2EE');box(64,519,832*Math.min(1,t/12),4,2,gold);
   };
  });
  for (const id of clipIds) {
   const encoder = spawn('ffmpeg', ['-hide_banner','-loglevel','error','-y','-f','image2pipe','-vcodec','png','-framerate','20','-i','pipe:0','-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',path.join(out,id+'.mp4')], { windowsHide: true, stdio: ['pipe','ignore','pipe'] });
   let error='';encoder.stderr.on('data', data=>error+=data);
   const finished=new Promise((resolve,reject)=>{encoder.on('error',reject);encoder.on('close',code=>code===0?resolve():reject(new Error(error)));});
   for(let frame=0;frame<240;frame++) { await page.evaluate(({id,t})=>window.drawClip(id,t),{id,t:frame/20});const png=await page.screenshot({type:'png'});if(!encoder.stdin.write(png))await new Promise(resolve=>encoder.stdin.once('drain',resolve)); }
   encoder.stdin.end();await finished;
   await page.evaluate(({id})=>window.drawClip(id,9.5),{id});await page.screenshot({path:path.join(out,id+'.png')});
   console.log(id+': 12 s, 960×540, captions, no audio.');
  }
 } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
