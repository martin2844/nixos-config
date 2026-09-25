import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {saveJSON} from './paperless-api.mjs';
const file='state/revision-pdfs-previos.json';
const state=JSON.parse(await fs.readFile(file,'utf8'));
const pending=state.documents.filter(d=>!['SUCCESS','ERROR'].includes(d.status));
if(pending.length){
  const child=spawn('docker',['compose','exec','--user','1000:100','-T','webserver','python','-'],{stdio:['pipe','pipe','inherit']});
  const completion=new Promise((resolve,reject)=>{child.on('error',reject);child.on('close',code=>code===0?resolve():reject(Error(`Revisión PDF: salida ${code}`)));});
  child.stdin.end(`import os,json,logging\nos.environ.setdefault('DJANGO_SETTINGS_MODULE','paperless.settings')\nimport django;django.setup()\nfrom documents.tasks import update_document_content_maybe_archive_file\nfrom documents.models import Document\nclass Capture(logging.Handler):\n def emit(self,r):\n  if r.levelno>=logging.ERROR:self.errors.append(r.getMessage())\ncapture=Capture();logging.getLogger('paperless.tasks').addHandler(capture)\nfor document_id in ${JSON.stringify(pending.map(d=>d.id))}:\n capture.errors=[]\n try:\n  update_document_content_maybe_archive_file.run(document_id)\n  d=Document.objects.get(pk=document_id)\n  if capture.errors:raise RuntimeError('; '.join(capture.errors))\n  if not d.archive_filename:raise RuntimeError('No se pudo generar la copia PDF buscable; revisar cifrado o firma')\n  result={'id':document_id,'status':'SUCCESS','characters':len(d.content)}\n except Exception as e:result={'id':document_id,'status':'ERROR','error':str(e)}\n print('EDILOCO_RESULT '+json.dumps(result),flush=True)\n`);
  for await(const line of createInterface({input:child.stdout})){
    if(line.startsWith('EDILOCO_RESULT ')){
      const result=JSON.parse(line.slice(15));Object.assign(state.documents.find(d=>d.id===result.id),result);await saveJSON(file,state);console.log(JSON.stringify(result));
    }else console.log(line);
  }
  await completion;
}
console.log(JSON.stringify({revisados:state.documents.length,errores:state.documents.filter(d=>d.status==='ERROR').length}));
