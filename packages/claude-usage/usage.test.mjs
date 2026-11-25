import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { formatUsage, readCredentials, readUsage, SessionExpired } from './usage.mjs';

const reset = '2033-05-18T03:33:20Z';
const limit = (kind, percent, scope = null) => ({ kind, percent, resets_at: reset, scope });

test('bar shows the most constrained general limit; model limits stay in the tooltip', () => {
  const result = formatUsage({ limits: [
    limit('session', 80), limit('weekly_all', 10),
    limit('weekly_scoped', 99, { model: { display_name: '<Opus & co>' } }),
  ] }, 0, 'max');
  assert.equal(result.text, 'Claude 20%');
  assert.equal(result.class, 'warning');
  assert.match(result.tooltip, /Sesión \(5 h\): 20 % restante/);
  assert.match(result.tooltip, /Semana · &lt;Opus &amp; co&gt;: 1 % restante/);
  assert.match(result.tooltip, /Plan: max/);
});

test('legacy five_hour/seven_day fields still work', () => {
  const result = formatUsage({ five_hour: { utilization: 5, resets_at: reset },
    seven_day: { utilization: 95, resets_at: reset }, seven_day_opus: { utilization: 0 } }, 0);
  assert.equal(result.text, 'Claude 5%');
  assert.equal(result.class, 'critical');
  assert.match(result.tooltip, /Semana · Opus: 100 % restante/);
});

test('invalid or absent data never implies 100%', () => {
  for (const data of [null, {}, { limits: [] }, { limits: [limit('session', '9')] },
    { limits: [limit('weekly_scoped', 0, { model: { display_name: 'Opus' } })] }, { five_hour: null }]) {
    assert.equal(formatUsage(data, 0).text, 'Claude —');
  }
});

test('a passed reset timestamp is unknown until fresh data arrives', () => {
  const result = formatUsage({ limits: [limit('session', 10)] }, Date.parse(reset) + 1000);
  assert.equal(result.text, 'Claude —');
  assert.match(result.tooltip, /pendiente de actualizar/);
});

test('extra usage is reported when enabled', () => {
  const result = formatUsage({ limits: [limit('session', 0)],
    extra_usage: { is_enabled: true, utilization: 42, spend_limit_reached: false } }, 0);
  assert.match(result.tooltip, /Uso extra: 42 %/);
});

test('credentials: expired or missing tokens are a session error, never refreshed', async t => {
  const dir = await mkdtemp(join(tmpdir(), 'claude-usage-test-'));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const file = join(dir, '.credentials.json');
  await writeFile(file, JSON.stringify({ claudeAiOauth: { accessToken: 'tok', expiresAt: 1000, subscriptionType: 'pro' } }));
  assert.deepEqual(await readCredentials({ file, now: 0 }), { token: 'tok', plan: 'pro' });
  await assert.rejects(readCredentials({ file, now: 2000 }), SessionExpired);
  await writeFile(file, JSON.stringify({}));
  await assert.rejects(readCredentials({ file, now: 0 }), SessionExpired);
});

test('HTTP client sends the OAuth headers and maps 401 to a session error', async t => {
  let seen;
  const server = createServer((req, res) => {
    seen = req.headers;
    if (req.headers.authorization !== 'Bearer good') { res.writeHead(401); return res.end(); }
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ limits: [limit('session', 1)] }));
  });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  t.after(() => server.close());
  const url = `http://127.0.0.1:${server.address().port}/`;
  const data = await readUsage({ token: 'good', url });
  assert.equal(data.limits[0].percent, 1);
  assert.equal(seen['anthropic-beta'], 'oauth-2025-04-20');
  await assert.rejects(readUsage({ token: 'bad', url }), SessionExpired);
});
