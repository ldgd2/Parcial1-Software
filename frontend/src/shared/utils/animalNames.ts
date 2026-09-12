const ADJECTIVES = [
  "Anónimo", "Enojado", "Feliz", "Veloz", "Misterioso", "Dormilón", "Triste", "Ruidoso", "Mágico",
  "Saltarín", "Curioso", "Sabio", "Bailarín", "Loco", "Hambriento", "Valiente", "Perezoso", "Invisible"
];

const ANIMALS = [
  "Zorro", "Canguro", "Mapache", "Pato", "Tigre", "Panda", "Koala", "Pingüino", "Mono",
  "Elefante", "León", "Lobo", "Oso", "Gato", "Perro", "Conejo", "Delfín", "Tiburón", "Caballo"
];

export function getRandomNickname(): string {
  const adj = ADJECTIVES[Math.floor(Math.random() * ADJECTIVES.length)];
  const animal = ANIMALS[Math.floor(Math.random() * ANIMALS.length)];
  return `${animal} ${adj}`;
}

export function getGuestId(): string {
  let guestId = localStorage.getItem("guestId");
  if (!guestId) {
    guestId = "guest_" + Math.random().toString(36).substring(2, 11);
    localStorage.setItem("guestId", guestId);
  }
  return guestId;
}

export function getGuestNickname(): string {
  let nickname = localStorage.getItem("guestNickname");
  if (!nickname) {
    nickname = getRandomNickname();
    localStorage.setItem("guestNickname", nickname);
  }
  return nickname;
}

export function setGuestNickname(nickname: string) {
  localStorage.setItem("guestNickname", nickname);
}
