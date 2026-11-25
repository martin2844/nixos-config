import { readFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const escape = value => String(value).replace(/[&<>"']/g, c => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;',
}[c]));
const number = value => typeof value === 'number' && Number.isFinite(value);
const refreshSeconds = 60;
const endpoint = 'https://api.anthropic.com/api/oauth/usage';
const dateFormat = { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' };

const labels = { session: 'Sesión (5 h)', weekly_all: 'Semana · todos los modelos', weekly_scoped: 'Semana' };

function parseDate(value) {
  if (typeof value !== 'string') return null;
  const date = new Date(value);
  return Number.isFinite(date.getTime()) ? date : null;
}

function describe({ label, used, resetsAt }, now) {
  const remaining = Math.max(0, Math.min(100, 100 - used));
  const reset = parseDate(resetsAt);
  const expired = Boolean(reset && reset.getTime() <= now);
  let detail = `${label}: ${remaining.toFixed(0)} % restante`;
  if (reset) detail += ` · renueva ${reset.toLocaleString('es-ES', dateFormat)}`;
  if (expired) detail += ' (pendiente de actualizar)';
  return { remaining, detail, expired };
}

// Prefer the structured `limits` list; fall back to the older five_hour/seven_day fields.
function limits(result) {
  if (Array.isArray(result?.limits)) {
    return result.limits.flatMap(limit => {
      if (!limit || !number(limit.percent)) return [];
      const model = limit.scope?.model?.display_name || limit.scope?.model?.id;
      const surface = limit.scope?.surface;
      const scope = [model, surface].filter(s => typeof s === 'string' && s).join(' · ');
      const label = scope ? `${labels[limit.kind] ?? limit.kind} · ${scope}` : (labels[limit.kind] ?? limit.kind);
      return [{ label, used: limit.percent, resetsAt: limit.resets_at, scoped: Boolean(limit.scope) }];
    });
  }
  return [['five_hour', labels.session, false], ['seven_day', labels.weekly_all, false],
    ['seven_day_opus', 'Semana · Opus', true], ['seven_day_sonnet', 'Semana · Sonnet', true]].flatMap(([key, label, scoped]) => {
    const w = result?.[key];
    if (!w || !number(w.utilization)) return [];
    return [{ label, used: w.utilization, resetsAt: w.resets_at, scoped }];
  });
}

function extraUsage(result) {
  const extra = result?.extra_usage;
  if (!extra?.is_enabled) return [];
  const line = number(extra.utilization) ? `Uso extra: ${extra.utilization.toFixed(0)} % del límite mensual` : 'Uso extra: activado';
  return ['', extra.spend_limit_reached ? `${line} (límite alcanzado)` : line];
}

export function unavailable(message = `No se pudo consultar el uso. Se reintentará en ${refreshSeconds} s. Clic derecho para actualizar.`) {
  return { text: 'Claude —', class: 'unavailable', tooltip: escape(message) };
}

export function formatUsage(result, now = Date.now(), plan = null) {
  const all = limits(result).map(l => ({ ...l, ...describe(l, now) }));
  // General limits (session, weekly) drive the bar; model-scoped ones only appear in the tooltip.
  const main = all.filter(l => !l.scoped);
  if (!main.length) {
    return unavailable('Claude no devuelve un porcentaje para esta cuenta. Comprueba el inicio de sesión de Claude Code.');
  }
  const remaining = Math.min(...main.map(l => l.remaining));
  const expired = main.some(l => l.expired);
  const lines = ['Claude · uso restante', ...main.map(l => l.detail)];
  const scoped = all.filter(l => l.scoped);
  if (scoped.length) lines.push('', ...scoped.map(l => l.detail));
  if (plan) lines.push(`Plan: ${plan}`);
  lines.push(...extraUsage(result));
  lines.push('', `Consultado: ${new Date(now).toLocaleString('es-ES', { ...dateFormat, second: '2-digit' })}`,
    `Actualización cada ${refreshSeconds} s · clic derecho para actualizar`,
    'Clic para abrir el uso en claude.ai');
  const tooltip = escape(lines.join('\n'));
  if (expired) return { text: 'Claude —', class: 'unavailable', tooltip };
  return {
    text: `Claude ${remaining.toFixed(0)}%`,
    percentage: Math.floor(remaining),
    class: remaining <= 10 ? 'critical' : remaining <= 25 ? 'warning' : 'normal',
    tooltip,
  };
}

export class SessionExpired extends Error {}

export async function readCredentials({
  file = join(process.env.CLAUDE_CONFIG_DIR || join(homedir(), '.claude'), '.credentials.json'),
  now = Date.now(),
} = {}) {
  const oauth = JSON.parse(await readFile(file, 'utf8'))?.claudeAiOauth;
  if (typeof oauth?.accessToken !== 'string' || !oauth.accessToken) throw new SessionExpired();
  // Never refresh here: rotating the refresh token would sign Claude Code out.
  if (number(oauth.expiresAt) && oauth.expiresAt <= now) throw new SessionExpired();
  return { token: oauth.accessToken, plan: typeof oauth.subscriptionType === 'string' ? oauth.subscriptionType : null };
}

export async function readUsage({ token, url = process.env.CLAUDE_USAGE_URL || endpoint, timeoutMs = 15000 }) {
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      'anthropic-beta': 'oauth-2025-04-20',
      'User-Agent': 'waybar-claude-usage/1.0',
    },
    signal: AbortSignal.timeout(timeoutMs),
  });
  if (response.status === 401) throw new SessionExpired();
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  // Keep tokens, server errors and raw account payloads out of bar logs.
  let output;
  try {
    const { token, plan } = await readCredentials();
    output = formatUsage(await readUsage({ token }), Date.now(), plan);
  } catch (error) {
    output = error instanceof SessionExpired
      ? unavailable('La sesión de Claude Code expiró o no existe. Abrí `claude` (o `claude /login`) para renovarla.')
      : unavailable();
  }
  console.log(JSON.stringify(output));
}
