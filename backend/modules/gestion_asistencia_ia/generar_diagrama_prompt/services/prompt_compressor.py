import re
import unicodedata
from typing import List, Tuple, Dict, Set


class HybridPromptCompressor:
    """
    Compresor híbrido de prompts basado en raíces morfológicas y operadores universales de parseo:
    Transforma conjugaciones y sustantivos técnicos en anclas estándar (FIX, EDIT, ADD, DEL, LINK, CLS, TBL, etc.)
    conservando la estructura fluida de la oración y eliminando artículos y relleno.
    """

    def __init__(self) -> None:
        # 1. Limpieza de menciones y saludos largos
        self.filler_phrases: List[str] = [
            r"@\w+\b",
            r"\b(hola|buenos dias|buenas tardes|buenas noches)\b",
            r"\b(por favor|necesito que|quiero que|ayudame a|podrias|puedes)\b",
            r"\b(muchas gracias|gracias de antemano)\b"
        ]

        # 2. Mapeo de expresiones compuestas a tokens técnicos directos
        self.compound_map: Dict[str, str] = {
            r"\bbase de datos\b": "DB",
            r"\bllaves? primarias?\b": "PK",
            r"\bllaves? foraneas?\b": "FK",
            r"\bmuchos a muchos\b": "N:M",
            r"\buno a muchos\b": "1:N",
            r"\buno a uno\b": "1:1",
            r"\bsin relacion\w*\b": "ORPHAN",
            r"\bsuelt[ao]s?\b": "ORPHAN"
        }

        # 3. Parseadores de verbos y entidades UML (Raíces morfológicas -> Comando corto)
        self.action_parsers: List[Tuple[str, str]] = [
            # FIX: arreglar, corregir, reparar, solucionar
            (r"^(arregl\w+|corrig\w+|corregir|repar\w+|solucion\w+)$", "FIX"),
            # EDIT: editar, modificar, actualizar, cambiar, renombrar
            (r"^(edit\w+|modific\w+|actualiz\w+|cambi\w+|renombr\w+)$", "EDIT"),
            # ADD: crear, agregar, añadir, hacer, haz, insertar
            (r"^(crea\w*|agreg\w+|anad\w+|hac\w+|haz|insert\w+|nuev[oa]s?)$", "ADD"),
            # DEL: eliminar, borrar, quitar, remover
            (r"^(elimin\w+|borr\w+|quit\w+|remov\w+)$", "DEL"),
            # LINK: conectar, relacionar, unir, vincular, asociar (evitando falsos positivos con universidad o unidad)
            (r"^(conect\w+|relacion\w+|unir\w*|unid\w*|unio\w*|uniend\w*|une\b|unen\b|unan\b|vincul\w+|asoci\w+)$", "LINK"),
            # CHECK: revisar, validar, verificar, detectar, analizar
            (r"^(revis\w+|valid\w+|verific\w+|detect\w+|analiz\w+)$", "CHECK"),
            # Sustantivos estructurales del diagrama
            (r"^diagram\w*$", "DIAG"),
            (r"^clas\w+$", "CLS"),
            (r"^tabl\w+$", "TBL"),
            (r"^atribut\w+$|^camp\w+$|^column\w+$", "ATTR"),
            (r"^relacion\w*$|^conexion\w*$", "REL"),
            (r"^distribucion$|^posicion\w*$", "LAYOUT")
        ]

        # 4. Stopwords ligeras: Solo artículos y demostrativos que no aportan contexto
        self.stopwords: Set[str] = {
            "el", "la", "los", "las", "un", "una", "unos", "unas",
            "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
            "al", "del", "lo", "le", "les", "me", "te", "se", "que"
        }

    def _strip_accents(self, text: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )

    def _parse_token(self, word: str) -> str:
        for pattern, token in self.action_parsers:
            if re.match(pattern, word):
                return token
        return word

    def compress(self, prompt: str) -> str:
        text = self._strip_accents(prompt.lower())

        for pattern in self.filler_phrases:
            text = re.sub(pattern, "", text)

        for pattern, repl in self.compound_map.items():
            text = re.sub(pattern, repl, text)

        # Colapsar signos repetidos ("???" -> "?")
        text = re.sub(r'([¿?¡!.,;:])\1+', r'\1', text)

        # Extraer palabras y signos de puntuación
        raw_tokens = re.findall(r'[a-zA-Z0-9_]+|[.,;?!:]', text)
        result: List[str] = []

        for tok in raw_tokens:
            low = tok.lower()
            if low in self.stopwords:
                continue

            # Si ya fue convertido por compound_map (ej. DB, PK, ORPHAN), respetarlo en mayúsculas
            if tok.isupper() and len(tok) > 1:
                parsed = tok
            else:
                parsed = self._parse_token(low)

            # Evitar tokens idénticos consecutivos (ej. "ADD nuevas CLS" -> "ADD ADD CLS" -> "ADD CLS")
            if result and result[-1] == parsed:
                continue

            result.append(parsed)

        output = " ".join(result)
        output = re.sub(r'\s+([.,;?!:])', r'\1', output)
        return output.strip(" ,.")

