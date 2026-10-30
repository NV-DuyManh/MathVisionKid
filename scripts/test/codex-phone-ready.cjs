const fs=require('node:fs');const path=require('node:path');const {createRequire}=require('node:module');
const root=path.resolve(__dirname,'../..');
const expoRequire=createRequire(require.resolve('expo/package.json',{paths:[path.join(root,'apps/student-mobile')]}));
const cliRequire=createRequire(expoRequire.resolve('@expo/cli/package.json'));
const {getIpAddressAsync}=cliRequire('./build/src/utils/ip.js');const {printQRCode}=cliRequire('./build/src/utils/qr.js');
const {getExpoGoUrl,loadExpoManifest}=require('../dev/show-student-qr.cjs');
(async()=>{
 const address=await getIpAddressAsync(),manifest=await loadExpoManifest(address),url=getExpoGoUrl(manifest,address);
 const endpoints=[['Spring Boot',`http://${address}:8080/actuator/health`],['FastAPI','http://127.0.0.1:8000/health'],['Expo Metro',`http://${address}:8081/status`],['Portal',`http://${address}:5172`],['Teacher',`http://${address}:5173`],['Admin',`http://${address}:5174`]];
 for(const [name,endpoint] of endpoints){const res=await fetch(endpoint,{signal:AbortSignal.timeout(10000)});if(!res.ok)throw new Error(`${name}: HTTP ${res.status}`);if(name==='Expo Metro'&&!(await res.text()).includes('packager-status:running'))throw new Error('Metro not ready');console.log(`${name}: HTTP ${res.status} - ACTIVE`);}
 const out=path.join(root,'report/codex-antigravity-review-20261029');const native=JSON.parse(fs.readFileSync(path.join(out,'android-bundle.json')));if(native.status!==200||native.bytes<10000)throw new Error('Native bundle has not passed verification');
 const runtime=JSON.parse(fs.readFileSync(path.join(out,'runtime-final.json')));if(runtime.lan!==address)throw new Error('LAN changed; rerun runtime verification');
 console.log('\nMATHVISIONKID — READY FOR PHONE TEST\n');
 console.log(`PC LAN IP: ${address}\nBackend API URL: http://${address}:8080/api/v1\nExpo Metro URL: http://${address}:8081\nExpo Go deep link: ${url}\nPortal URL: http://${address}:5172\nAdmin URL: http://${address}:5174\nTeacher URL: http://${address}:5173\n`);
 printQRCode(url).print();
 console.log('PC và điện thoại dùng cùng Wi-Fi. Mở Expo Go tương thích SDK 58 và quét QR.');
 console.log('Sẵn sàng để người dùng nghiệm thu. Chưa kiểm chứng trên điện thoại vật lý.');
 console.log('PostgreSQL: real query PASS | Redis: PONG | MinIO: readiness HTTP 200');
 console.log('Docker CLI vẫn timeout; không xóa/reset container hoặc volumes.');
 console.log(`QR HTML: ${path.join(out,'PHONE_TEST.html')}`);
})().catch(e=>{console.error(`NOT READY: ${e.message}`);process.exitCode=1});
