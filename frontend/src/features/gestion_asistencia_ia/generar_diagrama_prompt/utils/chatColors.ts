/**
 * Paleta de colores distintivos tipo WhatsApp para participantes en el chat grupal.
 * Asignación determinística por ID o nombre del usuario.
 */
const WHATSAPP_PALETTE = [
  '#25D366', // Verde WhatsApp
  '#34B7F1', // Celeste
  '#E542A3', // Fucsia
  '#FFA000', // Ámbar
  '#7C4DFF', // Púrpura
  '#00BFA5', // Turquesa
  '#FF5252', // Coral
  '#64DD17', // Lima
  '#FF6D00', // Naranja
  '#00E5FF', // Cian
  '#D500F9', // Magenta
  '#26A69A', // Verde Azulado
  '#AB47BC', // Lavanda
];

export function getUserColor(userIdOrName: string): string {
  if (!userIdOrName) return WHATSAPP_PALETTE[0];
  
  const lower = userIdOrName.toLowerCase();
  if (lower.includes('diag') || lower.includes('ia') || lower.includes('asistente')) {
    return '#25D366'; // Color distintivo para el bot de IA
  }

  let hash = 0;
  for (let i = 0; i < userIdOrName.length; i++) {
    hash = userIdOrName.charCodeAt(i) + ((hash << 5) - hash);
  }

  const index = Math.abs(hash) % WHATSAPP_PALETTE.length;
  return WHATSAPP_PALETTE[index];
}

