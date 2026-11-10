import asyncio
from typing import Any, Coroutine


def ejecutar_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    Ejecuta una corrutina desde el launcher (código síncrono).

    Cada `asyncio.run()` crea un event loop nuevo, pero el `engine` de SQLAlchemy
    es global: si queda una conexión en el pool, la siguiente acción la reutiliza
    desde otro loop y asyncpg falla con
    "cannot perform operation: another operation is in progress".
    Por eso se cierra el pool al terminar, dentro del mismo loop.
    """
    async def _con_cierre():
        from backend.core.database import engine
        await engine.dispose()
        try:
            return await coro
        finally:
            await engine.dispose()

    return asyncio.run(_con_cierre())
