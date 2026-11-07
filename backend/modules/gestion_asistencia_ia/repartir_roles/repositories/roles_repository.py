from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any

from backend.modules.gestion_proyectos.models import ColaboradorProyecto, Proyecto
from backend.modules.gestion_usuarios.models import Usuario


async def obtener_colaboradores_proyecto(proyecto_id: int, db: AsyncSession) -> List[ColaboradorProyecto]:
    result = await db.execute(
        select(ColaboradorProyecto)
        .where(ColaboradorProyecto.proyecto_id == proyecto_id)
    )
    return list(result.scalars().all())


async def obtener_usuarios_por_ids(usuario_ids: List[int], db: AsyncSession) -> Dict[int, Usuario]:
    if not usuario_ids:
        return {}
    result = await db.execute(
        select(Usuario).where(Usuario.id.in_(usuario_ids))
    )
    usuarios = result.scalars().all()
    return {u.id: u for u in usuarios}


async def asegurar_colaborador_proyecto(proyecto_id: int, usuario_id: int, db: AsyncSession) -> ColaboradorProyecto:
    result = await db.execute(
        select(ColaboradorProyecto).where(
            (ColaboradorProyecto.proyecto_id == proyecto_id) &
            (ColaboradorProyecto.usuario_id == usuario_id)
        )
    )
    colab = result.scalar_one_or_none()
    if not colab:
        colab = ColaboradorProyecto(
            proyecto_id=proyecto_id,
            usuario_id=usuario_id,
            rol_proyecto="invitado",
            estado="aprobado"
        )
        db.add(colab)
        await db.flush()
    return colab


async def guardar_roles_colaboradores(
    proyecto_id: int,
    roles_asignados: List[Dict[str, Any]],
    db: AsyncSession
) -> None:
    res_users = await db.execute(select(Usuario.id))
    valid_uids = set(res_users.scalars().all())

    for item in roles_asignados:
        uid = item.get("usuario_id")
        if not uid or uid not in valid_uids:
            continue
        colab = await asegurar_colaborador_proyecto(proyecto_id, uid, db)
        colab.rol_ia = item.get("rol_ia")
        colab.areas = item.get("areas", [])
        colab.responsabilidades = item.get("responsabilidades", [])
    await db.commit()

