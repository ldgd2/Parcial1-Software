export function parseUmlAttribute(rawAttr: string) {
  if (!rawAttr) {
    return { id: crypto.randomUUID(), visibilidad: '-' as const, nombre: 'attr', tipo: 'String', version: 0 };
  }
  
  let s = rawAttr.trim();
  let visibilidad: '-' | '+' | '#' | 'PK' | 'FK' = '-';
  
  if (/^PK\b/i.test(s)) {
    visibilidad = 'PK';
    s = s.replace(/^PK\b/i, '').trim();
  } else if (/^FK\b/i.test(s)) {
    visibilidad = 'FK';
    s = s.replace(/^FK\b/i, '').trim();
  } else {
    const matchVis = s.match(/^([\-\+\#\~\s]+)/);
    if (matchVis) {
      const visChars = matchVis[1].trim();
      if (visChars.includes('+')) visibilidad = '+';
      else if (visChars.includes('#')) visibilidad = '#';
      else if (visChars.includes('~')) visibilidad = '#';
      else visibilidad = '-';
      s = s.replace(/^([\-\+\#\~\s]+)/, '').trim();
    }
  }

  let nombre = s;
  let tipo = 'String';

  if (s.includes(':')) {
    const parts = s.split(':');
    nombre = parts[0].trim();
    tipo = parts.slice(1).join(':').trim() || 'String';
  }

  nombre = nombre.replace(/[^a-zA-Z0-9_]/g, '');
  if (!nombre) nombre = 'attr';

  return {
    id: crypto.randomUUID(),
    visibilidad,
    nombre,
    tipo,
    version: 0
  };
}

export function parseUmlMethod(rawMet: string) {
  if (!rawMet) {
    return { id: crypto.randomUUID(), visibilidad: '+' as const, nombre: 'method', parametros: '', retorno: 'void', version: 0 };
  }
  
  let s = rawMet.trim();
  let visibilidad: '+' | '-' | '#' = '+';

  const matchVis = s.match(/^([\-\+\#\~\s]+)/);
  if (matchVis) {
    const visChars = matchVis[1].trim();
    if (visChars.includes('-')) visibilidad = '-';
    else if (visChars.includes('#')) visibilidad = '#';
    else visibilidad = '+';
    s = s.replace(/^([\-\+\#\~\s]+)/, '').trim();
  }

  let nombre = s;
  let parametros = '';
  let retorno = 'void';

  const parenMatch = s.match(/^([a-zA-Z0-9_]+)\s*\((.*?)\)(?:\s*:\s*(.*))?$/);
  if (parenMatch) {
    nombre = parenMatch[1].trim();
    parametros = parenMatch[2].trim();
    retorno = parenMatch[3] ? parenMatch[3].trim() : 'void';
  } else if (s.includes(':')) {
    const parts = s.split(':');
    nombre = parts[0].replace(/[^a-zA-Z0-9_]/g, '').trim();
    retorno = parts[1].trim() || 'void';
  } else {
    nombre = s.replace(/[^a-zA-Z0-9_]/g, '').trim();
  }

  if (!nombre) nombre = 'method';

  return {
    id: crypto.randomUUID(),
    visibilidad,
    nombre,
    parametros,
    retorno,
    version: 0
  };
}
