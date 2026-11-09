export { ContextMemoryBadge } from './components/ContextMemoryBadge';
export { ContextModal } from './components/ContextModal';
export { DiagramPreview } from './components/DiagramPreview';
export { MemoriaPanel, EVENTO_MEMORIA_ACTUALIZADA } from './components/MemoriaPanel';
export { useContextoPersistente } from './hooks/useContextoPersistente';
export { useVersionesContexto, EVENTO_VERSIONES_ACTUALIZADAS } from './hooks/useVersionesContexto';
export { compararVersiones, restaurarVersion } from './utils/versionDiff';
export { useRegistroCambiosManuales } from './hooks/useRegistroCambiosManuales';
export { pausarRegistroManual, marcarOrigenProximosCambios, EVENTO_CAMBIO_LOCAL } from './utils/registroCambios';
/** Pide al panel del chat que abra el historial en una versión concreta. */
export const EVENTO_ABRIR_HISTORIAL = 'contexto_ia_abrir_historial';
export * from './types';
export * from './services/contextoService';

