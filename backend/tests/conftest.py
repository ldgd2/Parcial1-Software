"""
Tests del backend con la IA SIMULADA (no se llama a Kimi/Gemini/OpenRouter ni se gastan tokens).

Cada test corre dentro de una transacción que se DESHACE al terminar: usa la base de desarrollo
(con las migraciones aplicadas) pero no deja nada guardado. Los `commit()` de los servicios se
convierten en savepoints (join_transaction_mode="create_savepoint").

Ejecutar desde la raíz del repo:
    backend\\venv\\Scripts\\python -m pytest backend/tests -q
"""
import json
import uuid
from typing import Any, Dict, List

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from backend.core.config import settings
from backend.core.database import engine as engine_app, get_db
from backend.main import app
from backend.modules.gestion_notificaciones.services import notificaciones_service
from backend.modules.gestion_proyectos.models import ColaboradorProyecto, Proyecto
from backend.modules.gestion_usuarios.dependencies import get_current_user, get_current_user_optional
from backend.modules.gestion_usuarios.models import UsuarioRegistrado

engine_app.echo = False


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    async with engine.connect() as conn:
        trans = await conn.begin()
        sesion = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
        try:
            yield sesion
        finally:
            await sesion.close()
            await trans.rollback()
    await engine.dispose()


@pytest.fixture
def eventos_notif(monkeypatch) -> List[Dict[str, Any]]:
    """Captura los eventos de notificación en lugar de procesarlos en segundo plano."""
    capturados: List[Dict[str, Any]] = []
    monkeypatch.setattr(notificaciones_service, "programar", lambda evs: capturados.extend(evs or []))
    return capturados


class Equipo:
    """Un proyecto con anfitrión (Ana) e invitado (Beto), ambos aprobados."""

    def __init__(self, proyecto, ana, beto):
        self.proyecto, self.ana, self.beto = proyecto, ana, beto

    @property
    def pid(self) -> int:
        return self.proyecto.id


@pytest_asyncio.fixture
async def equipo(db, eventos_notif) -> Equipo:
    sufijo = uuid.uuid4().hex[:8]
    ana = UsuarioRegistrado(nombre="Ana Test", email=f"ana_{sufijo}@test.local")
    beto = UsuarioRegistrado(nombre="Beto Test", email=f"beto_{sufijo}@test.local")
    db.add_all([ana, beto])
    await db.flush()
    proyecto = Proyecto(nombre=f"Proyecto test {sufijo}", descripcion="Sistema de ventas de prueba")
    db.add(proyecto)
    await db.flush()
    db.add_all([
        ColaboradorProyecto(proyecto_id=proyecto.id, usuario_id=ana.id, rol_proyecto="anfitrion", estado="aprobado"),
        ColaboradorProyecto(proyecto_id=proyecto.id, usuario_id=beto.id, rol_proyecto="invitado", estado="aprobado"),
    ])
    await db.commit()
    eventos_notif.clear()   # crear el equipo no es parte de lo que se prueba
    return Equipo(proyecto, ana, beto)


class Cliente:
    """Cliente HTTP contra la app real (ASGI), con la sesión del test y el usuario elegido."""

    def __init__(self, db):
        self.db = db
        self.usuario = None

    def como(self, usuario):
        self.usuario = usuario
        return self

    async def _req(self, metodo: str, url: str, **kw):
        async def _db():
            yield self.db

        async def _usuario():
            if self.usuario is None:
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="Sin sesión")
            return self.usuario

        async def _usuario_opcional():
            return self.usuario

        app.dependency_overrides[get_db] = _db
        app.dependency_overrides[get_current_user] = _usuario
        app.dependency_overrides[get_current_user_optional] = _usuario_opcional
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
                return await c.request(metodo, url, **kw)
        finally:
            app.dependency_overrides.clear()

    async def get(self, url, **kw):
        return await self._req("GET", url, **kw)

    async def post(self, url, **kw):
        return await self._req("POST", url, **kw)

    async def put(self, url, **kw):
        return await self._req("PUT", url, **kw)

    async def delete(self, url, **kw):
        return await self._req("DELETE", url, **kw)


@pytest.fixture
def cliente(db) -> Cliente:
    return Cliente(db)


# ─── IA simulada ────────────────────────────────────────────────────────────

class IASimulada:
    """Reemplaza al cliente LLM: devuelve la respuesta que el test configure y registra los prompts."""

    def __init__(self):
        self.respuesta: Any = {
            "summary": "Se agregó la clase Pago relacionada con Venta.",
            "nodes": [
                {"name": "Venta", "attributes": ["+id: int", "+total: float"], "methods": []},
                {"name": "Pago", "attributes": ["+id: int", "+monto: float"], "methods": []},
            ],
            "relations": [{"from": "Pago", "to": "Venta", "type": "association"}],
        }
        self.prompts: List[Dict[str, Any]] = []

    async def consultar_llm(self, prompt, context=None, **kw):
        self.prompts.append({"prompt": prompt, "context": context})
        r = self.respuesta
        return (json.dumps(r) if isinstance(r, (dict, list)) else r), "kimi"


@pytest.fixture
def ia(monkeypatch) -> IASimulada:
    from backend.modules.gestion_asistencia_ia.generar_diagrama_prompt.services import llm_client, prompt_service

    simulada = IASimulada()
    monkeypatch.setattr(prompt_service, "consultar_llm", simulada.consultar_llm)

    async def sin_red(*a, **k):
        raise RuntimeError("Proveedor real desactivado en los tests")

    for nombre in ("_consultar_gemini", "_consultar_openrouter", "consultar_llm"):
        if hasattr(llm_client, nombre):
            monkeypatch.setattr(llm_client, nombre, sin_red)
    return simulada
