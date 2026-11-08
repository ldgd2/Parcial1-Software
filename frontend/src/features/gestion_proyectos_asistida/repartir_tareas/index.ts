export { TareasEquipoPanel } from './components/TareasEquipoPanel';
export { useTareasEquipo } from './hooks/useTareasEquipo';
export {
  tareasService,
  repartirTareasEquipo,
  obtenerMisTareas,
  obtenerTodasLasTareas,
  marcarTarea,
  crearTareaManual,
  eliminarTarea,
} from './services/tareasService';
export type {
  TareaItem,
  RepartirTareasRequest,
  RepartirTareasResponse,
  CrearTareaManualRequest,
} from './types';
