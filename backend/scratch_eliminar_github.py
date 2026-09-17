import asyncio
import sys
import os

# Ajustar el sys.path para importar módulos del backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.core.database import AsyncSessionLocal
from backend.modules.gestion_usuarios.models import UsuarioGitHub
from sqlalchemy import delete

async def eliminar_vinculos():
    async with AsyncSessionLocal() as db:
        await db.execute(delete(UsuarioGitHub))
        await db.commit()
        print("✅ Todas las vinculaciones de GitHub han sido eliminadas de la base de datos.")

if __name__ == "__main__":
    asyncio.run(eliminar_vinculos())
