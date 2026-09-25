#!/usr/bin/env python3
"""Restore public service code; keep credentials and runtime state outside Git."""
import datetime
import os
from pathlib import Path
import secrets
import shutil
import subprocess

REPO=Path(__file__).resolve().parent.parent
HOME=Path.home()
MOUNT=Path('/run/media/martin/Ediloco')
UUID='1c5b930d-5d2f-4b13-9577-661c73bc1993'

def install(home=HOME,repo=REPO):
 backup=home/'.local/state/nixos-config/backups'/('ediloco-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
 for name,project in [('paperless','documentos-ediloco'),('immich','immich-ediloco')]:
  runtime=home/'Projects'/project
  runtime.mkdir(parents=True,exist_ok=True)
  for source in (repo/'services'/name).iterdir():
   if (not source.is_file() or source.name in {'README.md','ACCESO.txt'}
       or source.name=='.env' or source.name.startswith('.env.')):continue
   destination=runtime/source.name
   if destination.exists() and destination.read_bytes()==source.read_bytes():continue
   if destination.exists() or destination.is_symlink():
    saved=backup/project/source.name;saved.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(destination,saved,follow_symlinks=False)
   # Replacing executable source by an atomic rename never truncates a running
   # interpreter's input and never follows a destination link into the repo.
   temporary=destination.with_name(destination.name+'.install-tmp')
   shutil.copy2(source,temporary);temporary.replace(destination)
  for directory in ['state','logs']:(runtime/directory).mkdir(exist_ok=True,mode=0o700)
  data=MOUNT/'Servicios'/('Paperless' if name=='paperless' else 'Immich')
  env=runtime/'.env'
  if not env.exists():
   admin=secrets.token_urlsafe(24)
   values={'DATA_ROOT':str(data),'DB_PASSWORD':secrets.token_hex(32),'ADMIN_PASSWORD':admin}
   if name=='paperless':values['SECRET_KEY']=secrets.token_hex(48)
   else:values['ADMIN_EMAIL']='martin@immich.local'
   descriptor=os.open(env,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
   with os.fdopen(descriptor,'w') as file:file.write(''.join(f'{k}={v}\n' for k,v in values.items()))
   access=runtime/'ACCESO.txt'
   descriptor=os.open(access,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
   with os.fdopen(descriptor,'w') as file:
    file.write(f"URL: http://localhost:{8010 if name=='paperless' else 2283}\nUsuario: {'martin' if name=='paperless' else values['ADMIN_EMAIL']}\nContraseña: {admin}\n")
  print(f'{name}: código instalado en {runtime}; credenciales privadas conservadas.')
 mounted=subprocess.run(['findmnt','-no','UUID','--target',str(MOUNT)],capture_output=True,text=True).stdout.strip()
 if mounted==UUID:
  for name,directories in [('Paperless',['data','media','export','postgres','redis','ollama']),('Immich',['library','postgres','redis','model-cache'])]:
   root=MOUNT/'Servicios'/name;root.mkdir(parents=True,exist_ok=True,mode=0o700)
   for directory in directories:(root/directory).mkdir(exist_ok=True,mode=0o700)
 else:print('Ediloco no está montado: no se crearon directorios de datos. Ejecutar otra vez con el disco conectado.')

if __name__=='__main__':install()
