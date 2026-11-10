"""
CU08: compartir un proyecto por correo con un usuario registrado, eligiendo su permiso.

Antes solo existía el enlace de invitación (el invitado quedaba "pendiente" como editor) y no había
"Compartidos conmigo". Ver y cambiar el permiso de los miembros vive en `permisos_proyecto` (CU38).
"""
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.permissions.proyecto import PERMISOS_VALIDOS, fijar_permiso, nivel_de, obtener_colaborador, verificar_permiso
from backend.modules.gestion_proyectos.models import ColaboradorProyecto, Proyecto
from backend.modules.gestion_usuarios.models import Usuario


async def invitar_por_correo(db: AsyncSession, proyecto_id: int, email: str, permiso: str, anfitrion: Usuario) -> dict:
    await verificar_permiso(db, anfitrion, proyecto_id, "anfitrion")
    if permiso not in PERMISOS_VALIDOS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Permiso inválido: usa 'edit' (editor) o 'view' (lector).")
    email = (email or "").strip().lower()

    invitado = (await db.execute(select(Usuario).where(func.lower(Usuario.email) == email))).scalar_one_or_none()
    if invitado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay ninguna cuenta con el correo {email}. El invitado primero debe registrarse en la plataforma.",
        )
    if invitado.id == anfitrion.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya eres el anfitrión de este proyecto.")

    colaborador = await obtener_colaborador(db, proyecto_id, invitado.id)
    if colaborador and colaborador.rol_proyecto == "anfitrion":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ese usuario ya es anfitrión del proyecto.")

    if colaborador is None:
        colaborador = ColaboradorProyecto(proyecto_id=proyecto_id, usuario_id=invitado.id,
                                          rol_proyecto="invitado", estado="aprobado")
        db.add(colaborador)
    else:
        # Ya había pedido entrar con el enlace (o estaba rechazado): la invitación lo aprueba
        colaborador.estado = "aprobado"
    fijar_permiso(colaborador, permiso)
    await db.commit()

    # Si está conectado a la sala, el permiso se aplica al momento
    from backend.modules.gestion_proyectos.permisos_proyecto.permisos_service import aplicar_en_sala
    await aplicar_en_sala(db, proyecto_id, invitado.id, permiso)
    return {
        "usuario_id": invitado.id,
        "nombre": invitado.nombre,
        "email": invitado.email,
        "rol_proyecto": colaborador.rol_proyecto,
        "estado": colaborador.estado,
        "permiso": colaborador.permiso,
        "nivel": nivel_de(colaborador.rol_proyecto, colaborador.permiso),
    }


async def compartidos_conmigo(db: AsyncSession, usuario: Usuario) -> list[Proyecto]:
    """Proyectos donde el usuario es invitado aprobado (no los que creó)."""
    resultado = await db.execute(
        select(Proyecto)
        .join(ColaboradorProyecto, ColaboradorProyecto.proyecto_id == Proyecto.id)
        .where(
            ColaboradorProyecto.usuario_id == usuario.id,
            ColaboradorProyecto.estado == "aprobado",
            ColaboradorProyecto.rol_proyecto != "anfitrion",
        )
        .options(selectinload(Proyecto.colaboradores))
        .order_by(Proyecto.id.desc())
    )
    return list(resultado.scalars().all())
