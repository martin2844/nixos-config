"""OCR image pages of Office PDF renditions, without modifying source files."""
import os,json,sys,tempfile,pathlib,subprocess,re


def scan_pdf(source,language):
 extracted=subprocess.run(['pdftotext','-layout',str(source),'-'],capture_output=True,timeout=180,check=True).stdout.decode('utf8','replace')
 pages=extracted.split('\f')
 listing=subprocess.run(['pdfimages','-list',str(source)],capture_output=True,timeout=180,check=True).stdout.decode('utf8','replace')
 image_pages={int(line.split()[0]) for line in listing.splitlines() if line.split() and line.split()[0].isdigit()}
 candidates=[i+1 for i,text in enumerate(pages) if not text.strip() and i+1 in image_pages]
 result={'pagesWithImages':len(image_pages),'pagesNeedingOcr':candidates}
 if not candidates:return {**result,'status':'NO_MISSING_TEXT_PAGES'}
 with tempfile.TemporaryDirectory(prefix='ediloco-ocr-') as directory:
  output=pathlib.Path(directory)/'ocr.pdf';sidecar=pathlib.Path(directory)/'ocr.txt'
  cmd=['ocrmypdf','--skip-text','--pages',','.join(map(str,candidates)),'--output-type','pdf','--jobs','2','--language',language,'--deskew','--rotate-pages','--sidecar',str(sidecar),str(source),str(output)]
  run=subprocess.run(cmd,capture_output=True,timeout=7200,env={**os.environ,'OMP_THREAD_LIMIT':'1'})
  if run.returncode:raise RuntimeError(run.stderr.decode('utf8','replace')[-2000:])
  text=sidecar.read_text() if sidecar.exists() else ''
  text=re.sub(r'\[(?:OCR skipped|skipped|page already has text)[^\]]*\]','',text,flags=re.I).strip()
  return {**result,'status':'OCR_TEXT' if text else 'NO_TEXT_RECOGNIZED','extraText':text,'characters':len(text)}


def self_test():
 import hashlib
 from fpdf import FPDF
 from PIL import Image,ImageDraw,ImageFont
 with tempfile.TemporaryDirectory(prefix='ediloco-prueba-') as directory:
  root=pathlib.Path(directory)
  image=Image.new('RGB',(1800,2400),'white')
  draw=ImageDraw.Draw(image);font=ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',64)
  draw.text((120,250),'CONTROL EDILOCO OCR 2026',font=font,fill='black')
  draw.text((120,420),'Documento de prueba sin datos personales.',font=font,fill='black')
  image.save(root/'scan.png')
  pdf=FPDF();pdf.add_page();pdf.set_font('Helvetica',size=14);pdf.cell(text='Pagina digital con texto original conservado.')
  pdf.add_page();pdf.image(str(root/'scan.png'),x=0,y=0,w=210,h=280);pdf.output(root/'mixed.pdf')
  before=hashlib.sha256((root/'mixed.pdf').read_bytes()).hexdigest()
  result=scan_pdf(root/'mixed.pdf','spa+eng+por')
  assert result['pagesNeedingOcr']==[2],result
  assert 'CONTROL EDILOCO OCR 2026' in result['extraText'],result
  assert 'Pagina digital' not in result['extraText'],result
  assert hashlib.sha256((root/'mixed.pdf').read_bytes()).hexdigest()==before
  pdf=FPDF();pdf.add_page();pdf.set_font('Helvetica',size=14);pdf.cell(text='Documento exclusivamente digital.');pdf.output(root/'digital.pdf')
  assert scan_pdf(root/'digital.pdf','eng')['status']=='NO_MISSING_TEXT_PAGES'
  print(json.dumps({'test':'OCR adicional','mixedPageDetected':True,'recognizedText':True,'digitalTextPreserved':True,'sourceUnchanged':True}))


def main():
 if sys.argv[1]=='--self-test':self_test();return
 os.environ.setdefault('DJANGO_SETTINGS_MODULE','paperless.settings')
 import django;django.setup()
 from documents.models import Document
 from paperless.config import OcrConfig
 for document_id in json.loads(sys.argv[1]):
  result={'id':document_id}
  try:
   document=Document.objects.get(pk=document_id)
   if not document.archive_filename:result['status']='NO_ARCHIVE'
   else:result.update(scan_pdf(document.archive_path,OcrConfig().language))
  except Exception as error:result.update(status='ERROR',error=str(error))
  print('EDILOCO_RESULT '+json.dumps(result),flush=True)

if __name__=='__main__':main()
