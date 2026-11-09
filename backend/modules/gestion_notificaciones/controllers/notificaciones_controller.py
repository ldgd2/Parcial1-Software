"""CU39: campana de notificaciones y registro de dispositivos para push (Firebase)."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.modules.gestion_notificaciones.models import DispositivoPush, Notificacion
from backend.modules.gestion_notificaciones.services.notificaciones_service import config_web
from backend.modules.gestion_usuarios.dependencies import get_current_user

router = APIRouter(prefix="/api/notificaciones", tags=["Notificaciones (CU39)"])


def _dict(n: Notificacion) -> Dict[str, Any]:
    return {
        "id": n.id, "tipo": n.tipo, "titulo": n.titulo, "mensaje": n.mensaje, "url": n.url,
        "proyecto_id": n.proyecto_id, "leida": n.leida,
        "creada_en": n.created_at.isoformat() if n.created_at else None,
    }


@router.get("/config")
async def configuracion():
    """Config pública de Firebase para el navegador. `push: false` = solo notificaciones dentro de la app."""
    return config_web()


@router.get("")
async def listar(
    solo_no_leidas: bool = Query(False),
    limite: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    usuario=Depends(get_current_user),
):
    q = select(Notificacion).where(Notificacion.usuario_id == usuario.id)
    if solo_no_leidas:
        q = q.where(Notificacion.leida.is_(False))
    filas = (await db.execute(q.order_by(Notificacion.created_at.desc(), Notificacion.id.desc()).limit(limite))).scalars().all()
    no_leidas = (await db.execute(
        select(func.count()).select_from(Notificacion)
        .where(Notificacion.usuario_id == usuario.id, Notificacion.leida.is_(False))
    )).scalar_one()
    return {"no_leidas": no_leidas, "items": [_dict(n) for n in filas]}


@router.post("/{notificacion_id}/leer")
async def marcar_leida(notificacion_id: int, db: AsyncSession = Depends(get_db), usuario=Depends(get_current_user)):
    r = await db.execute(
        update(Notificacion)
        .where(Notificacion.id == notificacion_id, Notificacion.usuario_id == usuario.id)
        .values(leida=True)
    )
    await db.commit()
    if not r.rowcount:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return {"ok": True}


@router.post("/leer-todas")
async def marcar_todas(db: AsyncSession = Depends(get_db), usuario=Depends(get_current_user)):
    r = await db.execute(
        update(Notificacion)
        .where(Notificacion.usuario_id == usuario.id, Notificacion.leida.is_(False))
        .values(leida=True)
    )
    await db.commit()
    return {"marcadas": r.rowcount}


class DispositivoRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=512)
    plataforma: str = Field("web", pattern="^(web|android|ios)$")


@router.post("/dispositivos")
async def registrar_dispositivo(req: DispositivoRequest, db: AsyncSession = Depends(get_db), usuario=Depends(get_current_user)):
    """Guarda el token FCM. Si el token ya era de otra cuenta (mismo navegador), pasa a la cuenta actual."""
    stmt = insert(DispositivoPush).values(usuario_id=usuario.id, token=req.token, plataforma=req.plataforma)
    stmt = stmt.on_conflict_do_update(
        index_elements=[DispositivoPush.token],
        set_={"usuario_id": usuario.id, "plataforma": req.plataforma},
    )
    await db.execute(stmt)
    await db.commit()
    return {"ok": True}


@router.delete("/dispositivos")
async def quitar_dispositivo(token: str = Query(..., min_length=20), db: AsyncSession = Depends(get_db), usuario=Depends(get_current_user)):
    await db.execute(delete(DispositivoPush).where(DispositivoPush.token == token, DispositivoPush.usuario_id == usuario.id))
    await db.commit()
    return {"ok": True}
