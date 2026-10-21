const fs=require('node:fs'),path=require('node:path');
const file=path.join(__dirname,'fidelity.js');
let source=fs.readFileSync(file,'utf8');
source=source.replace("medal(i+1)","uniqueMedal(i+1,'circle','desktop')").replace("medal(i+1,i===0||i===1?'shield':'circle')","uniqueMedal(i+1,i===0||i===1?'shield':'circle','tablet')");
source=source.replace('+cactus()+',"+uniqueCactus('one')+").replace('+cactus()+',"+uniqueCactus('two')+");
fs.writeFileSync(file,source);
