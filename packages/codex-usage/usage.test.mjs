import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { formatUsage, readUsage } from './usage.mjs';

const window = (usedPercent, windowDurationMins = 10080) => ({
  usedPercent, windowDurationMins, resetsAt: 2000000000,
});
const usage = (primary, secondary = null) => ({ rateLimits: { primary, secondary } });

test('weekly-only account displays remaining usage without inventing a 5h limit', () => {
  const result = formatUsage(usage(window(9)), 0);
  assert.equal(result.text, 'Codex 91% · ↻ —');
  assert.match(result.tooltip, /Semana: 91 % restante/);
  assert.doesNotMatch(result.tooltip, /5 h/);
});

test('main quota uses the most constrained window, never the other model bucket', () => {
  const result = formatUsage({ rateLimitsByLimitId: {
    codex: { primary: window(80, 300), secondary: window(9) },
    spark: { limitName: '<Spark & friends>', primary: window(100) },
  } }, 0);
  assert.equal(result.text, 'Codex 20% · ↻ —');
  assert.equal(result.class, 'warning');
  assert.match(result.tooltip, /&lt;Spark &amp; friends&gt;/);
});

test('exhausted quota is critical; invalid or absent data never implies 100%', () => {
  assert.equal(formatUsage(usage(window(100)), 0).class, 'critical');
  for (const data of [null, {}, usage(window(null)), usage(window('9')),
    { rateLimits: { limitId: 'spark', primary: window(0) } }]) {
    assert.equal(formatUsage(data, 0).text, 'Codex — · ↻ —');
  }
});

test('a passed reset timestamp is unknown until the server supplies fresh data', () => {
  const result = formatUsage(usage(window(80)), 2000000001000);
  assert.equal(result.text, 'Codex — · ↻ —');
  assert.match(result.tooltip, /pendiente de actualizar/);
});

async function mockServer(t, body) {
  const directory = await mkdtemp(join(tmpdir(), 'codex-usage-test-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const executable = join(directory, 'codex');
  await writeFile(executable, `#!${process.execPath}\n${body}`, { mode: 0o700 });
  return executable;
}

test('reset count is authoritative even when details are partial', () => {
  const result = formatUsage({ ...usage(window(10)), rateLimitResetCredits: {
    availableCount: 2,
    credits: [{ status: 'available', title: 'Full <reset>', expiresAt: 2000000000 }],
  } }, 0);
  assert.equal(result.text, 'Codex 90% · ↻ 2');
  assert.match(result.tooltip, /Resets disponibles: 2/);
  assert.match(result.tooltip, /Full &lt;reset&gt; · caduca/);
});

test('zero resets and unknown reset counts remain distinct', () => {
  const data = usage(window(10));
  assert.equal(formatUsage({ ...data, rateLimitResetCredits: { availableCount: 0, credits: null } }, 0).text, 'Codex 90% · ↻ 0');
  for (const resets of [null, {}, { availableCount: -1 }, { availableCount: '2' }]) {
    assert.equal(formatUsage({ ...data, rateLimitResetCredits: resets }, 0).text, 'Codex 90% · ↻ —');
  }
});

test('stdio client completes initialization and ignores unrelated notifications', async t => {
  const executable = await mockServer(t, `
const readline = require('node:readline');
let ready = false;
readline.createInterface({input: process.stdin}).on('line', line => {
  const msg = JSON.parse(line);
  if (msg.method === 'initialize') console.log(JSON.stringify({id: 1, result: {}}));
  if (msg.method === 'initialized') ready = true;
  if (msg.method === 'account/rateLimits/read' && ready) {
    console.log('null');
    console.log(JSON.stringify({method: 'unrelated', params: {}}));
    console.log(JSON.stringify({id: 2, result: {rateLimits: {primary: {usedPercent: 9}}}}));
  }
});`);
  const result = await readUsage({ executable, timeoutMs: 2000 });
  assert.equal(formatUsage(result).text, 'Codex 91% · ↻ —');
});

test('hung server times out', async t => {
  const executable = await mockServer(t, 'setInterval(() => {}, 1000);');
  await assert.rejects(readUsage({ executable, timeoutMs: 100 }), /timeout/);
});

test('missing CLI and server errors are handled without exposing raw errors', async t => {
  await assert.rejects(readUsage({ executable: '/nonexistent/codex-usage-test' }));
  const executable = await mockServer(t, `
process.stdin.on('data', () => console.log(JSON.stringify({id: 1, error: {message: 'private data'}})));
`);
  await assert.rejects(readUsage({ executable, timeoutMs: 2000 }), error => {
    assert.equal(error.message, 'initialization failed');
    return true;
  });
});
