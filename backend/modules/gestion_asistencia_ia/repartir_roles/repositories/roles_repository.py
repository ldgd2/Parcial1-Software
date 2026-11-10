from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any

from backend.modules.gestion_proyectos.models import ColaboradorProyecto, Proyecto
from backend.modules.gestion_usuarios.models import Usuario


async def obtener_colaboradores_proyecto(proyecto_id: int, db: AsyncSession) -> List[ColaboradorProyecto]:
    result = await db.execute(
        select(ColaboradorProyecto)
        .where(
            ColaboradorProyecto.proyecto_id == proyecto_id,
            ColaboradorProyecto.estado == "aprobado",   # pendientes y rechazados no reciben roles
        )
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


async def asegurar_colaborador_proyecto(proyecto_id: int, usuario_id: int, db: AsyncSession) -> Optional[ColaboradorProyecto]:
    """Fila del miembro APROBADO, o None si no lo es.

    Antes, si el usuario no estaba en el proyecto se lo creaba como miembro aprobado (editor):
    asignar un rol a cualquier id metía a esa persona al proyecto sin pasar por la aprobación
    del anfitrión."""
    result = await db.execute(
        select(ColaboradorProyecto).where(
            (ColaboradorProyecto.proyecto_id == proyecto_id) &
            (ColaboradorProyecto.usuario_id == usuario_id) &
            (ColaboradorProyecto.estado == "aprobado")
        )
    )
    return result.scalar_one_or_none()


async def guardar_roles_colaboradores(
    proyecto_id: int,
    roles_asignados: List[Dict[str, Any]],
    db: AsyncSession
) -> None:
    for item in roles_asignados:
        uid = item.get("usuario_id")
        if not uid:
            continue
        colab = await asegurar_colaborador_proyecto(proyecto_id, uid, db)
        if colab is None:   # no es miembro aprobado: no se le asigna nada
            continue
        colab.rol_ia = item.get("rol_ia")
        colab.areas = item.get("areas", [])
        colab.responsabilidades = item.get("responsabilidades", [])
    await db.commit()

