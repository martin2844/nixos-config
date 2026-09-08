import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const escape = value => String(value).replace(/[&<>"']/g, c => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;',
}[c]));
const number = value => typeof value === 'number' && Number.isFinite(value);

function windowLabel(minutes, fallback) {
  if (!number(minutes) || minutes <= 0) return fallback;
  if (minutes === 10080) return 'Semana';
  if (minutes % 1440 === 0) return `${minutes / 1440} días`;
  if (minutes % 60 === 0) return `${minutes / 60} h`;
  return `${minutes} min`;
}

function windows(bucket, now) {
  return ['primary', 'secondary'].flatMap((key, index) => {
    const w = bucket?.[key];
    if (!w || !number(w.usedPercent)) return [];
    const remaining = Math.max(0, Math.min(100, 100 - w.usedPercent));
    const reset = number(w.resetsAt) ? new Date(w.resetsAt * 1000) : null;
    const validReset = reset && Number.isFinite(reset.getTime());
    const expired = validReset && reset.getTime() <= now;
    let detail = `${windowLabel(w.windowDurationMins, index ? 'Secundario' : 'Principal')}: ${remaining.toFixed(0)} % restante`;
    if (validReset) detail += ` · renueva ${reset.toLocaleString('es-ES', {
      day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
    })}`;
    if (expired) detail += ' (pendiente de actualizar)';
    return [{ remaining, detail, expired }];
  });
}

export function unavailable(message = 'No se pudo consultar el uso. Se reintentará en dos minutos.') {
  return { text: 'Codex —', class: 'unavailable', tooltip: escape(message) };
}

function resetCredits(result) {
  const resets = result?.rateLimitResetCredits;
  // The service may omit or cap the details; their length is not the count.
  const count = resets?.availableCount;
  const known = Number.isSafeInteger(count) && count >= 0;
  const suffix = ` · ↻ ${known ? count : '—'}`;
  const lines = [known ? `Resets disponibles: ${count}` : 'Resets disponibles: sin datos'];
  if (known && count > 0 && Array.isArray(resets.credits)) {
    for (const credit of resets.credits) {
      if (credit?.status !== 'available') continue;
      const expiry = number(credit.expiresAt) ? new Date(credit.expiresAt * 1000) : null;
      const date = expiry && Number.isFinite(expiry.getTime()) ? expiry.toLocaleString('es-ES', {
        day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
      }) : null;
      lines.push(`${credit.title || 'Reset'}${date ? ` · caduca ${date}` : ''}`);
    }
  }
  return { suffix, lines };
}

export function formatUsage(result, now = Date.now()) {
  // Never substitute another model's allowance for the main Codex bucket.
  const buckets = result?.rateLimitsByLimitId;
  const legacy = result?.rateLimits;
  const bucket = buckets?.codex ?? ((!legacy?.limitId || legacy.limitId === 'codex') ? legacy : null);
  const main = windows(bucket, now);
  const resets = resetCredits(result);
  if (!main.length) {
    const output = unavailable(['Codex no devuelve un porcentaje para esta cuenta. Comprueba el inicio de sesión de Codex CLI.', '', ...resets.lines].join('\n'));
    output.text += resets.suffix;
    return output;
  }
  const remaining = Math.min(...main.map(w => w.remaining));
  const expired = main.some(w => w.expired);
  const lines = ['Codex · uso restante', ...main.map(w => w.detail)];
  if (bucket.planType) lines.push(`Plan: ${bucket.planType}`);
  lines.push('', ...resets.lines);
  for (const [id, other] of Object.entries(buckets ?? {})) {
    if (id === 'codex') continue;
    const details = windows(other, now);
    if (details.length) lines.push('', other.limitName || id, ...details.map(w => w.detail));
  }
  lines.push('', 'Actualización cada 2 min · clic para abrir ChatGPT');
  if (expired) return { text: `Codex —${resets.suffix}`, class: 'unavailable', tooltip: escape(lines.join('\n')) };
  return {
    text: `Codex ${remaining.toFixed(0)}%${resets.suffix}`,
    percentage: Math.floor(remaining),
    class: remaining <= 10 ? 'critical' : remaining <= 25 ? 'warning' : 'normal',
    tooltip: escape(lines.join('\n')),
  };
}

export function readUsage({
  executable = process.env.CODEX_USAGE_BIN || join(homedir(), '.local/bin/codex'),
  timeoutMs = 15000,
} = {}) {
  return new Promise((resolveResult, reject) => {
    const child = spawn(executable, ['app-server', '--stdio'], {
      cwd: homedir(), stdio: ['pipe', 'pipe', 'ignore'],
    });
    const reader = createInterface({ input: child.stdout });
    let done = false;
    let initialized = false;
    let killTimer;
    const timer = setTimeout(() => finish(new Error('timeout')), timeoutMs);
    function finish(error, result) {
      if (done) return;
      done = true;
      clearTimeout(timer);
      reader.close();
      child.stdin.end();
      child.kill('SIGTERM');
      if (child.exitCode === null && child.signalCode === null) {
        killTimer = setTimeout(() => child.kill('SIGKILL'), 1000);
        killTimer.unref();
      }
      if (error) reject(error); else resolveResult(result);
    }
    const send = value => child.stdin.write(JSON.stringify(value) + '\n');
    child.on('error', error => finish(error));
    child.stdin.on('error', error => finish(error));
    child.on('exit', () => {
      clearTimeout(killTimer);
      finish(new Error('app-server exited'));
    });
    reader.on('line', line => {
      if (done) return;
      let message;
      try { message = JSON.parse(line); } catch { return; }
      if (!message || typeof message !== 'object') return;
      if (message.id === 1 && !initialized) {
        if (message.error) return finish(new Error('initialization failed'));
        initialized = true;
        send({ method: 'initialized' });
        send({ id: 2, method: 'account/rateLimits/read' });
      } else if (message.id === 2 && initialized) {
        if (message.error) return finish(new Error('rate-limit request failed'));
        finish(null, message.result);
      }
    });
    send({ id: 1, method: 'initialize', params: {
      clientInfo: { name: 'waybar_codex_usage', title: 'Waybar Codex Usage', version: '1.0' },
    } });
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  // Keep credentials, server errors and raw account payloads out of bar logs.
  let output;
  try { output = formatUsage(await readUsage()); }
  catch { output = unavailable(); }
  console.log(JSON.stringify(output));
}
