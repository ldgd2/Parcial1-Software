/** CU37: "~5 h · media" para mostrar la estimación de una tarea (vacío si no tiene). */
export function etiquetaEsfuerzo(t: { estimacion_horas?: number | null; complejidad?: string | null }): string {
  const partes: string[] = [];
  if (t.estimacion_horas) partes.push(`~${t.estimacion_horas} h`);
  if (t.complejidad) partes.push(t.complejidad);
  return partes.join(' · ');
}

/** Total de horas estimadas de una lista de tareas. */
export const horasTotales = (ts: Array<{ estimacion_horas?: number | null }>) =>
  ts.reduce((acc, t) => acc + (t.estimacion_horas || 0), 0);
