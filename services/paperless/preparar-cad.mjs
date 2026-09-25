import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
process.chdir(path.dirname(fileURLToPath(import.meta.url)));
const plan=JSON.parse(await fs.readFile('/run/media/martin/Ediloco/Archivo-TheMartin/09_Documentos/00_Indice_documentos/plan-de-copia.json'));
const output=path.resolve('state/derivados');await fs.mkdir(output,{recursive:true,mode:0o700});
const cadBinary=await fs.access('tools/libredwg/bin/dwggrep').then(()=>'tools/libredwg/bin/dwggrep',()=> 'ediloco-dwggrep');
let state=JSON.parse(await fs.readFile('state/preparados-cad.json','utf8').catch(e=>{if(e.code==='ENOENT')return '{}';throw e;}));
const save=async()=>{await fs.writeFile('state/preparados-cad.tmp',JSON.stringify(state,null,2),{mode:0o600});await fs.rename('state/preparados-cad.tmp','state/preparados-cad.json');};
const extract=file=>new Promise((resolve,reject)=>{
 const child=spawn(cadBinary,['-h','-t','-b','.',file]);
 let text='',error='',bytes=0;
 const timer=setTimeout(()=>{child.kill('SIGKILL');},120000);
 child.stdout.on('data',b=>{bytes+=b.length;if(bytes>32e6)child.kill('SIGKILL');else text+=b.toString('utf8');});
 child.stderr.on('data',b=>{if(error.length<5000)error+=b.toString('utf8');});
 child.on('error',e=>{clearTimeout(timer);reject(e);});
 child.on('close',(code,signal)=>{clearTimeout(timer);resolve({text,error,code,signal});});
});
let done=0;
for(const entry of plan.entries.filter(e=>/\.dwg$/i.test(e.target))){
 if(state[entry.sha256])continue;
 const source=path.join(plan.destination,entry.target);
 const original=await fs.readFile(source);
 if(crypto.createHash('sha256').update(original).digest('hex')!==entry.sha256)throw Error(`Fuente cambiada: ${entry.target}`);
 const result=await extract(source);
 const lines=[...new Set(result.text.split('\n').map(s=>s.replace(/^\s*\S+\s+\d+:\s*/, '').trim()).filter(Boolean))];
 const text=lines.join('\n');
 const status=result.signal?'error':text?'texto_extraido':'solo_metadatos';
 const payload=path.join(output,entry.sha256+'.txt');
 const content=`Plano CAD: ${path.basename(entry.target)}\nCategoría: ${entry.target.split('/')[0].replaceAll('_',' ')}\nUbicación original: ${entry.target}\n\n${text?'Textos y anotaciones extraídos del plano:\n'+text:'No se recuperaron textos o anotaciones. Esta ficha permite localizar el plano por nombre y carpeta; no describe su geometría.'}\n`;
 await fs.writeFile(payload,content,{mode:0o600});
 state[entry.sha256]={payload,uploadName:path.basename(entry.target)+'.txt',payloadSha256:crypto.createHash('sha256').update(content).digest('hex'),strategy:'cad',status,extractedCharacters:text.length,toolExit:result.code,warning:result.error||undefined};
 if(++done%20===0){await save();console.log(JSON.stringify({preparados:Object.keys(state).length,total:1438}));}
}
await save();const statuses={};for(const r of Object.values(state))statuses[r.status]=(statuses[r.status]??0)+1;console.log(JSON.stringify({total:Object.keys(state).length,estados:statuses}));
