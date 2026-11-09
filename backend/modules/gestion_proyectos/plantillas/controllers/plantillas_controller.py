"""CU42: plantillas de proyecto (base + guardadas por cada usuario)."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user, get_current_user_optional
from backend.modules.gestion_proyectos.plantillas.models import PlantillaProyecto
from backend.modules.gestion_proyectos.plantillas.services.plantillas_base import listar_base, obtener_base

router = APIRouter(prefix="/api/plantillas", tags=["Proyectos - Plantillas"])

MAX_CLASES_PLANTILLA = 200


class GuardarPlantillaRequest(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    descripcion: str = Field("", max_length=500)
    lienzo: Dict[str, Any] = Field(..., description="{nodes, relations} del diagrama")


def _meta(p: PlantillaProyecto) -> Dict[str, Any]:
    return {"id": f"u:{p.id}", "nombre": p.nombre, "descripcion": p.descripcion,
            "clases": len((p.lienzo or {}).get("nodes") or []), "origen": "usuario"}


@router.get("")
async def listar_plantillas(db: AsyncSession = Depends(get_db), usuario=Depends(get_current_user_optional)) -> List[Dict[str, Any]]:
    propias: List[Dict[str, Any]] = []
    if usuario:
        filas = (await db.execute(
            select(PlantillaProyecto).where(PlantillaProyecto.usuario_id == usuario.id)
            .order_by(PlantillaProyecto.created_at.desc())
        )).scalars().all()
        propias = [_meta(p) for p in filas]
    return listar_base() + propias


@router.get("/{plantilla_id}")
async def obtener_plantilla(plantilla_id: str, db: AsyncSession = Depends(get_db), usuario=Depends(get_current_user_optional)) -> Dict[str, Any]:
    if plantilla_id.startswith("base:"):
        p = obtener_base(plantilla_id[5:])
        if not p:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        return p
    if not plantilla_id.startswith("u:") or not plantilla_id[2:].isdigit() or not usuario:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    p = await db.get(PlantillaProyecto, int(plantilla_id[2:]))
    if not p or p.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return {**_meta(p), "lienzo": p.lienzo}


@router.post("", status_code=201)
async def guardar_plantilla(req: GuardarPlantillaRequest, db: AsyncSession = Depends(get_db), usuario=Depends(get_current_user)) -> Dict[str, Any]:
    nodes = (req.lienzo or {}).get("nodes") or []
    if not nodes:
        raise HTTPException(status_code=400, detail="El diagrama está vacío: no hay nada que guardar como plantilla")
    if len(nodes) > MAX_CLASES_PLANTILLA:
        raise HTTPException(status_code=400, detail=f"Máximo {MAX_CLASES_PLANTILLA} clases por plantilla")
    lienzo = {"nodes": nodes, "relations": (req.lienzo or {}).get("relations") or []}
    p = PlantillaProyecto(usuario_id=usuario.id, nombre=req.nombre.strip(), descripcion=req.descripcion.strip(), lienzo=lienzo)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _meta(p)


@router.delete("/{plantilla_id}", status_code=204)
async def eliminar_plantilla(plantilla_id: str, db: AsyncSession = Depends(get_db), usuario=Depends(get_current_user)) -> None:
    if not plantilla_id.startswith("u:") or not plantilla_id[2:].isdigit():
        raise HTTPException(status_code=400, detail="Solo se pueden borrar plantillas propias")
    p = await db.get(PlantillaProyecto, int(plantilla_id[2:]))
    if not p or p.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    await db.delete(p)
    await db.commit()
