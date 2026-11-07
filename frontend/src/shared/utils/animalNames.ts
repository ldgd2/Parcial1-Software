/**
 * Utilidades para obtener el nombre real del usuario o colaborador en la sala.
 * Se eliminaron los nombres aleatorios de animales para usar la identidad real del usuario.
 */

export function getGuestId(): string {
  let guestId = localStorage.getItem("guestId");
  if (!guestId) {
    guestId = "guest_" + Math.random().toString(36).substring(2, 9);
    localStorage.setItem("guestId", guestId);
  }
  return guestId;
}

export function getGuestNickname(): string {
  // Limpiar cualquier nombre residual de animal
  const existing = localStorage.getItem("guestNickname");
  const isAnimal = existing && (
    existing.includes("Zorro") || existing.includes("Canguro") || existing.includes("Mapache") ||
    existing.includes("Pato") || existing.includes("Tigre") || existing.includes("Panda") ||
    existing.includes("Koala") || existing.includes("Pingüino") || existing.includes("Mono") ||
    existing.includes("Elefante") || existing.includes("León") || existing.includes("Lobo") ||
    existing.includes("Oso") || existing.includes("Gato") || existing.includes("Perro") ||
    existing.includes("Conejo") || existing.includes("Delfín") || existing.includes("Tiburón") ||
    existing.includes("Caballo")
  );

  if (isAnimal) {
    localStorage.removeItem("guestNickname");
  }

  // Priorizar el nombre de usuario registrado si existe en sesión
  const storedName = localStorage.getItem("usuario_nombre");
  if (storedName && storedName.trim()) {
    return storedName.trim();
  }

  const userStr = localStorage.getItem("user");
  if (userStr) {
    try {
      const parsed = JSON.parse(userStr);
      if (parsed?.nombre) return parsed.nombre.trim();
    } catch {}
  }

  const cleanGuest = localStorage.getItem("guestNickname");
  if (cleanGuest && cleanGuest.trim()) {
    return cleanGuest.trim();
  }

  const defaultName = "Colaborador";
  localStorage.setItem("guestNickname", defaultName);
  return defaultName;
}

export function setGuestNickname(nickname: string): void {
  if (nickname && nickname.trim()) {
    const trimmed = nickname.trim();
    localStorage.setItem("guestNickname", trimmed);
    localStorage.setItem("usuario_nombre", trimmed);
  }
}
