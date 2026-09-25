"""Read-only source mount; derived searchable copies are written to /work/state."""
import hashlib,json,pathlib,re,subprocess,zipfile,urllib.request,urllib.error,time,datetime
from PIL import Image
from fpdf import FPDF
import magic

ROOT=pathlib.Path('/source')
WORK=pathlib.Path('/work')
OUT=WORK/'state/derivados'
OUT.mkdir(parents=True,exist_ok=True)
plan=json.loads((ROOT/'00_Indice_documentos/plan-de-copia.json').read_text())
STATE=WORK/'state/preparados-formatos.json'
state=json.loads(STATE.read_text()) if STATE.exists() else {}
HOST='/home/martin/Projects/documentos-ediloco/state/derivados'
def sha(data):return hashlib.sha256(data).hexdigest()
def save():
 temp=STATE.with_suffix('.tmp');temp.write_text(json.dumps(state,ensure_ascii=False,indent=2));temp.replace(STATE)
def store(entry,data,extension,strategy,**extra):
 dest=OUT/(entry['sha256']+extension);dest.write_bytes(data)
 state[entry['sha256']]={'payload':HOST+'/'+dest.name,'uploadName':pathlib.Path(entry['target']).name+extension,'payloadSha256':sha(data),'strategy':strategy,**extra}
def text_copy(entry,text,strategy,**extra):
 body=f"Documento: {pathlib.Path(entry['target']).name}\nUbicación original: {entry['target']}\n\nContenido extraído:\n{text}\n"
 store(entry,body.encode(),'.txt',strategy,**extra)
def text_pdf(entry,text,**extra):
 pdf=FPDF();pdf.set_auto_page_break(True,margin=12)
 pdf.add_font('Liberation',fname='/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf')
 pdf.set_font('Liberation',size=9);pdf.add_page()
 pdf.set_creation_date(datetime.datetime.fromtimestamp(entry['mtimeMs']/1000,datetime.timezone.utc))
 text=re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',text).replace('\t','    ')
 pdf.multi_cell(0,4,text=text,new_x='LMARGIN',new_y='NEXT',wrapmode='CHAR')
 store(entry,bytes(pdf.output()),'.pdf','texto_pdf',**extra)
def convert_office(source):
 boundary='paperless-ediloco-'+str(time.time_ns())
 body=(f'--{boundary}\r\nContent-Disposition: form-data; name="files"; filename="documento{source.suffix}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()+source.read_bytes()+f'\r\n--{boundary}--\r\n'.encode())
 req=urllib.request.Request('http://gotenberg:3000/forms/libreoffice/convert',data=body,headers={'Content-Type':'multipart/form-data; boundary='+boundary})
 with urllib.request.urlopen(req,timeout=180) as r:return r.read()
def tika_text(source):
 req=urllib.request.Request('http://tika:9998/tika',data=source.read_bytes(),method='PUT',headers={'Accept':'text/plain'})
 with urllib.request.urlopen(req,timeout=180) as r:return r.read().decode('utf8','replace').strip()
def dxf_text(data):
 try:lines=data.decode('utf8').splitlines()
 except UnicodeDecodeError:lines=data.decode('cp1252','replace').splitlines()
 text=[];kind=''
 for i in range(0,len(lines)-1,2):
  code,value=lines[i].strip(),lines[i+1].strip()
  if code=='0':kind=value
  if kind in ('TEXT','MTEXT','ATTRIB','ATTDEF','DIMENSION') and code in ('1','3'):
   text.append(re.sub(r'\\U\+([0-9A-Fa-f]{4})',lambda m:chr(int(m[1],16)),value))
 return '\n'.join(dict.fromkeys(text))

for entry in plan['entries']:
 key=entry['sha256'];target=entry['target'];source=ROOT/target;ext=source.suffix.lower()
 if source.name.startswith('._') and source.read_bytes()[:4]==b'\x00\x05\x16\x07':
  state[key]={'excluded':'metadatos auxiliares AppleDouble; no es el documento'};continue
 if key in state and 'conversionError' not in state[key] and state[key].get('strategy')!='texto_normalizado':continue
 if ext=='.dwg':continue
 if source.name.startswith('~$'):
  state[key]={'excluded':'archivo temporal de bloqueo de Microsoft Office'};continue
 if entry['bytes']==0:
  state[key]={'excluded':'archivo vacío'};continue
 if ext in ('.key','.csr','.crt','.ca-bundle'):
  state[key]={'excluded':'clave o certificado técnico; no es un documento para OCR'};continue
 if ext=='.mov':
  state[key]={'excluded':'video; Paperless no indexa contenido audiovisual'};continue
 if ext not in ('.ai','.psd','.pages','.numbers','.docm','.pptm','.dxf','.zip','.md','.txt','.csv','.ics','.ini','.base','.canvas'):continue
 data=source.read_bytes()
 if sha(data)!=key:raise RuntimeError('Fuente cambiada: '+target)
 try:
  if ext=='.ai' and data.startswith(b'%PDF'):
   state[key]={'payload':str(pathlib.Path(plan['destination'])/target),'uploadName':source.stem+'.pdf','payloadSha256':key,'strategy':'pdf_en_illustrator'}
  elif ext=='.psd':
   image=Image.open(source);dest=OUT/(key+'.png');image.convert('RGB').save(dest)
   state[key]={'payload':HOST+'/'+dest.name,'uploadName':source.name+'.png','payloadSha256':sha(dest.read_bytes()),'strategy':'imagen_renderizada'}
  elif ext in ('.pages','.numbers','.docm','.pptm'):
   try:
    pdf=convert_office(source)
    if not pdf.startswith(b'%PDF'):raise RuntimeError('La conversión no devolvió PDF')
    store(entry,pdf,'.pdf','office_convertido')
   except Exception as conversion_error:
    text=tika_text(source)
    if not text:raise RuntimeError('Sin texto extraíble: '+str(conversion_error))
    text_copy(entry,text,'texto_office',conversionWarning=str(conversion_error))
  elif ext=='.dxf':
   text=dxf_text(data)
   text_copy(entry,text or 'Sin anotaciones textuales; consultar la geometría en el original.','cad',status='texto_extraido' if text else 'solo_metadatos',extractedCharacters=len(text))
  elif ext=='.zip':
   members=[]
   with zipfile.ZipFile(source) as archive:
    if sum(i.file_size for i in archive.infolist())>500_000_000:raise RuntimeError('ZIP excede límite de extracción de 500 MB')
    for info in archive.infolist():
     if info.is_dir():continue
     member=archive.read(info);digest=sha(member);suffix=pathlib.Path(info.filename).suffix.lower()
     existing=next((e for e in plan['entries'] if e['sha256']==digest),None)
     item={'name':info.filename,'sha256':digest,'bytes':len(member),'existingTarget':existing['target'] if existing else None}
     if not existing and suffix in ('.pdf','.jpg','.jpeg','.png','.tif','.tiff','.doc','.docx','.txt'):
      dest=OUT/('zip-'+digest+suffix);dest.write_bytes(member);item['payload']=HOST+'/'+dest.name
     members.append(item)
   state[key]={'archiveMembers':members,'excluded':'contenedor ZIP: se indexan sus documentos internos sin duplicar los existentes'}
  elif ext in ('.md','.txt','.csv'):
   mime=magic.from_file(str(source),mime=True)
   if mime not in ('text/plain','text/csv','application/csv'):
    try:text=data.decode('utf8')
    except UnicodeDecodeError:text=data.decode('cp1252')
    text_pdf(entry,text,originalMime=mime)
  else:
   text=data.decode('utf8')
   if not text.strip() or text.strip()=='{}':state[key]={'excluded':'archivo vacío o configuración sin contenido documental'}
   else:text_copy(entry,text,'texto_tecnico')
 except Exception as error:
  state[key]={'conversionError':str(error)}
 save()
save()
print(json.dumps({'entradas':len(state),'preparados':sum('payload' in x for x in state.values()),'errores':sum('conversionError' in x for x in state.values()),'excluidos':sum('excluded' in x for x in state.values())}))
