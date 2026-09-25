import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {connect,json,saveJSON} from './paperless-api.mjs';
const {api,all}=await connect();
const ledger=JSON.parse(await fs.readFile('state/importaciones.json','utf8'));
const byId=new Map(Object.values(ledger).filter(r=>r.status==='SUCCESS').map(r=>[r.documentId,r]));
const documents=await all('/api/documents/?page_size=100');
const nativeOffice=/\.(docx?|xlsx?|pptx?|ppsx|od[tsgp]|rtf)$/i;
const eligible=documents.filter(d=>nativeOffice.test(byId.get(d.id)?.target??''));
const file='state/ocr-office.json';
const state=JSON.parse(await fs.readFile(file,'utf8').catch(e=>{if(e.code==='ENOENT')return '{}';throw e;}));
const pending=eligible.filter(d=>!state[d.id]);
if(pending.length){
  const child=spawn('docker',['compose','exec','--user','1000:100','-T','webserver','python','-',JSON.stringify(pending.map(d=>d.id))],{stdio:['pipe','pipe','inherit']});
  const completion=new Promise((resolve,reject)=>{child.on('error',reject);child.on('close',code=>code===0?resolve():reject(Error(`OCR Office: salida ${code}`)));});
  child.stdin.end(await fs.readFile('ocr-office.py'));
  for await(const line of createInterface({input:child.stdout})){
    if(!line.startsWith('EDILOCO_RESULT ')){console.log(line);continue;}
    const result=JSON.parse(line.slice(15));
    if(result.extraText){
      const d=await api(`/api/documents/${result.id}/`);
      if(!d.content.includes(result.extraText))await api(`/api/documents/${d.id}/`,json('PATCH',{content:d.content+'\n\nTexto reconocido en páginas escaneadas del documento:\n'+result.extraText}));
      delete result.extraText;
    }
    state[result.id]=result;await saveJSON(file,state);console.log(JSON.stringify(result));
  }
  await completion;
}
// PDF rendering may omit decorative Unicode glyphs. Index the complete source
// text for these conversions, including its original Unicode characters.
const prepared=JSON.parse(await fs.readFile('state/preparados-formatos.json','utf8'));
const plan=JSON.parse(await fs.readFile('/run/media/martin/Ediloco/Archivo-TheMartin/09_Documentos/00_Indice_documentos/plan-de-copia.json','utf8'));
for(const [hash,conversion] of Object.entries(prepared)){
  if(conversion.strategy!=='texto_pdf'||ledger[hash]?.status!=='SUCCESS')continue;
  const bytes=await fs.readFile(plan.destination+'/'+ledger[hash].target);
  let content;try{content=new TextDecoder('utf-8',{fatal:true}).decode(bytes);}catch{content=new TextDecoder('windows-1252').decode(bytes);}
  const d=await api(`/api/documents/${ledger[hash].documentId}/`);
  if(d.content!==content)await api(`/api/documents/${d.id}/`,json('PATCH',{content}));
}
console.log(JSON.stringify({officeRevisados:Object.keys(state).length,conOcrAgregado:Object.values(state).filter(r=>r.status==='OCR_TEXT').length,errores:Object.values(state).filter(r=>r.status==='ERROR').length}));
