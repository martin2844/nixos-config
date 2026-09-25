import fs from 'node:fs/promises';
import {createReadStream,openAsBlob} from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import {CLASSIFICATION_VERSION, classifyDocument, desiredTags, ensureCategories} from './clasificacion.mjs';

process.chdir(path.dirname(fileURLToPath(import.meta.url)));
let stopRequested=false;
for(const signal of ['SIGTERM','SIGINT'])process.on(signal,()=>{stopRequested=true;console.log('Pausa solicitada; guardando el estado de la importación.');});
const hashStream=async stream=>{const hash=crypto.createHash('sha256');for await(const chunk of stream)hash.update(chunk);return hash.digest('hex');};
const hashFile=file=>hashStream(createReadStream(file));
const mode = process.argv[2] ?? '--plan';
if (!['--plan', '--piloto', '--todos', '--estado', '--verificar'].includes(mode)) {
  throw new Error('Uso: node importar.mjs --plan|--piloto|--todos|--estado|--verificar');
}
const mount = '/run/media/martin/Ediloco';
const uuid = execFileSync('findmnt', ['-no', 'UUID', '--target', mount], { encoding: 'utf8' }).trim();
if (uuid !== '1c5b930d-5d2f-4b13-9577-661c73bc1993') throw new Error('Ediloco no está montado correctamente.');
const plan = JSON.parse(await fs.readFile(`${mount}/Archivo-TheMartin/09_Documentos/00_Indice_documentos/plan-de-copia.json`, 'utf8'));
const prepared={};
for(const file of ['state/preparados-cad.json','state/preparados-formatos.json','state/preparados-recuperacion.json']){
  Object.assign(prepared,JSON.parse(await fs.readFile(file,'utf8').catch(e=>{if(e.code==='ENOENT')return '{}';throw e;})));
}
const supported = /\.(pdf|jpe?g|jfif|png|tiff?|bmp|gif|webp|heic|txt|md|docx?|xlsx?|pptx?|ppsx|od[tsgp]|rtf|csv|eml)$/i;
const eligible = plan.entries.filter(e => !prepared[e.sha256]?.excluded && !prepared[e.sha256]?.conversionError && (supported.test(e.target)||prepared[e.sha256]?.payload)).sort((a,b)=>a.bytes-b.bytes);
const pilot = eligible.filter(e =>
  /^(Vivienda\/|Identidad_y_tramites\/(DNI_y_NIE|Empadronamiento)\/)/.test(e.target) ||
  (/^Identidad_y_tramites\/Pasaportes\//.test(e.target) && !/\/Martina\/\d+\.jpg$/i.test(e.target))
);
if (mode === '--plan') {
  console.log(JSON.stringify({ total: plan.entries.length, compatibles: eligible.length, piloto: pilot.length,
    bytesPiloto: pilot.reduce((n,e)=>n+e.bytes,0), omitidos: plan.entries.length-eligible.length },null,2));
  process.exit(0);
}

await fs.mkdir('state', { recursive: true, mode: 0o700 });
const lock = await fs.open('state/import.lock', 'wx').catch(() => { throw new Error('Ya existe state/import.lock. Comprobá que no haya otra importación antes de quitarlo.'); });
try {
  const env = Object.fromEntries((await fs.readFile('.env','utf8')).trim().split('\n').map(line => {
    const index=line.indexOf('='); return [line.slice(0,index),line.slice(index+1)];
  }));
  const base='http://127.0.0.1:8010';
  const login=await fetch(`${base}/api/token/`,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({username:'martin',password:env.ADMIN_PASSWORD})});
  if(!login.ok) throw new Error(`Login HTTP ${login.status}`);
  const {token}=await login.json();
  const api=async (endpoint, options={})=> {
    const res=await fetch(base+endpoint,{signal:AbortSignal.timeout(900000),...options,headers:{Authorization:`Token ${token}`,...options.headers}});
    if(!res.ok) {const error=new Error(`${endpoint}: HTTP ${res.status}: ${(await res.text()).slice(0,500)}`);error.status=res.status;throw error;}
    return res.json();
  };
  const json=(method,data)=>({method,headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  let ledger=JSON.parse(await fs.readFile('state/importaciones.json','utf8').catch(e=>{if(e.code==='ENOENT')return '{}';throw e;}));
  for(const record of Object.values(ledger))record.status=record.status.toUpperCase();
  const save=async()=>{await fs.writeFile('state/importaciones.tmp',JSON.stringify(ledger,null,2),{mode:0o600});await fs.rename('state/importaciones.tmp','state/importaciones.json');};
  const previousClassification=JSON.parse(await fs.readFile('state/clasificacion.json','utf8').catch(e=>{if(e.code==='ENOENT')return '{}';throw e;}));
  const previouslyClassified=new Set(previousClassification.version===CLASSIFICATION_VERSION?previousClassification.decisions.map(d=>Number(d.id)):[]);
  let classificationTags;
  const getAll=async endpoint=>{let url=endpoint;const out=[];while(url){const page=await api(url);out.push(...page.results);url=page.next?new URL(page.next).pathname+new URL(page.next).search:null;}return out;};

  const active=()=>Object.values(ledger).filter(r=>!['SUCCESS','FAILURE','REJECTED','EXCLUDED'].includes(r.status));
  const reconcile=async()=> {
    for(const record of Object.values(ledger)) if(record.task && (!['SUCCESS','FAILURE','REJECTED','EXCLUDED'].includes(record.status) || (record.status==='SUCCESS' && !record.documentId))) {
      const response=await api(`/api/tasks/?task_id=${encodeURIComponent(record.task)}`);
      const tasks=Array.isArray(response)?response:response.results;
      const task=tasks.find(t=>t.task_id===record.task);
      if(task) {record.status=task.status.toUpperCase(); record.documentId=task.result_data?.document_id??task.related_document_ids?.[0]??task.related_document; if(record.status==='FAILURE')record.error=task.result_data??task.result;}
    }
    if(['--todos','--piloto'].includes(mode)) for(const record of Object.values(ledger)) {
      if(record.status!=='SUCCESS' || !record.documentId || record.classificationVersion===CLASSIFICATION_VERSION)continue;
      if(!previouslyClassified.has(Number(record.documentId))){
        classificationTags??=await ensureCategories(api,getAll,json);
        const doc=await api(`/api/documents/${record.documentId}/`);
        const classification=classifyDocument(doc,path.resolve(plan.destination,record.target));
        const tags=desiredTags(doc,classificationTags,classification.category);
        if(JSON.stringify([...doc.tags].sort((a,b)=>a-b))!==JSON.stringify(tags))await api(`/api/documents/${doc.id}/`,json('PATCH',{tags}));
      }
      record.classificationVersion=CLASSIFICATION_VERSION;
    }
    await save();
    const counts={};for(const r of Object.values(ledger))counts[r.status]=(counts[r.status]??0)+1;
    const progress={fecha:new Date().toISOString(),totalInventario:plan.entries.length,compatibles:eligible.length,importaciones:Object.keys(ledger).length,estados:counts};
    await fs.writeFile('state/progreso.tmp',JSON.stringify(progress,null,2),{mode:0o600});
    await fs.rename('state/progreso.tmp','state/progreso.json');
    console.log(JSON.stringify(progress));
  };
  if(mode==='--estado') {await reconcile();}
  else if(mode==='--verificar') {
    await reconcile();
    let checked=0,originalCopies=0,derivedCopies=0;
    for(const record of Object.values(ledger)) {
      const source=path.resolve(plan.destination,record.target);
      const hash=await hashFile(source);
      if(hash!==record.sha256) throw new Error(`Origen cambiado: ${record.target}`);
      if(record.status==='SUCCESS') {
        if(!Number.isInteger(Number(record.documentId)))throw new Error(`Falta el identificador del documento: ${record.target}`);
        const res=await fetch(`${base}/api/documents/${record.documentId}/download/?original=true`,{headers:{Authorization:`Token ${token}`}});
        if(!res.ok) throw new Error(`Descarga HTTP ${res.status}`);
        const copyHash=await hashStream(res.body);
        if(copyHash!==(record.payloadSha256??hash)) throw new Error(`Copia diferente: ${record.target}`);
        if(copyHash===hash)originalCopies++;else derivedCopies++;
        checked++;
      }
    }
    await fs.writeFile('state/verificacion.json',JSON.stringify({fecha:new Date().toISOString(),originalesRevisados:Object.keys(ledger).length,copiasVerificadas:checked,copiasIdenticas:originalCopies,derivadosVerificados:derivedCopies},null,2),{mode:0o600});
    console.log(`SHA256: ${originalCopies} copias de originales y ${derivedCopies} derivados verificados; fuentes conservadas.`);
  } else {
    // Recover a request interrupted after POST only from positive API evidence.
    // If no task/document is found, leave the intent intact for manual review.
    for(const record of Object.values(ledger).filter(r=>r.status==='SUBMITTING')){
      const source=path.resolve(plan.destination,record.target);
      const since=new Date(new Date(record.submittedAt).getTime()-60000).toISOString();
      const containsSource=value=>value===source||(value&&typeof value==='object'&&Object.values(value).some(containsSource));
      const tasks=(await getAll(`/api/tasks/?page_size=100&date_created_after=${encodeURIComponent(since)}`)).filter(t=>t.task_id!==record.previousTask&&containsSource(t.input_data));
      if(tasks.length===1){record.task=tasks[0].task_id;record.status=tasks[0].status.toUpperCase();record.documentId=tasks[0].result_data?.document_id??tasks[0].related_document_ids?.[0];await save();continue;}
      const documents=(await getAll('/api/documents/?page_size=100')).filter(d=>d.custom_fields.some(f=>f.value===source));
      if(documents.length===1){
        const response=await fetch(`${base}/api/documents/${documents[0].id}/download/?original=true`,{headers:{Authorization:`Token ${token}`}});
        if(response.ok&&await hashStream(response.body)===record.payloadSha256){record.status='SUCCESS';record.documentId=documents[0].id;await save();continue;}
      }
      throw Error(`Envío interrumpido sin evidencia suficiente para reenviarlo: ${record.target}. Revisar tareas en Paperless.`);
    }
    classificationTags=await ensureCategories(api,getAll,json);
    const fields=await getAll('/api/custom_fields/?page_size=100');
    const sourceField=fields.find(f=>f.name==='Archivo de origen')??await api('/api/custom_fields/',json('POST',{name:'Archivo de origen',data_type:'longtext'}));
    if(sourceField.data_type!=='longtext')throw new Error('Archivo de origen debe ser un campo de texto largo.');
    let queued=0;
    for(const entry of plan.entries){
      const conversion=prepared[entry.sha256];
      if((conversion?.excluded||conversion?.conversionError) && ledger[entry.sha256]?.status!=='SUCCESS'){
        ledger[entry.sha256]={...ledger[entry.sha256],sha256:entry.sha256,target:entry.target,bytes:entry.bytes,status:'EXCLUDED',reason:conversion.excluded??conversion.conversionError};
      }
    }
    await reconcile();
    while(active().length>40 && !stopRequested){await new Promise(r=>setTimeout(r,15000));await reconcile();}
    for(const entry of mode==='--todos'?eligible:pilot) {
      if(stopRequested)break;
      const conversion=prepared[entry.sha256];
      const previous=ledger[entry.sha256];
      const correctedPayload=conversion?.payloadSha256 && previous?.payloadSha256!==conversion.payloadSha256;
      if(previous && !(previous.status==='REJECTED' || (['FAILURE','EXCLUDED'].includes(previous.status)&&correctedPayload))) continue;
      const source=path.resolve(plan.destination,entry.target);
      if(!source.startsWith(path.resolve(plan.destination)+path.sep))throw new Error('Ruta fuera de Documentos.');
      const stat=await fs.lstat(source);if(!stat.isFile())throw new Error(`El origen no es un archivo regular: ${entry.target}`);
      const hash=await hashFile(source);
      if(hash!==entry.sha256 || stat.size!==entry.bytes)throw new Error(`El origen cambió respecto del inventario: ${entry.target}`);
      const classification=classifyDocument({original_file_name:path.basename(source)},source);
      const tags=[classificationTags.find(t=>t.name===classification.category).id];
      const form=new FormData();
      // Markdown bytes are preserved; the upload name selects the plain-text parser.
      const uploadName=conversion?.uploadName??(/\.md$/i.test(source)?path.basename(source)+'.txt':path.basename(source));
      const payloadPath=conversion?.payload??source;
      const payloadSha256=payloadPath===source?hash:await hashFile(payloadPath);
      if(conversion?.payloadSha256 && conversion.payloadSha256!==payloadSha256)throw new Error(`Conversión cambiada: ${entry.target}`);
      form.append('document',await openAsBlob(payloadPath),uploadName);
      const context=path.dirname(entry.target).split('/').slice(1).join(' · ').replaceAll('_',' ');
      form.append('title',`${context?`${context} — `:''}${path.basename(source,path.extname(source))}`.slice(0,128));
      for(const tag of tags)form.append('tags',String(tag));
      form.append('custom_fields',JSON.stringify({[sourceField.id]:source}));
      // Persist the intent before POST. An ambiguous interrupted upload is never retried automatically.
      ledger[hash]={sha256:hash,target:entry.target,bytes:entry.bytes,payloadSha256,strategy:conversion?.strategy??'original',status:'SUBMITTING',submittedAt:new Date().toISOString(),previousTask:previous?.task};
      await save();
      let task;
      try {task=await api('/api/documents/post_document/',{method:'POST',body:form});}
      catch(error){
        if(error.status>=400 && error.status<500){ledger[hash].status='REJECTED';ledger[hash].error=error.message;await save();}
        if(ledger[hash].status==='REJECTED'){console.error(`Rechazado: ${entry.target}: ${error.message}`);continue;}
        throw error;
      }
      ledger[hash].task=task;ledger[hash].status='QUEUED';await save();
      queued++;console.log(`Enviado ${queued}: ${entry.target}`);
      // Keep the OCR queue bounded when importing the full collection.
      if(queued%20===0){await reconcile();while(active().length>40 && !stopRequested){await new Promise(r=>setTimeout(r,15000));await reconcile();}}
    }
    await reconcile();
    while(active().length && !stopRequested){await new Promise(r=>setTimeout(r,15000));await reconcile();}
    if(stopRequested)process.exitCode=75;
  }
} finally {
  await lock.close();await fs.unlink('state/import.lock');
}
