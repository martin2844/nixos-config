import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {connect, json, saveJSON} from './paperless-api.mjs';
import {CLASSIFICATION_VERSION, LEGACY_TAGS, classifyDocument, desiredTags, ensureCategories} from './clasificacion.mjs';

process.chdir(path.dirname(fileURLToPath(import.meta.url)));
const apply = process.argv.includes('--aplicar');
if (process.argv.slice(2).some(a => !['--aplicar', '--plan'].includes(a))) throw Error('Uso: reclasificar.mjs --plan|--aplicar');
await fs.mkdir('state', {recursive: true, mode: 0o700});
const lock = await fs.open('state/clasificacion.lock', 'wx');
try {
  const {api, all, request} = await connect();
  const fields = await all('/api/custom_fields/?page_size=100');
  const sourceId = fields.find(f => f.name === 'Archivo de origen')?.id;
  if (!sourceId) throw Error('No existe el campo Archivo de origen');
  const documents = await all('/api/documents/?page_size=100&ordering=id');
  const originalTags = await all('/api/tags/?page_size=100');
  const views = await all('/api/saved_views/?page_size=100');
  const ui = await api('/api/ui_settings/');
  const timestamp = Date.now();
  // A recoverable metadata backup precedes all mutations. Original files are untouched.
  await saveJSON(`state/etiquetas-antes-${timestamp}.json`, {
    at: new Date().toISOString(), tags: originalTags, views, ui,
    documents: documents.map(d => ({id: d.id, tags: d.tags})),
  });
  const decisions = documents.flatMap(d => {
    const source = d.custom_fields.find(f => f.field === sourceId)?.value;
    // Only the imported archive is managed; manually added documents stay intact.
    return typeof source === 'string' && source.startsWith('/run/media/martin/Ediloco/Archivo-TheMartin/09_Documentos/')
      ? [{id: d.id, ...classifyDocument(d, source)}] : [];
  });
  const counts = {};
  for (const d of decisions) counts[d.category] = (counts[d.category] ?? 0) + 1;
  await saveJSON('state/plan-clasificacion.json', {version: CLASSIFICATION_VERSION, at: new Date().toISOString(), counts, decisions});
  console.log(JSON.stringify({apply, total: decisions.length, counts}));
  if (apply) {
    const tags = await ensureCategories(api, all, json);
    for (const t of tags.filter(t => LEGACY_TAGS.includes(t.name) && t.matching_algorithm !== 0))
      await api(`/api/tags/${t.id}/`, json('PATCH', {matching_algorithm: 0, match: ''}));
    const byId = new Map(documents.map(d => [d.id, d]));
    const groups = new Map();
    for (const decision of decisions) {
      const doc = byId.get(decision.id);
      const desired = desiredTags(doc, tags, decision.category);
      const remove = doc.tags.filter(id => !desired.includes(id));
      const add = desired.filter(id => !doc.tags.includes(id));
      if (!remove.length && !add.length) continue;
      const key = JSON.stringify({add_tags: add, remove_tags: remove});
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(doc.id);
    }
    let changed = 0;
    for (const [key, ids] of groups) for (let i = 0; i < ids.length; i += 100) {
      const batch = ids.slice(i, i + 100);
      await api('/api/documents/bulk_edit/', json('POST', {documents: batch, method: 'modify_tags', parameters: JSON.parse(key)}));
      changed += batch.length;
      console.log(`Etiquetas actualizadas: ${changed}`);
    }
    // Replace the four original shortcuts without deleting anyone's other views.
    const featured = ['Documentos', 'Planos', 'Documentos Bancarios', 'Migraciones'];
    const oldNames = ['DNI', 'Casa', 'Pasaporte', 'Empadronamiento'];
    const icons = ['person', 'building', 'bank', 'globe2'];
    const visible = [];
    for (let i = 0; i < featured.length; i++) {
      const name = featured[i];
      const old = views.find(v => v.name === name) ?? views.find(v => v.name === oldNames[i]);
      const payload = {name, icon: icons[i], sort_field: 'title', sort_reverse: false, display_mode: 'table', display_fields: ['title', 'tag', 'pagecount'], filter_rules: [{rule_type: 6, value: String(tags.find(t => t.name === name).id)}]};
      const view = await api(old ? `/api/saved_views/${old.id}/` : '/api/saved_views/', json(old ? 'PATCH' : 'POST', payload));
      visible.push(view.id);
    }
    const oldIds = new Set(views.filter(v => oldNames.includes(v.name)).map(v => v.id));
    const settings = ui.settings.saved_views ?? {};
    await api('/api/ui_settings/', json('POST', {settings: {...ui.settings, saved_views: {...settings,
      sidebar_views_visible_ids: [...new Set([...visible, ...(settings.sidebar_views_visible_ids ?? []).filter(id => !oldIds.has(id))])],
      dashboard_views_visible_ids: [...new Set([...visible, ...(settings.dashboard_views_visible_ids ?? []).filter(id => !oldIds.has(id))])],
    }}}));
    // Delete only empty legacy labels. Late OCR completions are cleaned on the next run.
    const latestTags = await all('/api/tags/?page_size=100');
    for (const t of latestTags.filter(t => LEGACY_TAGS.includes(t.name) && t.document_count === 0))
      await request(`/api/tags/${t.id}/`, {method: 'DELETE'});
    await saveJSON('state/clasificacion.json', {version: CLASSIFICATION_VERSION, at: new Date().toISOString(), counts, decisions, changed});
    console.log(JSON.stringify({done: true, changed, counts}));
  }
} finally { await lock.close(); await fs.unlink('state/clasificacion.lock'); }
