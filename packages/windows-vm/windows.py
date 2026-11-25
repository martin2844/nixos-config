#!/usr/bin/env python3
"""Open Windows; shut down its VM after the desktop closes."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

CONFIG = Path('/home/martin/.config/windows-vm')
STATE = Path('/home/martin/.local/state/windows-vm')
FREERDP = '/run/current-system/sw/bin/xfreerdp'
os.environ['PATH'] = '/run/current-system/sw/bin:' + os.environ.get('PATH', '')

def notify(message):
    subprocess.run(['notify-send', 'Windows', message], check=False)

def credentials():
    return dict(line.split('=', 1) for line in (CONFIG / 'credentials.env').read_text().splitlines() if '=' in line)

def rdp_args(auth_only=False):
    creds = credentials()
    args = ['/v:127.0.0.1:3389', '/u:' + creds['USERNAME'], '/p:' + creds['PASSWORD'], '/cert:tofu', '/log-level:ERROR']
    if auth_only:
        return args + ['+auth-only']
    return args + ['/t:Windows', '/wm-class:windows-vm', '/size:1600x900', '+dynamic-resolution', '+clipboard', '/network:lan', '/sound:sys:pulse']

def rdp(auth_only=False):
    # Credentials travel through a private pipe, never process arguments.
    return subprocess.run([FREERDP, '/args-from:stdin'], input='\n'.join(rdp_args(auth_only))+'\n', text=True,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          timeout=20 if auth_only else None).returncode

def focus():
    try:
        clients = json.loads(subprocess.check_output(['hyprctl', '-j', 'clients'], text=True))
        for client in clients:
            if client.get('class') == 'windows-vm':
                selector = json.dumps('address:' + client['address'])
                result = subprocess.run(['hyprctl', 'dispatch',
                                         'hl.dsp.focus({ window = ' + selector + ' })'],
                                        capture_output=True, text=True, check=True)
                return result.stdout.strip() == 'ok'
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return False

def active(unit):
    result = subprocess.run(['systemctl', '--user', 'show', '--property=ActiveState', '--value', unit],
                            capture_output=True, text=True, check=True)
    return result.stdout.strip() in {'active', 'activating', 'reloading'}

def cancel_shutdown():
    subprocess.run(['systemctl', '--user', 'stop', 'windows-idle-shutdown.timer',
                    'windows-idle-shutdown.service'], check=True)
    return 0

def schedule_shutdown():
    if active('windows.service'):
        subprocess.run(['systemctl', '--user', 'restart', 'windows-idle-shutdown.timer'], check=True)
        notify('Windows se apagará en 30 segundos. Abrila de nuevo para cancelar.')
    return 0

def idle_shutdown():
    # A new desktop session may have started just as the timer expired.
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / 'launcher.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        if active('windows-desktop.service') or not active('windows.service'):
            return 0
        notify('Apagando Windows y liberando los recursos de la VM…')
        subprocess.run(['systemctl', '--user', 'stop', 'windows.service'], check=True)
    return 0

def open_desktop():
    cancel_shutdown()
    if focus():
        return 0
    if active('windows-desktop.service'):
        notify('Windows se está abriendo. Esperá un momento.')
        return 0
    subprocess.run(['systemctl', '--user', 'start', 'windows-desktop.service'], check=True)
    return 0

def session():
    if focus():
        return 0
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / 'launcher.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            notify('Windows se está abriendo. Esperá un momento.')
            return 0
        check = subprocess.run([str(CONFIG / 'check-storage')], capture_output=True, text=True)
        if check.returncode:
            notify('No se encuentra el disco Windows montado y disponible para escritura.')
            return 1
        subprocess.run(['systemctl', '--user', 'start', 'windows.service'], check=True)
        notify('Iniciando el escritorio de Windows…')
        deadline = time.monotonic() + 900
        while time.monotonic() < deadline:
            try:
                if rdp(auth_only=True) == 0:
                    result = rdp()
                    if result:
                        notify('La conexión se cerró. Volvé a abrir Windows para reconectar.')
                    return result
            except subprocess.TimeoutExpired:
                pass
            state = subprocess.run(['systemctl', '--user', 'is-active', '--quiet', 'windows.service'])
            if state.returncode:
                notify('La VM se detuvo. Revisá: journalctl --user -u windows.service')
                return 1
            time.sleep(5)
        notify('Windows todavía no responde por escritorio remoto. Consultá http://127.0.0.1:8006')
        return 1

if __name__ == '__main__':
    try:
        actions = {'--session': session, '--cancel-shutdown': cancel_shutdown,
                   '--schedule-shutdown': schedule_shutdown, '--idle-shutdown': idle_shutdown}
        if len(sys.argv) == 1:
            sys.exit(open_desktop())
        if len(sys.argv) != 2 or sys.argv[1] not in actions:
            raise SystemExit('Uso: windows')
        sys.exit(actions[sys.argv[1]]())
    except (OSError, subprocess.SubprocessError) as error:
        notify('No se pudo abrir Windows. Revisá el estado de Docker y de windows.service.')
        sys.exit(1)
