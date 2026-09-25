"""Installation must preserve credentials/data and back up changed code."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('install_ediloco',REPO/'scripts/install-ediloco.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class EdilocoTests(unittest.TestCase):
 def launcher(self, root, app='paperless', args=(), commands=None):
  defaults={
   'findmnt':'echo 1c5b930d-5d2f-4b13-9577-661c73bc1993',
   'notify-send':'exit 0',
   'curl':'if [ -e "$HOME/ready" ]; then printf 200; else exit 7; fi',
   'systemctl':'''echo "$*" >> "$HOME/systemctl-log"
case "$*" in
  *is-active*) exit 3 ;;
  *start*) touch "$HOME/ready" ;;
esac''',
   'sleep':'exit 0',
   'xdg-open':'printf "%s" "$1" > "$HOME/opened"',
  }
  defaults.update(commands or {})
  bindir=root/'bin';bindir.mkdir(exist_ok=True)
  for name,code in defaults.items():
   p=bindir/name;p.write_text('#!/bin/sh\n'+code+'\n');p.chmod(0o755)
  env={**os.environ,'HOME':str(root),'XDG_RUNTIME_DIR':str(root/'run'),
       'PATH':str(bindir)+':'+os.environ['PATH']}
  return subprocess.run(['bash',str(REPO/'home/.local/bin/ediloco-app'),app,*args],
                        env=env,capture_output=True,text=True,timeout=10)

 def test_cold_launch_starts_only_selected_library_before_opening(self):
  for app,url in [('paperless','http://localhost:8010'),('immich','http://localhost:2283')]:
   with self.subTest(app=app),tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    r=self.launcher(root,app)
    self.assertEqual(r.returncode,0,r.stderr)
    self.assertEqual((root/'opened').read_text(),url)
    self.assertIn(f'--user start {app}.service',(root/'systemctl-log').read_text())
    self.assertNotIn('immich' if app=='paperless' else 'paperless',(root/'systemctl-log').read_text())

 def test_unresponsive_active_unit_is_restarted(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   r=self.launcher(root,commands={'systemctl':'''echo "$*" >> "$HOME/systemctl-log"
case "$*" in
  *is-active*) exit 0 ;;
  *restart*) touch "$HOME/ready" ;;
  *) exit 95 ;;
esac'''})
   self.assertEqual(r.returncode,0,r.stderr)
   self.assertIn('--user restart paperless.service',(root/'systemctl-log').read_text())
   self.assertTrue((root/'opened').exists())

 def test_failed_start_or_readiness_never_opens_browser(self):
  for commands in [{'systemctl':'exit 1'}, {'curl':'exit 7'}]:
   with self.subTest(commands=commands),tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    r=self.launcher(root,commands=commands)
    self.assertNotEqual(r.returncode,0)
    self.assertFalse((root/'opened').exists())

 def test_missing_disk_prevents_start(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   r=self.launcher(root,commands={'findmnt':'echo wrong-disk'})
   self.assertNotEqual(r.returncode,0)
   self.assertFalse((root/'systemctl-log').exists())
   self.assertFalse((root/'opened').exists())

 def test_stop_works_without_disk_and_covers_cli_started_containers(self):
  for app,project in [('paperless','documentos-ediloco'),('immich','immich-ediloco')]:
   with self.subTest(app=app),tempfile.TemporaryDirectory() as directory:
    root=Path(directory);runtime=root/'Projects'/project;runtime.mkdir(parents=True)
    stop=runtime/'detener.sh'
    stop.write_text('#!/bin/sh\necho stopped > "$HOME/stopped"\n');stop.chmod(0o755)
    r=self.launcher(root,app,args=['--stop'],commands={'findmnt':'exit 96'})
    self.assertEqual(r.returncode,0,r.stderr)
    self.assertEqual((root/'systemctl-log').read_text().splitlines(),[f'--user stop {app}.service'])
    self.assertTrue((root/'stopped').exists())
    self.assertFalse((root/'opened').exists())

 def test_shutdown_failure_is_reported(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);runtime=root/'Projects/documentos-ediloco';runtime.mkdir(parents=True)
   stop=runtime/'detener.sh';stop.write_text('#!/bin/sh\nexit 1\n');stop.chmod(0o755)
   r=self.launcher(root,args=['--stop'])
   self.assertNotEqual(r.returncode,0)
   self.assertFalse((root/'opened').exists())

 def test_migration_changes_only_target_projects_without_starting_or_stopping(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   unitdir=root/'.config/systemd/user';unitdir.mkdir(parents=True)
   unit=unitdir/'paperless.service';unit.symlink_to(REPO/'home/.config/systemd/user/paperless.service')
   commands={
    'systemctl':'''echo "$*" >> "$TEST_DIR/units"
case "$*" in
  *disable*) rm "$HOME/.config/systemd/user/paperless.service" ;;
esac''',
    'docker':'''case "$*" in
  "ps -aq --filter label=com.docker.compose.project=documentos-ediloco") printf 'doc-running\\ndoc-stopped\\n' ;;
  "ps -aq --filter label=com.docker.compose.project=immich-ediloco") printf 'photo-running\\n' ;;
  "update --restart=no doc-running doc-stopped"|"update --restart=no photo-running") echo "$*" >> "$TEST_DIR/updates" ;;
  *) exit 97 ;;
esac'''}
   for name,code in commands.items():
    p=root/name;p.write_text('#!/bin/sh\n'+code+'\n');p.chmod(0o755)
   r=subprocess.run(['bash',str(REPO/'scripts/configure-ediloco-on-demand.sh')],
      env={**os.environ,'HOME':str(root),'PATH':str(root)+':'+os.environ['PATH'],'TEST_DIR':str(root)},capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
   self.assertTrue(unit.is_symlink())
   self.assertEqual(unit.resolve(),REPO/'home/.config/systemd/user/paperless.service')
   self.assertEqual((root/'units').read_text().splitlines(),
                    ['--user disable paperless.service immich.service documentos-indexacion.service','--user daemon-reload'])
   self.assertEqual((root/'updates').read_text().splitlines(),
                    ['update --restart=no doc-running doc-stopped','update --restart=no photo-running'])

 def test_index_resume_preserves_containers_and_normal_start_applies_config(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);log=root/'docker-args'
   for name,code in {'findmnt':'echo 1c5b930d-5d2f-4b13-9577-661c73bc1993',
                     'docker':'printf "%s\\n" "$@" > "$DOCKER_TEST_LOG"'}.items():
    p=root/name;p.write_text('#!/bin/sh\n'+code+'\n');p.chmod(0o755)
   env={**os.environ,'PATH':str(root)+':'+os.environ['PATH'],'DOCKER_TEST_LOG':str(log)}
   script=str(REPO/'services/paperless/iniciar.sh')
   for args,expected in [([],['compose','up','-d']),(['--no-recreate'],['compose','up','-d','--no-recreate'])]:
    r=subprocess.run(['bash',script,*args],env=env,capture_output=True,text=True)
    self.assertEqual(r.returncode,0,r.stderr)
    self.assertEqual(log.read_text().splitlines(),expected)
   log.unlink()
   (root/'findmnt').write_text('#!/bin/sh\necho wrong-disk\n')
   r=subprocess.run(['bash',script,'--no-recreate'],env=env,capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0)
   self.assertFalse(log.exists())

 def test_restore_preserves_private_data_and_backs_up_code(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);repo=root/'repo';home=root/'home'
   for service in ['paperless','immich']:
    source=repo/'services'/service;source.mkdir(parents=True)
    (source/'iniciar.sh').write_text('#!/bin/sh\nexit 0\n');(source/'iniciar.sh').chmod(0o755)
    # Even ignored local files in a source directory must not replace secrets.
    (source/'.env').write_text('WRONG_SOURCE_CREDENTIALS')
    (source/'ACCESO.txt').write_text('wrong source password')
   runtime=home/'Projects/documentos-ediloco';(runtime/'state').mkdir(parents=True)
   (runtime/'.env').write_text('PRIVATE_EXISTING_CONFIGURATION\n')
   (runtime/'ACCESO.txt').write_text('private credentials')
   (runtime/'state/progreso.json').write_text('private progress')
   (runtime/'iniciar.sh').write_text('old startup code')
   with patch.object(module.subprocess,'run',return_value=subprocess.CompletedProcess([],1,stdout='')):
    module.install(home,repo)
    module.install(home,repo)
   self.assertEqual((runtime/'.env').read_text(),'PRIVATE_EXISTING_CONFIGURATION\n')
   self.assertEqual((runtime/'ACCESO.txt').read_text(),'private credentials')
   self.assertEqual((runtime/'state/progreso.json').read_text(),'private progress')
   self.assertTrue(os.access(runtime/'iniciar.sh',os.X_OK))
   backups=list((home/'.local/state/nixos-config/backups').glob('*/documentos-ediloco/iniciar.sh'))
   self.assertEqual(len(backups),1)
   self.assertEqual(backups[0].read_text(),'old startup code')
   self.assertEqual((home/'Projects/immich-ediloco/.env').stat().st_mode&0o777,0o600)

 def test_launcher_accepts_login_redirect_without_restarting_service(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);log=root/'opened'
   commands={'curl':'printf 302',
             'systemctl':'exit 93',
             'notify-send':'exit 94'}
   r=self.launcher(root,commands=commands)
   self.assertEqual(r.returncode,0,r.stderr)
   self.assertEqual(log.read_text(),'http://localhost:8010')

if __name__=='__main__':unittest.main()
