/**
 * Comandos del chat que NO llaman a la IA (no gastan crédito):
 *   /resumen [hoy|ayer|semana|N dias|AAAA-MM-DD..AAAA-MM-DD]  (CU34)
 *   /documentar                                              (CU35)
 */

export interface VersionResumida {
  ts: number;
  intent: string;
  cmd: string;
  delta: string;
  autor?: string | null;
  estado_propuesta?: string | null;
}

export interface Periodo {
  desde: number;   // Unix, segundos
  hasta: number;
  etiqueta: string;
}

const inicioDelDia = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime() / 1000;

/** "hoy" (por defecto), "ayer", "semana", "3 dias", "2026-11-01..2026-11-08" */
export function parsePeriodo(texto: string, ahora: Date = new Date()): Periodo {
  const t = (texto || '').trim().toLowerCase();
  const hoy = inicioDelDia(ahora);
  const fin = ahora.getTime() / 1000;
  const rango = t.match(/^(\d{4}-\d{2}-\d{2})\s*(?:\.\.|a|-|hasta)\s*(\d{4}-\d{2}-\d{2})$/);
  if (rango) {
    const d1 = new Date(`${rango[1]}T00:00:00`).getTime() / 1000;
    const d2 = new Date(`${rango[2]}T23:59:59`).getTime() / 1000;
    if (!isNaN(d1) && !isNaN(d2)) return { desde: d1, hasta: d2, etiqueta: `del ${rango[1]} al ${rango[2]}` };
  }
  const dias = t.match(/^(\d{1,3})\s*d[ií]as?$/);
  if (dias) {
    const n = Math.max(1, parseInt(dias[1], 10));
    return { desde: hoy - (n - 1) * 86400, hasta: fin, etiqueta: `de los últimos ${n} días` };
  }
  if (t === 'ayer') return { desde: hoy - 86400, hasta: hoy - 1, etiqueta: 'de ayer' };
  if (t === 'semana' || t === 'esta semana') return { desde: hoy - 6 * 86400, hasta: fin, etiqueta: 'de los últimos 7 días' };
  return { desde: hoy, hasta: fin, etiqueta: 'de hoy' };
}

const clasesDelDelta = (delta: string) =>
  (delta || '').split('|').flatMap(p => p.trim().slice(1).split(',')).map(s => s.trim()).filter(Boolean);

const top = (m: Map<string, number>, n = 4) =>
  [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, n).map(([k, v]) => `${k} (${v})`).join(', ');

const esManual = (intent: string) => ['MANUAL', 'RESTAURAR'].includes((intent || '').toUpperCase());

/** CU34: resumen del historial en lenguaje natural, armado por código. */
export function resumenHistorial(versiones: VersionResumida[], periodo: Periodo): string {
  const vs = versiones.filter(v => v.ts >= periodo.desde && v.ts <= periodo.hasta).sort((a, b) => a.ts - b.ts);
  if (!vs.length) return `No hubo cambios ${periodo.etiqueta}.`;

  const manuales = vs.filter(v => (v.intent || '').toUpperCase() === 'MANUAL').length;
  const restauraciones = vs.filter(v => (v.intent || '').toUpperCase() === 'RESTAURAR').length;
  const ia = vs.filter(v => !esManual(v.intent));
  const aprobadas = ia.filter(v => v.estado_propuesta === 'aprobada').length;
  const rechazadas = ia.filter(v => v.estado_propuesta === 'rechazada').length;
  const pendientes = ia.filter(v => v.estado_propuesta === 'pendiente').length;

  const porPersona = new Map<string, number>();
  const porClase = new Map<string, number>();
  vs.forEach(v => {
    const quien = v.autor || 'Alguien';
    porPersona.set(quien, (porPersona.get(quien) || 0) + 1);
    clasesDelDelta(v.delta).forEach(c => porClase.set(c, (porClase.get(c) || 0) + 1));
  });

  const hora = (ts: number) => new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const ultimos = vs.slice(-4).reverse().map(v => {
    const quien = v.autor || 'Alguien';
    const que = esManual(v.intent) ? v.cmd : `pidió a la IA: ${v.cmd}`;
    const estado = v.estado_propuesta && !esManual(v.intent) ? ` (${v.estado_propuesta})` : '';
    return `   ${hora(v.ts)} ${quien} — ${que.slice(0, 90)}${estado}`;
  });

  const lineas = [
    `Resumen ${periodo.etiqueta}: ${vs.length} cambio${vs.length > 1 ? 's' : ''}.`,
    `• A mano: ${manuales}${restauraciones ? ` · restauraciones: ${restauraciones}` : ''}`,
    `• Con la IA: ${ia.length}${ia.length ? ` (aprobadas ${aprobadas}, rechazadas ${rechazadas}${pendientes ? `, pendientes ${pendientes}` : ''})` : ''}`,
    `• Por persona: ${top(porPersona, 6)}`,
  ];
  if (porClase.size) lineas.push(`• Clases más tocadas: ${top(porClase)}`);
  lineas.push('• Lo último:', ...ultimos);
  return lineas.join('\n');
}

// ─── CU35: diccionario de datos ─────────────────────────────────────────────

const celda = (s: unknown) => String(s ?? '').replace(/\|/g, '\\|').replace(/\n/g, ' ');

const ETIQUETA_RELACION: Record<string, string> = {
  association: 'Asociación', aggregation: 'Agregación', composition: 'Composición',
  inheritance: 'Herencia', dependency: 'Dependencia', realization: 'Realización',
};

/** Diccionario de datos en Markdown a partir del diagrama actual (sin IA). */
export function diccionarioMarkdown(
  estado: { nodes: any[]; relations: any[] },
  proyecto: string,
  fecha: Date = new Date()
): { markdown: string; clases: number; relaciones: number } {
  const nodes = (estado.nodes || []).filter((n: any) => n?.nombre);
  const nombre = new Map(nodes.map((n: any) => [String(n.id), n.nombre]));
  const md: string[] = [
    `# Diccionario de datos — ${proyecto}`,
    '',
    `Generado el ${fecha.toLocaleString()} · ${nodes.length} clases · ${(estado.relations || []).length} relaciones`,
    '',
    '## Índice',
    ...nodes.map((n: any) => `- [${n.nombre}](#${String(n.nombre).toLowerCase().replace(/[^a-z0-9]+/g, '-')})`),
    '',
  ];
  nodes.forEach((n: any) => {
    md.push(`## ${n.nombre}`, '');
    if (n.type && n.type !== 'class') md.push(`*Tipo:* ${n.type}`, '');
    if (n.responsable) md.push(`*Responsable:* ${n.responsable}`, '');
    const attrs = n.atributos || [];
    if (attrs.length) {
      md.push('| Atributo | Tipo | Clave | Visibilidad |', '|---|---|---|---|');
      attrs.forEach((a: any) => {
        const v = a.visibilidad || '+';
        const clave = v === 'PK' ? 'PK' : v === 'FK' || /_id$/i.test(a.nombre || '') ? 'FK' : '';
        md.push(`| ${celda(a.nombre)} | ${celda(a.tipo)} | ${clave} | ${['PK', 'FK'].includes(v) ? '+' : celda(v)} |`);
      });
    } else {
      md.push('_Sin atributos._');
    }
    const mets = n.metodos || [];
    if (mets.length) {
      md.push('', '**Métodos**', '');
      mets.forEach((m: any) => md.push(`- \`${m.visibilidad || '+'} ${m.nombre}(${m.parametros || ''}): ${m.retorno || 'void'}\``));
    }
    const rels = (estado.relations || []).filter((r: any) => String(r.sourceId) === String(n.id) || String(r.targetId) === String(n.id));
    if (rels.length) {
      md.push('', '**Relaciones**', '');
      rels.forEach((r: any) => {
        const otro = String(r.sourceId) === String(n.id) ? nombre.get(String(r.targetId)) : nombre.get(String(r.sourceId));
        const card = [r.sourceLabel, r.label].filter(Boolean).join(' → ');
        md.push(`- ${ETIQUETA_RELACION[r.type] ?? r.type ?? 'Asociación'} con **${otro ?? '?'}**${card ? ` (${card})` : ''}`);
      });
    }
    md.push('');
  });
  if ((estado.relations || []).length) {
    md.push('## Relaciones', '', '| Origen | Destino | Tipo | Cardinalidad |', '|---|---|---|---|');
    estado.relations.forEach((r: any) => {
      md.push(`| ${celda(nombre.get(String(r.sourceId)))} | ${celda(nombre.get(String(r.targetId)))} | ${celda(ETIQUETA_RELACION[r.type] ?? r.type)} | ${celda([r.sourceLabel, r.label].filter(Boolean).join(' → '))} |`);
    });
    md.push('');
  }
  return { markdown: md.join('\n'), clases: nodes.length, relaciones: (estado.relations || []).length };
}

/** Descarga un archivo de texto en el navegador de quien lo pidió. */
export function descargarTexto(nombreArchivo: string, contenido: string, tipo = 'text/markdown;charset=utf-8') {
  const url = URL.createObjectURL(new Blob([contenido], { type: tipo }));
  const a = document.createElement('a');
  a.href = url;
  a.download = nombreArchivo;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
