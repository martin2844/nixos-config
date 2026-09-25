import fs from 'node:fs/promises';
import {createWriteStream} from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawn,execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {saveJSON} from './paperless-api.mjs';

const root=path.dirname(fileURLToPath(import.meta.url));process.chdir(root);
const stateFile='state/indexacion-completa.json';
const planFile='/run/media/martin/Ediloco/Archivo-TheMartin/09_Documentos/00_Indice_documentos/plan-de-copia.json';
if(execFileSync('findmnt',['-no','UUID','--target','/run/media/martin/Ediloco'],{encoding:'utf8'}).trim()!=='1c5b930d-5d2f-4b13-9577-661c73bc1993')throw Error('Ediloco no está montado.');
const planHash=crypto.createHash('sha256').update(await fs.readFile(planFile)).digest('hex');
let state=JSON.parse(await fs.readFile(stateFile,'utf8').catch(e=>{if(e.code==='ENOENT')return '{}';throw e;}));
if(state.planHash!==planHash)state={planHash,startedAt:new Date().toISOString(),steps:{}};
if(state.status==='COMPLETED'){console.log('Esta indexación ya finalizó. Ver RESULTADO.md.');process.exit(0);}
let child,stopping=false;
for(const signal of ['SIGTERM','SIGINT'])process.on(signal,()=>{stopping=true;child?.kill('SIGTERM');});
const run=(command,args,log,input)=>new Promise((resolve,reject)=>{
  if(stopping){reject(Error('Pausa solicitada'));return;}
  const stream=createWriteStream(log,{flags:'a',mode:0o600});
  stream.write(`\n--- ${new Date().toISOString()} ---\n`);
  child=spawn(command,args,{cwd:root,stdio:['pipe','pipe','pipe']});
  child.stdout.pipe(stream,{end:false});child.stderr.pipe(stream,{end:false});
  if(input)child.stdin.end(input);else child.stdin.end();
  child.once('error',e=>{stream.end();child=null;reject(e);});
  child.once('close',(code,signal)=>{stream.end();child=null;code===0?resolve():reject(Error(`${command}: salida ${code??signal}; ver ${log}`));});
});
const step=async(name,command,args,log)=>{
  if(state.steps[name]?.completedAt)return;
  state.status='RUNNING';state.phase=name;state.updatedAt=new Date().toISOString();delete state.error;
  await saveJSON(stateFile,state);console.log(`${state.updatedAt}: ${name}`);
  await run(command,args,log);
  state.steps[name]={completedAt:new Date().toISOString()};await saveJSON(stateFile,state);
};
// flock in the user service prevents two controllers. Remove a stale importer
// lock only after verifying that no importer still runs in this project.
for(const pid of (await fs.readdir('/proc')).filter(p=>/^\d+$/.test(p))){
  try{
    if(await fs.readlink(`/proc/${pid}/cwd`)!==root)continue;
    const cmd=(await fs.readFile(`/proc/${pid}/cmdline`,'utf8')).split('\0');
    if(cmd.some(a=>a==='importar.mjs'||a===path.join(root,'importar.mjs')))throw Error(`Ya hay un importador activo: ${pid}`);
  }catch(e){if(!['ENOENT','EACCES','EPERM','EINVAL'].includes(e.code))throw e;}
}
await fs.unlink('state/import.lock').catch(e=>{if(e.code!=='ENOENT')throw e;});
try{
  // Resuming the importer must not interrupt running OCR/index updates merely
  // because the service configuration changed. paperless.service applies it.
  await run('bash',['iniciar.sh','--no-recreate'],'logs/indexacion-servicios.log');
  // A resumed service can outlive a Docker restart, so always check readiness.
  for(let i=0;;i++){
    try{const r=await fetch('http://127.0.0.1:8010/api/');if(r.status<500)break;}catch{}
    if(i>=60||stopping)throw Error('Paperless no está disponible');
    await new Promise(r=>setTimeout(r,5000));
  }
  await step('preparar_planos',process.execPath,['preparar-cad.mjs'],'logs/preparar-cad.log');
  await step('preparar_formatos','docker',['run','--rm','-i','--user','1000:100','--network','documentos-ediloco_default','--mount','type=bind,source=/run/media/martin/Ediloco/Archivo-TheMartin/09_Documentos,target=/source,readonly','--mount',`type=bind,source=${root},target=/work`,'--entrypoint','python3','documentos-ediloco-paperless:3.2.1','/work/preparar-formatos.py'],'logs/preparar-formatos.log');
  await step('configurar_ocr',process.execPath,['configurar-ocr.mjs'],'logs/configurar-ocr.log');
  await step('importacion_y_ocr',process.execPath,['importar.mjs','--todos'],'logs/importar-todos.log');
  await step('revision_pdfs_previos',process.execPath,['revisar-pdfs.mjs'],'logs/revisar-pdfs.log');
  await step('ocr_office',process.execPath,['ocr-office.mjs'],'logs/ocr-office.log');
  await step('clasificacion_documentos',process.execPath,['reclasificar.mjs','--aplicar'],'logs/clasificacion.log');
  await step('indice_texto','docker',['compose','exec','--user','1000:100','-T','webserver','document_index','reindex'],'logs/indice-texto.log');
  await step('indice_semantico','docker',['compose','exec','--user','1000:100','-T','webserver','document_llmindex','update'],'logs/indice-completo.log');
  await step('verificar_integridad',process.execPath,['importar.mjs','--verificar'],'logs/verificacion-completa.log');
  await step('informe_final',process.execPath,['informe-indexacion.mjs'],'logs/informe-indexacion.log');
  state.status='COMPLETED';state.completedAt=new Date().toISOString();delete state.error;
  await saveJSON(stateFile,state);console.log('Procesamiento terminado. Ver RESULTADO.md y state/informe-indexacion.json para alcance y excepciones.');
}catch(error){
  state.status=stopping?'PAUSED':'ERROR';state.error=error.message;state.updatedAt=new Date().toISOString();await saveJSON(stateFile,state);
  console.error(error.message);process.exitCode=stopping?75:1;
}
