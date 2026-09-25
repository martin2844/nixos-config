import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {connect,json,saveJSON} from './immich-api.mjs';
process.chdir(path.dirname(fileURLToPath(import.meta.url)));
if(execFileSync('findmnt',['-no','UUID','--target','/run/media/martin/Ediloco'],{encoding:'utf8'}).trim()!=='1c5b930d-5d2f-4b13-9577-661c73bc1993')throw Error('Ediloco no está montado.');
await fs.mkdir('state',{recursive:true,mode:0o700});
const {api,userId}=await connect({signup:true});
await api(`/admin/users/${userId}`,json('PUT',{shouldChangePassword:false}));
const config=await api('/admin/config');
config.machineLearning.enabled=true;
config.machineLearning.urls=['http://immich-machine-learning:3003'];
config.machineLearning.clip={...config.machineLearning.clip,enabled:true,modelName:'ViT-SO400M-16-SigLIP2-384__webli'};
config.machineLearning.facialRecognition={...config.machineLearning.facialRecognition,enabled:true,modelName:'buffalo_l'};
config.machineLearning.ocr={...config.machineLearning.ocr,enabled:true};
config.machineLearning.duplicateDetection.enabled=true;
config.reverseGeocoding.enabled=true;
// City/country lookup is local; disable the external map tile provider.
config.map.enabled=false;
config.newVersionCheck.enabled=false;
config.server.loginPageMessage='Fotos de Ediloco · biblioteca local';
for(const [name,job] of Object.entries(config.job))job.concurrency=['metadataExtraction','thumbnailGeneration','library'].includes(name)?2:1;
await api('/admin/config',json('PUT',config));
await api('/users/me/preferences',json('PUT',{folders:{enabled:true,sidebarWeb:true}}));
await api('/queues/videoConversion',json('PUT',{isPaused:true}));
for(const name of ['faceDetection','smartSearch','ocr']){
  await api(`/queues/${name}`,json('PUT',{isPaused:process.argv.includes('--pausar-ia')}));
}
const videoExtensions=['3gp','3gpp','avi','flv','insv','m2t','m2ts','m4v','mkv','mov','mp4','mpe','mpeg','mpg','mts','mxf','ts','vob','webm','wmv'];
// One case-insensitive glob covers mixed-case extensions too and avoids
// exhausting PostgreSQL's small compiled-regex cache during library rescans.
const videoPattern='**/*.{'+videoExtensions.map(ext=>[...ext].map(c=>/[a-z]/.test(c)?`[${c}${c.toUpperCase()}]`:c).join('')).join(',')+'}';
const exclusionPatterns=[
  '**/00_Control/**','**/09_Documentos/**','**/._*',
  videoPattern
];
const spec={name:'Fotos de TheMartin en Ediloco',importPaths:['/external/Archivo-TheMartin'],exclusionPatterns};
let library=(await api('/libraries')).find(l=>l.name===spec.name);
if(library)library=await api(`/libraries/${library.id}`,json('PUT',spec));
else library=await api('/libraries',json('POST',{...spec,ownerId:userId}));
const validation=await api(`/libraries/${library.id}/validate`,json('POST',{importPaths:spec.importPaths,exclusionPatterns}));
await saveJSON('state/configuracion.json',{date:new Date().toISOString(),library,validation,models:{search:config.machineLearning.clip.modelName,faces:config.machineLearning.facialRecognition.modelName,ocr:config.machineLearning.ocr.modelName},concurrency:config.job});
// Fail before starting if the server cannot read an import path.
if(JSON.stringify(validation).includes('"isValid":false'))throw Error('Una ruta de la biblioteca no es válida; ver state/configuracion.json');
await api(`/libraries/${library.id}/scan`,{method:'POST'});
console.log(JSON.stringify({biblioteca:library.id,escaneoIniciado:true,modelos:{busqueda:config.machineLearning.clip.modelName,caras:config.machineLearning.facialRecognition.modelName,ocr:config.machineLearning.ocr.modelName}}));
