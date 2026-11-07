export function parseUmlAttribute(rawAttr: any) {
  if (!rawAttr) {
    return { id: crypto.randomUUID(), visibilidad: '-' as const, nombre: 'attr', tipo: 'String', version: 0 };
  }

  // Si ya es un objeto (ej. { nombre, tipo, visibilidad } o { name, type, visibility })
  if (typeof rawAttr === 'object') {
    let rawName = String(rawAttr.nombre || rawAttr.name || rawAttr.id || 'attr').trim();
    let tipo = String(rawAttr.tipo || rawAttr.type || 'String').trim();
    let visibilidad: '-' | '+' | '#' | 'PK' | 'FK' = '-';
    const rawVis = String(rawAttr.visibilidad || rawAttr.visibility || '').trim();

    // Extraer visibilidad si viene embebida en rawName (ej: "- id: Int" o "+ nombre: string")
    const visMatch = rawName.match(/^([\-\+\#\~]|PK|FK)\s*/i);
    if (visMatch) {
      const v = visMatch[1].toUpperCase();
      if (v === 'PK' || v === 'FK') visibilidad = v;
      else if (visMatch[1] === '+') visibilidad = '+';
      else if (visMatch[1] === '#') visibilidad = '#';
      else visibilidad = '-';
      rawName = rawName.replace(/^([\-\+\#\~]|PK|FK)\s*/i, '').trim();
    } else if (rawVis) {
      if (['+', '-', '#', 'PK', 'FK'].includes(rawVis)) {
        visibilidad = rawVis as any;
      } else if (rawVis.includes('+')) {
        visibilidad = '+';
      } else if (rawVis.includes('#')) {
        visibilidad = '#';
      }
    }

    // Si rawName contiene ":" (ej: "id: Int" o "id: Int : String"), extraer nombre y tipo
    if (rawName.includes(':')) {
      const parts = rawName.split(':');
      rawName = parts[0].trim();
      const extractedType = parts.slice(1).join(':').trim();
      if (extractedType && (!tipo || tipo.toLowerCase() === 'string')) {
        tipo = extractedType;
      }
    }

    // Limpiar tipo si contiene ":" duplicado
    if (tipo.includes(':')) {
      tipo = tipo.split(':').pop()?.trim() || tipo;
    }

    const cleanName = rawName.replace(/[^a-zA-Z0-9_]/g, '') || 'attr';

    return {
      id: rawAttr.id || crypto.randomUUID(),
      visibilidad,
      nombre: cleanName,
      tipo: tipo || 'String',
      version: typeof rawAttr.version === 'number' ? rawAttr.version : 0
    };
  }
  
  let s = String(rawAttr).trim();
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

  if (tipo.includes(':')) {
    tipo = tipo.split(':').pop()?.trim() || tipo;
  }

  nombre = nombre.replace(/[^a-zA-Z0-9_]/g, '');
  if (!nombre) nombre = 'attr';

  return {
    id: crypto.randomUUID(),
    visibilidad,
    nombre,
    tipo: tipo || 'String',
    version: 0
  };
}

export function parseUmlMethod(rawMet: any) {
  if (!rawMet) {
    return { id: crypto.randomUUID(), visibilidad: '+' as const, nombre: 'method', parametros: '', retorno: 'void', version: 0 };
  }

  // Si ya es un objeto (ej. { nombre, parametros, retorno, visibilidad } o { name, params, returnType, visibility })
  if (typeof rawMet === 'object') {
    let rawName = String(rawMet.nombre || rawMet.name || 'method').trim();
    let visibilidad: '+' | '-' | '#' = '+';
    const rawVis = String(rawMet.visibilidad || rawMet.visibility || '').trim();

    // Extraer visibilidad de rawName si viene embebida
    const visMatch = rawName.match(/^([\-\+\#\~])\s*/);
    if (visMatch) {
      if (visMatch[1] === '-') visibilidad = '-';
      else if (visMatch[1] === '#') visibilidad = '#';
      else visibilidad = '+';
      rawName = rawName.replace(/^([\-\+\#\~])\s*/, '').trim();
    } else if (rawVis) {
      if (['+', '-', '#'].includes(rawVis)) {
        visibilidad = rawVis as any;
      } else if (rawVis.includes('-')) {
        visibilidad = '-';
      } else if (rawVis.includes('#')) {
        visibilidad = '#';
      }
    }

    let parametros = '';
    const rawParams = rawMet.parametros ?? rawMet.params ?? rawMet.parameters;
    if (Array.isArray(rawParams)) {
      parametros = rawParams
        .map((p: any) => typeof p === 'object' ? `${p.nombre || p.name}: ${p.tipo || p.type}` : String(p))
        .join(', ');
    } else if (rawParams) {
      parametros = String(rawParams).trim();
    }

    let retorno = String(rawMet.retorno || rawMet.returnType || rawMet.return_type || 'void').trim();

    // Si rawName viene en formato "enrollInCourse(course: Course): void"
    const parenMatch = rawName.match(/^([a-zA-Z0-9_]+)\s*\((.*?)\)(?:\s*:\s*(.*))?$/);
    if (parenMatch) {
      rawName = parenMatch[1].trim();
      if (!parametros) parametros = parenMatch[2].trim();
      if (parenMatch[3]) retorno = parenMatch[3].trim();
    } else if (rawName.includes(':')) {
      const parts = rawName.split(':');
      rawName = parts[0].trim();
      if (parts[1]) retorno = parts[1].trim();
    }

    const cleanName = rawName.replace(/[^a-zA-Z0-9_]/g, '') || 'method';

    return {
      id: rawMet.id || crypto.randomUUID(),
      visibilidad,
      nombre: cleanName,
      parametros,
      retorno: retorno || 'void',
      version: typeof rawMet.version === 'number' ? rawMet.version : 0
    };
  }
  
  let s = String(rawMet).trim();
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
