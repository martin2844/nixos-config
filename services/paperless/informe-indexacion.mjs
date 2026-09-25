import fs from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {connect,saveJSON} from './paperless-api.mjs';
const run=promisify(execFile);
const {api}=await connect();
const read=async(file,fallback={})=>JSON.parse(await fs.readFile(file,'utf8').catch(e=>{if(e.code==='ENOENT')return JSON.stringify(fallback);throw e;}));
const plan=await read('/run/media/martin/Ediloco/Archivo-TheMartin/09_Documentos/00_Indice_documentos/plan-de-copia.json');
const ledger=await read('state/importaciones.json');
const prepared={...await read('state/preparados-cad.json'),...await read('state/preparados-formatos.json'),...await read('state/preparados-recuperacion.json')};
const documents=new Map();let next='/api/documents/?page_size=100';
while(next){
  const page=await api(next);
  for(const d of page.results)documents.set(d.id,{id:d.id,characters:d.content.trim().length,pages:d.page_count,mime:d.mime_type,archive:!!d.archived_file_name});
  next=page.next?new URL(page.next).pathname+new URL(page.next).search:null;
}
const rows=plan.entries.map(e=>{
  const r=ledger[e.sha256],conversion=prepared[e.sha256],d=documents.get(r?.documentId);
  return {target:e.target,sha256:e.sha256,bytes:e.bytes,status:r?.status??'MISSING',documentId:r?.documentId,
    strategy:r?.strategy,metadataOnly:conversion?.status==='solo_metadatos',characters:d?.characters,pages:d?.pages,
    excluded:r?.reason,error:r?.status==='SUCCESS'?undefined:r?.error};
});
const counts={};for(const r of rows)counts[r.status]=(counts[r.status]??0)+1;
const unclassified=rows.filter(r=>!['SUCCESS','EXCLUDED','FAILURE','REJECTED'].includes(r.status));
if(unclassified.length)throw Error(`${unclassified.length} archivos todavía pendientes; el informe final no puede cerrarse.`);
const missing=rows.filter(r=>r.status==='SUCCESS'&&!documents.has(r.documentId));
if(missing.length)throw Error(`${missing.length} documentos importados no aparecen en Paperless.`);
const source=`import os,json\nos.environ.setdefault('DJANGO_SETTINGS_MODULE','paperless.settings')\nimport django;django.setup()\nfrom documents.models import Document\nfrom paperless_ai.indexing import read_store\nwith read_store() as store: times=store.get_modified_times()\ndocuments=list(Document.objects.values_list('id','modified'))\nmissing=[i for i,m in documents if str(i) not in times]\nstale=[i for i,m in documents if str(i) in times and times[str(i)]!=m.isoformat()]\nprint('EDILOCO_RESULT '+json.dumps({'documents':len(documents),'indexed':len(times),'missing':missing,'stale':stale}))\n`;
const result=await run('docker',['compose','exec','--user','1000:100','-T','webserver','python','-c',source],{maxBuffer:5e6});
const semantic=JSON.parse(result.stdout.split('\n').find(l=>l.startsWith('EDILOCO_RESULT ')).slice(15));
if(semantic.missing.length||semantic.stale.length)throw Error(`Índice semántico incompleto: ${semantic.missing.length} ausentes, ${semantic.stale.length} desactualizados.`);
const verification=await read('state/verificacion.json');
if(verification.originalesRevisados!==plan.entries.length||verification.copiasVerificadas!==counts.SUCCESS)throw Error('La verificación de integridad no cubre el inventario completo.');
const pdfReview=await read('state/revision-pdfs-previos.json',{documents:[]});
const office=await read('state/ocr-office.json');
const report={date:new Date().toISOString(),inventory:plan.entries.length,counts,semantic,verification,
  withText:rows.filter(r=>r.status==='SUCCESS'&&r.characters>0&&!r.metadataOnly).length,
  metadataOnly:rows.filter(r=>r.status==='SUCCESS'&&r.metadataOnly).length,
  withoutRecognizedText:rows.filter(r=>r.status==='SUCCESS'&&!r.characters),
  excluded:rows.filter(r=>r.status==='EXCLUDED'),failed:rows.filter(r=>['FAILURE','REJECTED'].includes(r.status)),
  pdfReviewErrors:pdfReview.documents.filter(r=>r.status!=='SUCCESS'),
  officeOcrErrors:Object.values(office).filter(r=>r.status==='ERROR'||r.status==='NO_ARCHIVE'),rows};
await saveJSON('state/informe-indexacion.json',report);
const attention=report.failed.length+report.withoutRecognizedText.length+report.pdfReviewErrors.length+report.officeOcrErrors.length;
const markdown=`# Indexación de Documentos Ediloco\n\nProcesamiento terminado el ${new Date(report.date).toLocaleString('es-ES',{timeZone:'Europe/Madrid'})} (Madrid). ${attention?'Hay observaciones para revisar.':'Sin errores de importación detectados.'}\n\nAbrir **http://localhost:8010**. Usuario **martin**; contraseña en \\ACCESO.txt\\.\n\n- Inventario completo revisado: **${plan.entries.length} archivos**.\n- Documentos disponibles en Paperless: **${counts.SUCCESS??0}**.\n- Con texto extraído o reconocido (incluye anotaciones CAD): **${report.withText}**.\n- Planos catalogados sólo por nombre y carpeta: **${report.metadataOnly}**.\n- Sin texto reconocido: **${report.withoutRecognizedText.length}**.\n- Archivos excluidos del OCR: **${counts.EXCLUDED??0}**. Se conservan en sus carpetas; incluyen temporales, vacíos, archivos técnicos, videos y ZIP cuyos documentos internos ya estaban en el inventario.\n- Errores de importación: **${report.failed.length}**. Observaciones de revisión PDF: **${report.pdfReviewErrors.length}**; Office: **${report.officeOcrErrors.length}**.\n- Índice semántico actualizado: **${semantic.indexed} documentos**, con BGE-M3 local. Qwen3.5:9b para consultas.\n- Integridad: **${verification.originalesRevisados} fuentes** comparadas con el SHA256 original, **${verification.copiasIdenticas} copias idénticas** y **${verification.derivadosVerificados} derivados verificados**.\n\nLos originales no se movieron, borraron ni reemplazaron. El OCR trabaja sobre copias. Los formatos especiales usan derivados para la búsqueda; el campo **Archivo de origen** permite encontrar el archivo original.\n\nPara buscar, escribir casa, dni o pasaporte y pulsar Enter. El chat permite preguntas por significado con referencias. El OCR puede cometer errores y las imágenes sin texto legible no se describen por su contenido visual.\n\nEl detalle por archivo y las excepciones están en [state/informe-indexacion.json](state/informe-indexacion.json). Las verificaciones del servicio inicial están en state/prueba-servicio.json y state/prueba-interfaz.json.\n\nAntes de desconectar Ediloco: \\./detener.sh\\. Instrucciones completas en [README.md](README.md).\n`.replaceAll('\\','`');
await fs.writeFile('RESULTADO.md',markdown);
console.log(JSON.stringify({inventory:report.inventory,counts,withText:report.withText,metadataOnly:report.metadataOnly,withoutRecognizedText:report.withoutRecognizedText.length,semanticIndexed:semantic.indexed}));
