import { API_URL } from '@/shared/lib/api';
import { TokenService } from '@/shared/lib/TokenService';
import type { SugerenciaIA } from '../types/chatTypes';

interface ErrorDetectado {
  id: string;
  tipo: string;
  severidad: 'alta' | 'media' | 'baja' | string;
  tabla: string;
  columna?: string | null;
  descripcion: string;
  solucion_sugerida: string;
}

/** Textos cortos para el chat (el detector devuelve descripciones técnicas largas). */
const TITULO: Record<string, (e: ErrorDetectado) => string> = {
  sin_pk: e => `${e.tabla} no tiene clave primaria`,
  fk_huerfana: e => `${e.tabla}.${e.columna} apunta a una clase que no existe`,
  tipo_discordante: e => `${e.tabla}.${e.columna} no tiene el mismo tipo que la clave a la que apunta`,
  relacion_nm_directa: e => `${e.tabla} tiene una relación muchos a muchos sin clase intermedia`,
  dependencia_circular: e => `${e.tabla} tiene una dependencia circular`,
  tabla_aislada: e => `${e.tabla} no está conectada con ninguna otra clase`,
  palabra_reservada: e => `${e.columna ? `${e.tabla}.${e.columna}` : e.tabla} usa una palabra reservada de SQL`,
};

/**
 * Revisa el diagrama con el detector del backend (no usa la IA, no gasta crédito).
 * Devuelve null si no se pudo revisar (p. ej. sin sesión): nunca redirige al login,
 * porque se usa en segundo plano.
 */
export async function detectarProblemas(nodes: any[], relations: any[]): Promise<SugerenciaIA[] | null> {
  const token = TokenService.getToken();
  if (!token || !nodes?.length) return token ? [] : null;
  try {
    const res = await fetch(`${API_URL}/api/interoperabilidad/detectar-errores`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ nodes, relations }),
    });
    if (!res.ok) return null;
    const data: { errores?: ErrorDetectado[] } = await res.json();
    const orden: Record<string, number> = { alta: 0, media: 1, baja: 2 };
    return (data.errores || [])
      .sort((a, b) => (orden[a.severidad] ?? 3) - (orden[b.severidad] ?? 3))
      .map(e => ({
        clave: `${e.tipo}:${e.tabla}:${e.columna ?? ''}`.toLowerCase(),
        severidad: e.severidad,
        texto: (TITULO[e.tipo]?.(e) ?? e.descripcion).slice(0, 160),
        detalle: e.solucion_sugerida,
        pedido: `corrige el diagrama: ${e.solucion_sugerida}`,
      }));
  } catch {
    return null;
  }
}
