import test from 'node:test';
import assert from 'node:assert/strict';
import {classifyDocument, desiredTags} from '../services/paperless/clasificacion.mjs';

const root = '/run/media/martin/Ediloco/Archivo-TheMartin/09_Documentos/';
const cases = [
  ['DNI fotografiado sin OCR', 'Identidad_y_tramites/DNI_y_NIE/foto.jpg', '', null, 'Documentos'],
  ['pasaporte completo', 'Identidad_y_tramites/Pasaportes/Persona/pasaporte.pdf', 'Visa / visas', 19, 'Documentos'],
  ['escritura menciona DNI', 'Vivienda/Documentos_de_la_casa/hoja2.jpg', 'Comparece con Documento Nacional de Identidad ante escribano', 1, 'Vivienda'],
  ['contrato menciona pasaporte', 'Otros_documentos/Descargas/acuerdo.pdf', 'ACUERDO DE SERVICIOS DE DERIVACIÓN DIGITAL Entre las partes DNI/Pasaporte', 5, 'Trabajo'],
  ['extracto con nombre aleatorio', 'Otros_documentos/Descargas/ab312.pdf', 'Resumen de cuenta Vencimiento Actual Tarjeta Titular DNI', 5, 'Documentos Bancarios'],
  ['transferencia', 'Finanzas_y_pagos/Payment receits/agosto.pdf', 'Transfer confirmation Transfer created Funded', 3, 'Documentos Bancarios'],
  ['factura menciona NIE e IBAN', 'Otros_documentos/Descargas/factura.pdf', 'FACTURA Servicios prestados NIE IBAN', 1, 'Facturas y recibos'],
  ['visa estaba en Trabajo', 'Trabajo_y_CV/Archivo_personal/confirmation.pdf', 'U.S. Department of State Electronic Diversity Visa Program Confirmation', 1, 'Migraciones'],
  ['Visa bancaria no es migración', 'Otros_documentos/Descargas/tarjeta.pdf', 'VISA CLASSIC PAGINA: 1 Sucursal Saldo anterior Pago minimo', 1, 'Documentos Bancarios'],
  ['CAD estaba en Estudios', 'Estudios/Facultad/planta.dwg', '', null, 'Planos'],
  ['derivado CAD sin geometría', 'Trabajo_y_CV/Arquitectura/file.dwg', 'Plano CAD: file.dwg', null, 'Planos'],
  ['PDF plano con rótulo', 'Trabajo_y_CV/Arquitectura/terraza.pdf', 'Obra: Quincho Plano: Vista B Fecha: 01/01/2020 Escala: 1:25', 1, 'Planos'],
  ['manual de arquitectura no es plano', 'Estudios/Facultad/manual.pdf', 'Introducción a la arquitectura. Casa vivienda planta planos.', 80, 'Estudios'],
  ['especificación técnica no es plano', 'Trabajo_y_CV/Arquitectura/especificacion.pdf', 'ESPECIFICACIONES TECNICAS GENERALES Sección 07500 Membranas Impermeables. Los planos indican los cortes.', 7, 'Trabajo'],
  ['clase de programación menciona cuentas', 'Otros_documentos/Descargas/Written Assignment.docx', 'Department of Computer Science University of the People Bank statement example for transaction locking', 2, 'Estudios'],
  ['CSV de comercio no es libro', 'Otros_documentos/Descargas/productos.csv', 'SKU,Nombre,Visibilidad en el catálogo,Inventario', null, 'Trabajo'],
  ['nota de emigración no es un trámite', 'Notas_y_textos/MyVault/emigrar.md.txt', '# DNI pasaporte Cómo emigrar y buscar vivienda', null, 'Notas'],
  ['foto de perfil no es trámite por su carpeta', 'Identidad_y_tramites/Barcelona/profile.jpg', '', null, 'Por clasificar'],
  ['contrato de agua guardado con padrón', 'Identidad_y_tramites/Empadronamiento/agua.pdf', 'CAMBIO DE TITULAR DEL CONTRATO DE SUMINISTRO DE AGUA', 4, 'Vivienda'],
  ['desconocido queda pendiente', 'Otros_documentos/Descargas/scan.jpg', '', null, 'Por clasificar'],
];
for (const [name, source, content, page_count, expected] of cases) test(name, () => {
  const document = {original_file_name: source.split('/').at(-1), content, page_count};
  assert.equal(classifyDocument(document, root + source).category, expected);
});

test('preserves unrelated user labels while replacing mistaken managed labels', () => {
  const tags = [{id: 1, name: 'DNI'}, {id: 2, name: 'Casa'}, {id: 3, name: 'Documentos Bancarios'}, {id: 4, name: 'Mi revisión personal'}];
  const doc = {tags: [1, 2, 4]};
  assert.deepEqual(desiredTags(doc, tags, 'Documentos Bancarios'), [3, 4]);
  assert.deepEqual(doc.tags, [1, 2, 4]);
  assert.deepEqual(desiredTags({tags: [3, 4]}, tags, 'Documentos Bancarios'), [3, 4]);
});
