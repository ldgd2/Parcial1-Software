"""
Trabajos en segundo plano para peticiones largas (IA, exportación).

Detrás de Cloudflare cualquier petición HTTP se corta a los 100 s (error 524, que el navegador
muestra como CORS / "Failed to fetch") aunque el servidor termine bien. El patrón es:
  POST .../iniciar  -> responde al instante {trabajo_id}
  GET  .../estado/{id} -> {estado: en_proceso|ok|error, resultado, error, segundos}
Los trabajos viven en memoria (el backend corre con un solo worker de uvicorn).
"""
import asyncio
import time
import uuid
from typing import Any, Awaitable, Callable, Dict

from fastapi import HTTPException

_TRABAJOS: Dict[str, Dict[str, Any]] = {}
_MAX = 300


def _limpiar() -> None:
    if len(_TRABAJOS) < _MAX:
        return
    terminados = sorted((t for t, v in _TRABAJOS.items() if v.get("terminado")),
                        key=lambda t: _TRABAJOS[t]["terminado"])
    for tid in terminados[:100]:
        _TRABAJOS.pop(tid, None)


def iniciar(usuario_id: Any, fabrica: Callable[[], Awaitable[Any]]) -> str:
    """Lanza `fabrica()` en segundo plano y devuelve el id del trabajo."""
    _limpiar()
    trabajo_id = uuid.uuid4().hex
    trabajo: Dict[str, Any] = {"estado": "en_proceso", "usuario_id": usuario_id, "inicio": time.time()}
    _TRABAJOS[trabajo_id] = trabajo

    async def correr():
        try:
            res = await fabrica()
            if hasattr(res, "model_dump"):
                res = res.model_dump()
            trabajo.update(estado="ok", resultado=res)
        except HTTPException as e:
            trabajo.update(estado="error", error=str(e.detail))
        except Exception as e:  # noqa: BLE001
            trabajo.update(estado="error", error=str(e) or e.__class__.__name__)
        finally:
            trabajo["terminado"] = time.time()

    trabajo["_tarea"] = asyncio.create_task(correr())  # referencia fuerte: que el GC no la cancele
    return trabajo_id


def estado(trabajo_id: str, usuario_id: Any) -> Dict[str, Any]:
    trabajo = _TRABAJOS.get(trabajo_id)
    if not trabajo or trabajo["usuario_id"] != usuario_id:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado (¿se reinició el servidor?).")
    return {
        "estado": trabajo["estado"],
        "segundos": int((trabajo.get("terminado") or time.time()) - trabajo["inicio"]),
        "resultado": trabajo.get("resultado"),
        "error": trabajo.get("error"),
    }
