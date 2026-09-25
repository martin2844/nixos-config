// Deliberately conservative primary categories. A mention is not a document type.
export const CLASSIFICATION_VERSION = 1;
export const CATEGORIES = [
  ['Documentos', '#2f80ed'], ['Planos', '#219653'],
  ['Documentos Bancarios', '#1565c0'], ['Migraciones', '#9b51e0'],
  ['Facturas y recibos', '#f2994a'], ['Impuestos', '#b7791f'],
  ['Vivienda', '#27ae60'], ['Seguros', '#00838f'], ['Salud', '#eb5757'],
  ['Vehículos', '#455a64'], ['Estudios', '#673ab7'], ['Trabajo', '#795548'],
  ['Libros y manuales', '#607d8b'], ['Notas', '#78909c'], ['Por clasificar', '#828282'],
].map(([name, color]) => ({name, color}));
export const LEGACY_TAGS = ['Casa', 'DNI', 'Pasaporte', 'Empadronamiento',
  'Identidad y tramites', 'Identidad y trámites', 'TheMartin',
  'Documentos por clasificar', 'Finanzas y pagos', 'Notas y textos',
  'Otros documentos', 'Trabajo y CV', 'Vehiculos'];
export const MANAGED_TAGS = new Set([...LEGACY_TAGS, ...CATEGORIES.map(c => c.name)]);
const normalize = text => String(text ?? '').normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().replace(/[_\s]+/g, ' ');

export function classifyDocument(document, source = '') {
  const location = normalize(source);
  const filename = normalize(document.original_file_name || source.split('/').at(-1) || document.title);
  const content = normalize(document.content);
  // Type indicators belong in the header, not in an arbitrary paragraph of a book.
  const header = content.slice(0, 1800);
  const start = content.slice(0, 500);
  const result = (category, reason) => ({category, reason, version: CLASSIFICATION_VERSION});
  if (/\.(dwg|dxf|dwt)(\.txt)?$/i.test(filename) || /\.(dwg|dxf|dwt)$/i.test(source) || /^plano cad:/.test(start)) return result('Planos', 'Archivo CAD');

  const note = /\.(md|txt)(\.(txt|pdf))?$/i.test(filename) || /\/notas y textos\//.test(location);
  // Notes about passports, banks or visas remain notes; actual signed agreements do not.
  if (note && !/^(#\s*)?(acuerdo de|contrato de)/.test(start)) return result('Notas', 'Nota o texto personal');

  const academic = /\/(estudios|publicidad)\//.test(location) || /\b(parcial|cuestionario|actividad practica|trabajo practico|apuntes|written assignment|assignment week)\b/.test(filename) || /\b(university of the people|instructor|department of computer science)\b/.test(start);
  const technical = /\b(especificaciones? tecnicas?|pliego|norma tecnica|procedimiento especifico)\b/.test(start);
  const architectural = /\b(facultad|arquitectura|planos|fichas tecnicas)\b/.test(location);
  const shortDrawing = (document.page_count ?? 1) <= 6 && !technical;
  const drawingName = /\b(planta|corte|fachada|lamina|azotea|terraza|detalle|replanteo|plano|planos)\b/.test(filename);
  const drawingHeader = /\b(escala\s*:?\s*1\s*[:/]|plano\s*:|planta baja|planta alta|corte [a-z]\s*[-–]\s*[a-z]|vista [a-z]\b)/.test(header);
  const dimensioned = (header.match(/\b\d{1,2}[.,]\d{2}\b/g) ?? []).length >= 8;
  if (shortDrawing && ((architectural && (drawingName || (dimensioned && /\b(vista|eje|columna|muro|planta|corte)\b/.test(header)))) || drawingHeader || /\/(replanteo|planos|[^/]* - planos[^/]*)\//.test(location))) return result('Planos', 'Lámina o plano PDF/imagen');
  if (academic) return result('Estudios', 'Material académico o certificado de estudios');
  if (/\.(csv|xlsx?)$/.test(filename) && /\b(sku|inventario|products export)\b/.test(start)) return result('Trabajo', 'Inventario o catálogo de productos');

  // Receipts and bank statements are distinct even when both mention account numbers.
  if (/\b(resumen de (cuenta|tarjeta)|extracto (bancario|de cuenta)|bank statement|account statement|transfer confirmation|comprobante de transferencia|direct deposit authorization|certificado de titularidad|certificacion de titularidad)\b/.test(start + ' ' + filename) ||
      (/\b(citibank|santander|bbva|galicia|american express|visa classic)\b/.test(start) && /\b(account|statement|saldo anterior|saldo actual|pago minimo|limite de compra)\b/.test(header)) ||
      /\/(citi statement|inversiones)\//.test(location)) return result('Documentos Bancarios', 'Extracto, cuenta, inversión o transferencia');
  if (/\b(factura|invoice|recibo|comprobante de pago|comprobante de compra)\b/.test(filename) || /\b(factura|invoice|comprobante de pago|tu pago fue confirmado|transferencia recibida)\b/.test(start) || /\/finanzas y pagos\/(comprobantes|payment receits|elm docs)\//.test(location)) return result('Facturas y recibos', 'Factura o comprobante de un pago');

  if (/\b(contrato de suministro|contrato de (alquiler|arrendamiento)|cambio de titular del contrato)\b/.test(header)) return result('Vivienda', 'Contrato de vivienda o suministro');
  if (/\b(nonimmigrant visa|immigrant visa|diversity visa|ds[- ]?160|registro central.de extranjeros|certificado de registro de ciudadano|solicitud de (residencia|nacionalidad)|autorizacion de residencia|empadronamiento|padron municipal|processo de nacionalidade|naturalizacao)\b/.test(header + ' ' + filename) ||
      (content.length > 100 && /\/(ciudadania portugal|ciudadania espana)\//.test(location) && !/\bfotos?\b/.test(filename))) return result('Migraciones', 'Residencia, ciudadanía, visado o padrón');
  if (/\b(pasaporte|passport|passaporte)\b/.test(filename) || /\/pasaportes\//.test(location) ||
      /\/(dni y nie|documentos civiles|actas y certificados|documentos personales|licencia de conducir)\//.test(location) ||
      /^(dni|nie|cuil|cuit)([ .-]|\d)/.test(filename) ||
      (/\b(republica (argentina|portuguesa)|reino de espana|ministerio del interior)\b/.test(start) && /\b(surname|given names|nacionalidad|fecha de nacimiento)\b/.test(header) && (document.page_count ?? 1) <= 2) ||
      /\b(constancia de cuil|acta de nacimiento|partida de nacimiento|acta de matrimonio|certidao de nascimento)\b/.test(start)) return result('Documentos', 'Identificación o certificado personal');
  if (/\b(declaracion (de la renta|jurada de impuestos)|certificado de retenciones|form w-?8|form w-?9|modelo (100|130|303)|monotributo|tax return)\b/.test(header + ' ' + filename)) return result('Impuestos', 'Declaración o certificado fiscal');
  if (/\/vivienda\//.test(location) || /\b(contrato de (alquiler|arrendamiento)|escritura (publica|de compraventa)|compraventa (de|del) inmueble|contrato de locacion)\b/.test(header + ' ' + filename)) return result('Vivienda', 'Escritura, alquiler o documentación de vivienda');
  if (/\b(poliza|certificado.allianz|insurance certificate|worldcup care|condiciones particulares.{0,30}seguro)\b/.test(start + ' ' + filename) && !technical && !/\b(personal afectado|datos de la obra)\b/.test(start)) return result('Seguros', 'Póliza o certificado de cobertura');
  if (/\/salud\//.test(location) || /\b(historia clinica|informe medico|receta medica|resultados? de laboratorio|contratoyreglamentomedife|seguro de salud|examen neurologico)\b/.test(start + ' ' + filename)) return result('Salud', 'Documento médico o de cobertura sanitaria');
  if (/\/vehiculos\//.test(location) || /\b(certificado de legalidad|licencias nacionales de conducir|verificacion tecnica vehicular|situacion: infraccion|infraccion nro|certificado-patente)\b/.test(header + ' ' + filename)) return result('Vehículos', 'Trámite de vehículo, conducción o multa');

  if (/\b(curriculum|resume|curriculums|cv)\b/.test(filename) || /\bcurriculums\//.test(location) || /^(#\s*)?(acuerdo de|contrato de|propuesta de desarrollo|employment agreement|offer letter)/.test(start)) return result('Trabajo', 'CV, propuesta o contrato de trabajo/servicios');
  if (/\b(diploma|titulo universitario|certificado analitico|certificado de alumno)\b/.test(filename + ' ' + start)) return result('Estudios', 'Material académico o certificado de estudios');
  if (/\b(manual|handbook|catalogo|guia de usuario|isbn)\b/.test(filename + ' ' + start) || /\/libros y manuales\//.test(location)) return result('Libros y manuales', 'Libro, catálogo o manual');
  if (/\/trabajo y cv\/arquitectura\//.test(location) || technical) return result('Trabajo', 'Documentación técnica de trabajo');
  return result('Por clasificar', content.trim() ? 'Sin indicios suficientes del tipo de documento' : 'Sin texto legible ni nombre concluyente');
}

export async function ensureCategories(api, all, json) {
  const tags = await all('/api/tags/?page_size=100');
  for (const spec of CATEGORIES) {
    const existing = tags.find(t => t.name === spec.name);
    if (!existing) tags.push(await api('/api/tags/', json('POST', {...spec, matching_algorithm: 0})));
    else if (existing.matching_algorithm !== 0) Object.assign(existing, await api(`/api/tags/${existing.id}/`, json('PATCH', {matching_algorithm: 0, match: ''})));
  }
  return tags;
}

export function desiredTags(document, tags, category) {
  const managedIds = new Set(tags.filter(t => MANAGED_TAGS.has(t.name)).map(t => t.id));
  const selected = tags.find(t => t.name === category);
  if (!selected) throw Error(`Categoría no configurada: ${category}`);
  return [...new Set([...document.tags.filter(id => !managedIds.has(id)), selected.id])].sort((a,b) => a-b);
}
