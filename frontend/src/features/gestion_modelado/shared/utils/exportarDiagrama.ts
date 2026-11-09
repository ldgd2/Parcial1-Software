/**
 * CU41: exportar el diagrama a SVG, PNG o PDF en el navegador (sin librerías).
 * Dibuja las clases como en el lienzo (cabecera de color, atributos, métodos) y las relaciones
 * con su tipo (herencia, composición, agregación, dependencia) y cardinalidades.
 */

type Tema = 'oscuro' | 'claro';

const COLORES: Record<Tema, Record<string, string>> = {
  oscuro: { fondo: '#1a1e24', nodo: '#222831', borde: '#393E46', texto: '#ffffff', texto2: '#DFD0B8', linea: '#948979', titulo: '#DFD0B8' },
  claro: { fondo: '#ffffff', nodo: '#ffffff', borde: '#9aa0a6', texto: '#1f2328', texto2: '#3c4043', linea: '#5f6368', titulo: '#1f2328' },
};

const ANCHO = 220;
const CABECERA = 34;
const FILA = 17;
const SECCION = 12;
const MARGEN = 40;
const ALTO_TITULO = 34;

const esc = (s: unknown) =>
  String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const firmaAtributo = (a: any) => `${a?.visibilidad ?? '+'} ${a?.nombre ?? ''}: ${a?.tipo ?? ''}`;
const firmaMetodo = (m: any) => `${m?.visibilidad ?? '+'} ${m?.nombre ?? ''}(${m?.parametros ?? ''}): ${m?.retorno ?? 'void'}`;
const recortar = (s: string, max = 30) => (s.length > max ? `${s.slice(0, max - 1)}…` : s);

function altoNodo(n: any) {
  const atr = (n.atributos || []).length;
  const met = (n.metodos || []).length;
  return CABECERA + SECCION + Math.max(atr, 1) * FILA + (met ? SECCION + met * FILA : 0) + 8;
}

function borde(cx: number, cy: number, w: number, h: number, hacia: { x: number; y: number }) {
  const dx = hacia.x - cx, dy = hacia.y - cy;
  if (!dx && !dy) return { x: cx, y: cy };
  const k = Math.min(Math.abs(w / 2 / (dx || 1e-9)), Math.abs(h / 2 / (dy || 1e-9)));
  return { x: cx + dx * k, y: cy + dy * k };
}

/** SVG completo del diagrama. */
export function diagramaASvg(
  estado: { nodes: any[]; relations: any[] },
  opciones: { tema?: Tema; titulo?: string } = {}
): { svg: string; ancho: number; alto: number } {
  const c = COLORES[opciones.tema ?? 'oscuro'];
  const nodos = (estado.nodes || []).map((n: any) => ({
    n, x: Number(n.x) || 0, y: Number(n.y) || 0, w: Number(n.width) || ANCHO, h: altoNodo(n),
  }));
  const extraTitulo = opciones.titulo ? ALTO_TITULO : 0;
  if (!nodos.length) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="160" viewBox="0 0 480 160"><rect width="100%" height="100%" fill="${c.fondo}"/><text x="240" y="85" text-anchor="middle" font-family="Inter, Segoe UI, sans-serif" font-size="14" fill="${c.texto2}">Diagrama vacío</text></svg>`;
    return { svg, ancho: 480, alto: 160 };
  }
  const minX = Math.min(...nodos.map(b => b.x)) - MARGEN;
  const minY = Math.min(...nodos.map(b => b.y)) - MARGEN - extraTitulo;
  const ancho = Math.max(...nodos.map(b => b.x + b.w)) + MARGEN - minX;
  const alto = Math.max(...nodos.map(b => b.y + b.h)) + MARGEN - minY;
  const porId = new Map(nodos.map(b => [String(b.n.id), b]));
  const X = (v: number) => v - minX;
  const Y = (v: number) => v - minY;

  const partes: string[] = [];
  partes.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${ancho}" height="${alto}" viewBox="0 0 ${ancho} ${alto}" font-family="Inter, 'Segoe UI', Roboto, sans-serif">`);
  partes.push(`<defs>
    <marker id="herencia" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="12" markerHeight="12" orient="auto"><path d="M1,1 L11,6 L1,11 Z" fill="${c.fondo}" stroke="${c.linea}" stroke-width="1.3"/></marker>
    <marker id="flecha" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="10" markerHeight="10" orient="auto"><path d="M1,1 L11,6 L1,11" fill="none" stroke="${c.linea}" stroke-width="1.3"/></marker>
    <marker id="rombo-lleno" viewBox="0 0 16 10" refX="1" refY="5" markerWidth="16" markerHeight="10" orient="auto"><path d="M1,5 L8,1 L15,5 L8,9 Z" fill="${c.linea}"/></marker>
    <marker id="rombo-hueco" viewBox="0 0 16 10" refX="1" refY="5" markerWidth="16" markerHeight="10" orient="auto"><path d="M1,5 L8,1 L15,5 L8,9 Z" fill="${c.fondo}" stroke="${c.linea}" stroke-width="1.3"/></marker>
  </defs>`);
  partes.push(`<rect width="100%" height="100%" fill="${c.fondo}"/>`);
  if (opciones.titulo) {
    partes.push(`<text x="${MARGEN}" y="${MARGEN - 6}" font-size="16" font-weight="700" fill="${c.titulo}">${esc(opciones.titulo)}</text>`);
  }

  // Relaciones (debajo de las clases)
  (estado.relations || []).forEach((r: any) => {
    const a = porId.get(String(r.sourceId)), b = porId.get(String(r.targetId));
    if (!a || !b) return;
    const ca = { x: X(a.x) + a.w / 2, y: Y(a.y) + a.h / 2 };
    const cb = { x: X(b.x) + b.w / 2, y: Y(b.y) + b.h / 2 };
    const p1 = borde(ca.x, ca.y, a.w, a.h, cb);
    const p2 = borde(cb.x, cb.y, b.w, b.h, ca);
    const tipo = r.type || 'association';
    const fin = tipo === 'inheritance' || tipo === 'realization' ? ' marker-end="url(#herencia)"' : ['dependency', 'directed', 'instantiate'].includes(tipo) ? ' marker-end="url(#flecha)"' : '';
    const ini = tipo === 'composition' ? ' marker-start="url(#rombo-lleno)"' : tipo === 'aggregation' ? ' marker-start="url(#rombo-hueco)"' : '';
    const punteada = tipo === 'dependency' || tipo === 'realization' ? ' stroke-dasharray="6 4"' : '';
    partes.push(`<line x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}" stroke="${c.linea}" stroke-width="1.5"${punteada}${ini}${fin}/>`);
    const etiqueta = (p: { x: number; y: number }, hacia: { x: number; y: number }, txt?: string) => {
      if (!txt) return;
      const dx = hacia.x - p.x, dy = hacia.y - p.y, l = Math.hypot(dx, dy) || 1;
      partes.push(`<text x="${p.x + (dx / l) * 18 + (dy / l) * 8}" y="${p.y + (dy / l) * 18 - (dx / l) * 8}" font-size="10" fill="${c.texto2}" text-anchor="middle">${esc(txt)}</text>`);
    };
    etiqueta(p1, p2, r.sourceLabel);
    etiqueta(p2, p1, r.targetLabel);
    if (r.label) {
      partes.push(`<text x="${(p1.x + p2.x) / 2}" y="${(p1.y + p2.y) / 2 - 6}" font-size="10" font-style="italic" fill="${c.texto2}" text-anchor="middle">${esc(r.label)}</text>`);
    }
  });

  // Clases
  nodos.forEach(({ n, x, y, w, h }) => {
    const nx = X(x), ny = Y(y);
    partes.push(`<g>`);
    partes.push(`<rect x="${nx}" y="${ny}" width="${w}" height="${h}" rx="4" fill="${c.nodo}" stroke="${c.borde}"/>`);
    partes.push(`<path d="M${nx + 4},${ny} h${w - 8} a4,4 0 0 1 4,4 v${CABECERA - 4} h${-w} v${-(CABECERA - 4)} a4,4 0 0 1 4,-4 z" fill="${esc(n.color || '#393E46')}"/>`);
    if (n.type && n.type !== 'class') {
      partes.push(`<text x="${nx + w / 2}" y="${ny + 12}" font-size="9" fill="#ffffff" fill-opacity="0.8" text-anchor="middle">«${esc(n.type)}»</text>`);
    }
    partes.push(`<text x="${nx + w / 2}" y="${ny + (n.type && n.type !== 'class' ? 27 : 22)}" font-size="13" font-weight="700" fill="#ffffff" text-anchor="middle">${esc(recortar(n.nombre || '', 26))}</text>`);
    let yy = ny + CABECERA;
    partes.push(`<line x1="${nx}" y1="${yy}" x2="${nx + w}" y2="${yy}" stroke="${c.borde}"/>`);
    const atrs = n.atributos || [];
    if (!atrs.length) {
      partes.push(`<text x="${nx + 10}" y="${yy + SECCION / 2 + 12}" font-size="11" font-style="italic" fill="${c.texto2}" fill-opacity="0.6">sin atributos</text>`);
    }
    atrs.forEach((a: any, i: number) => {
      partes.push(`<text x="${nx + 10}" y="${yy + SECCION / 2 + 12 + i * FILA}" font-size="11" font-family="Consolas, 'Courier New', monospace" fill="${c.texto2}">${esc(recortar(firmaAtributo(a), Math.floor(w / 7)))}</text>`);
    });
    const mets = n.metodos || [];
    if (mets.length) {
      yy += SECCION + Math.max(atrs.length, 1) * FILA;
      partes.push(`<line x1="${nx}" y1="${yy}" x2="${nx + w}" y2="${yy}" stroke="${c.borde}"/>`);
      mets.forEach((m: any, i: number) => {
        partes.push(`<text x="${nx + 10}" y="${yy + SECCION / 2 + 12 + i * FILA}" font-size="11" font-family="Consolas, 'Courier New', monospace" fill="${c.texto2}">${esc(recortar(firmaMetodo(m), Math.floor(w / 7)))}</text>`);
      });
    }
    partes.push(`</g>`);
  });
  partes.push(`</svg>`);
  return { svg: partes.join('\n'), ancho, alto };
}

const nombreArchivo = (base: string, ext: string) =>
  `${(base || 'diagrama').toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'diagrama'}.${ext}`;

function descargarBlob(blob: Blob, nombre: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

export function exportarSvg(estado: { nodes: any[]; relations: any[] }, nombre: string, tema: Tema = 'oscuro') {
  const { svg } = diagramaASvg(estado, { tema, titulo: nombre });
  descargarBlob(new Blob([svg], { type: 'image/svg+xml;charset=utf-8' }), nombreArchivo(nombre, 'svg'));
}

/** PNG a doble resolución (nítido en pantallas y documentos). */
export function exportarPng(estado: { nodes: any[]; relations: any[] }, nombre: string, tema: Tema = 'oscuro'): Promise<void> {
  const { svg, ancho, alto } = diagramaASvg(estado, { tema, titulo: nombre });
  const escala = Math.min(2, 16000 / Math.max(ancho, alto));   // límite de tamaño de los canvas
  return new Promise((resolver, rechazar) => {
    const img = new Image();
    const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml;charset=utf-8' }));
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = Math.ceil(ancho * escala);
      canvas.height = Math.ceil(alto * escala);
      const ctx = canvas.getContext('2d');
      if (!ctx) { URL.revokeObjectURL(url); rechazar(new Error('Sin canvas')); return; }
      ctx.scale(escala, escala);
      ctx.drawImage(img, 0, 0);
      URL.revokeObjectURL(url);
      canvas.toBlob(b => {
        if (!b) { rechazar(new Error('No se pudo generar el PNG')); return; }
        descargarBlob(b, nombreArchivo(nombre, 'png'));
        resolver();
      }, 'image/png');
    };
    img.onerror = () => { URL.revokeObjectURL(url); rechazar(new Error('No se pudo dibujar el diagrama')); };
    img.src = url;
  });
}

/** PDF con el diálogo de impresión del navegador ("Guardar como PDF"), fondo claro. */
export function exportarPdf(estado: { nodes: any[]; relations: any[] }, nombre: string): boolean {
  const { svg, ancho, alto } = diagramaASvg(estado, { tema: 'claro', titulo: nombre });
  const ventana = window.open('', '_blank');
  if (!ventana) return false;   // ventanas emergentes bloqueadas
  const horizontal = ancho >= alto;
  ventana.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${esc(nombre)}</title>
<style>@page { size: A4 ${horizontal ? 'landscape' : 'portrait'}; margin: 10mm; }
html,body{margin:0;background:#fff} svg{width:100%;height:auto;max-height:100vh;display:block}</style></head>
<body>${svg}<script>window.onload=function(){setTimeout(function(){window.print();},150)};</script></body></html>`);
  ventana.document.close();
  return true;
}
