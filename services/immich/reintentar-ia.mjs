// Queue only missing analyses. Immich requires no active jobs when starting
// a "missing" sweep, so let in-flight requests finish without removing jobs.
import {setTimeout as delay} from 'node:timers/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {connect,json,saveJSON} from './immich-api.mjs';

process.chdir(path.dirname(fileURLToPath(import.meta.url)));
const names=['faceDetection','smartSearch','ocr'];
const {api}=await connect();
let interrupted=false;
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>{interrupted=true;});
try {
  for(const name of names)await api(`/queues/${name}`,json('PUT',{isPaused:true}));
  const deadline=Date.now()+10*60*1000;
  while(true){
    if(interrupted)throw Error('Interrumpido; se reanudarán las colas.');
    const queues=await api('/queues');
    if(queues.filter(q=>names.includes(q.name)).every(q=>q.statistics.active===0))break;
    if(Date.now()>deadline)throw Error('Los trabajos activos siguen ejecutándose; se reanudarán las colas sin vaciarlas.');
    await delay(5000);
  }
  for(const name of names)await api(`/jobs/${name}`,json('PUT',{command:'start',force:false}));
  await saveJSON('state/reintento-pendientes.json',{date:new Date().toISOString(),queues:names,onlyMissing:true});
  console.log('Análisis faltantes reencolados; los análisis completados se conservan.');
} finally {
  const resumed=await Promise.allSettled(names.map(name=>api(`/queues/${name}`,json('PUT',{isPaused:false}))));
  for(let i=0;i<resumed.length;i++)if(resumed[i].status==='rejected'){
    console.error(`No se pudo reanudar ${names[i]}: ${resumed[i].reason.message}`);
    process.exitCode=1;
  }
}
