import fs from 'node:fs/promises';
import {connect,json,saveJSON} from './paperless-api.mjs';
const {api,all}=await connect();
const file='state/revision-pdfs-previos.json';
let revision;
try{revision=JSON.parse(await fs.readFile(file,'utf8'));}catch(e){if(e.code!=='ENOENT')throw e;}
if(!revision){
  const documents=await all('/api/documents/?page_size=100');
  revision={createdAt:new Date().toISOString(),documents:documents.filter(d=>d.mime_type==='application/pdf').map(d=>({id:d.id,status:'PENDING'}))};
  await saveJSON(file,revision);
}
const config=(await api('/api/config/'))[0];
await api(`/api/config/${config.id}/`,json('PATCH',{mode:'auto',archive_file_generation:'always',output_type:'pdf'}));
console.log(JSON.stringify({ocr:'auto por página',archivo:'PDF con texto y OCR cuando falta',pdfsPreviosParaRevisar:revision.documents.length}));
