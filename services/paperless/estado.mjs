import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
process.chdir(path.dirname(fileURLToPath(import.meta.url)));
for(const name of ['indexacion-completa','progreso']){
  const state=JSON.parse(await fs.readFile(`state/${name}.json`,'utf8'));
  if(name==='progreso')console.log(`Archivos del inventario: ${state.totalInventario}\nDocumentos a procesar: ${state.compatibles}\nProcesados: ${state.estados.SUCCESS??0}\nEn cola o procesándose: ${(state.estados.PENDING??0)+(state.estados.STARTED??0)+(state.estados.QUEUED??0)}\nExcluidos: ${state.estados.EXCLUDED??0}\nErrores: ${(state.estados.FAILURE??0)+(state.estados.REJECTED??0)}\nActualización: ${state.fecha}`);
  else console.log(`Estado: ${state.status}\nEtapa: ${state.phase}${state.error?'\nDetalle: '+state.error:''}`);
}
