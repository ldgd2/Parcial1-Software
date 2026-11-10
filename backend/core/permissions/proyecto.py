"""
CU38 / CU43: permisos DENTRO de un proyecto, validados en el servidor.

Niveles (de menor a mayor):
  - lector     → ver el proyecto: lienzo, historial, actividad, memorias; puede comentar.
  - editor     → cambiar el diagrama: guardar lienzo, pedir cambios a la IA, aprobar/rechazar
                 propuestas, restaurar versiones, memorias, completar tareas.
  - anfitrion  → administrar: permisos de los miembros, repartir roles y tareas, borrar la memoria.

El nivel sale de `colaboradores_proyecto`: el anfitrión es `rol_proyecto='anfitrion'`; los demás
miembros APROBADOS son editor o lector según su `permiso` ('edit' | 'view').

`permiso` es la ÚNICA fuente de verdad. Las columnas antiguas `permiso_rol` / `puede_*` se siguen
escribiendo (con `fijar_permiso` / `guardar_permiso`) solo para que lo que aún las lea vea lo mismo.

Antes la mayoría de estas rutas aceptaban pedidos sin sesión y solo el frontend ocultaba botones:
cualquiera que llamara a la API podía aprobar propuestas o guardar el lienzo.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db

NIVELES = {"lector": 1, "editor": 2, "anfitrion": 3}
PERMISOS_VALIDOS = ("edit", "view")

MENSAJE_SOLO_LECTURA = "Tu permiso en este proyecto es de solo lectura: pide al anfitrión que te haga editor."
_MENSAJES = {
    "editor": MENSAJE_SOLO_LECTURA,
    "anfitrion": "Solo el anfitrión del proyecto puede hacer esto.",
}


def nivel_de(rol_proyecto: Optional[str], permiso: Optional[str]) -> str:
    if rol_proyecto == "anfitrion":
        return "anfitrion"
    return "lector" if permiso == "view" else "editor"


def es_lector(colaborador) -> bool:
    """True si el colaborador (fila de colaboradores_proyecto) solo puede ver."""
    if colaborador is None:
        return False
    return nivel_de(colaborador.rol_proyecto, colaborador.permiso) == "lector"


def fijar_permiso(colaborador, permiso: str) -> None:
    """Asigna 'edit' | 'view' y mantiene sincronizadas las columnas antiguas."""
    lector = permiso == "view"
    colaborador.permiso = "view" if lector else "edit"
    colaborador.permiso_rol = "lector" if lector else "editor"
    colaborador.puede_editar = colaborador.puede_eliminar = colaborador.puede_usar_ia = not lector


async def obtener_colaborador(db: AsyncSession, proyecto_id: int, usuario_id: int):
    from backend.modules.gestion_proyectos.models import ColaboradorProyecto

    return (await db.execute(
        select(ColaboradorProyecto).where(
            ColaboradorProyecto.proyecto_id == proyecto_id,
            ColaboradorProyecto.usuario_id == usuario_id,
        )
    )).scalar_one_or_none()


async def nivel_en_proyecto(db: AsyncSession, proyecto_id: int, usuario_id: int) -> Optional[str]:
    """Nivel del usuario en el proyecto, o None si no es miembro aprobado."""
    from backend.modules.gestion_proyectos.models import ColaboradorProyecto

    fila = (await db.execute(
        select(ColaboradorProyecto.rol_proyecto, ColaboradorProyecto.permiso, ColaboradorProyecto.estado)
        .where(ColaboradorProyecto.proyecto_id == proyecto_id, ColaboradorProyecto.usuario_id == usuario_id)
    )).first()
    if not fila or fila.estado != "aprobado":
        return None
    return nivel_de(fila.rol_proyecto, fila.permiso)


async def verificar_permiso(db: AsyncSession, usuario, proyecto_id: Optional[int], nivel: str = "lector") -> str:
    """Lanza 401/403/404 si el usuario no alcanza `nivel` en el proyecto. Devuelve su nivel."""
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inicia sesión para continuar.",
                            headers={"WWW-Authenticate": "Bearer"})
    if not proyecto_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Falta el proyecto.")
    actual = await nivel_en_proyecto(db, int(proyecto_id), usuario.id)
    if actual is None:
        from backend.modules.gestion_proyectos.models import Proyecto
        if await db.get(Proyecto, int(proyecto_id)) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No eres miembro aprobado de este proyecto.")
    if NIVELES[actual] < NIVELES[nivel]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_MENSAJES.get(nivel, "Permiso insuficiente."))
    return actual


async def exigir_permiso_edicion(db: AsyncSession, proyecto_id: Optional[int], usuario) -> None:
    """Nivel editor en el proyecto. Sin proyecto (diagrama local, sin sala) no hay nada que comprobar."""
    if proyecto_id:
        await verificar_permiso(db, usuario, proyecto_id, "editor")


async def guardar_permiso(db: AsyncSession, proyecto_id: int, usuario_id: int, lector: bool) -> bool:
    """Persiste el permiso de un miembro (no anfitrión). Devuelve False si no es colaborador."""
    from backend.modules.gestion_proyectos.models import ColaboradorProyecto

    resultado = await db.execute(
        update(ColaboradorProyecto)
        .where(
            ColaboradorProyecto.proyecto_id == proyecto_id,
            ColaboradorProyecto.usuario_id == usuario_id,
            ColaboradorProyecto.rol_proyecto != "anfitrion",
        )
        .values(
            permiso="view" if lector else "edit",
            permiso_rol="lector" if lector else "editor",
            puede_editar=not lector,
            puede_eliminar=not lector,
            puede_usar_ia=not lector,
        )
    )
    await db.commit()
    return resultado.rowcount > 0


def requiere_proyecto(nivel: str = "lector"):
    """Dependencia para rutas con `proyecto_id` en la URL. Devuelve el usuario autenticado."""
    from backend.modules.gestion_usuarios.dependencies import get_current_user_optional

    async def _dep(proyecto_id: int, db: AsyncSession = Depends(get_db), usuario=Depends(get_current_user_optional)):
        await verificar_permiso(db, usuario, proyecto_id, nivel)
        return usuario

    return _dep


def usuario_requerido():
    """Sesión obligatoria (para rutas sin proyecto en la URL que validan con `verificar_permiso`)."""
    from backend.modules.gestion_usuarios.dependencies import get_current_user_optional

    async def _dep(usuario=Depends(get_current_user_optional)):
        if usuario is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inicia sesión para continuar.",
                                headers={"WWW-Authenticate": "Bearer"})
        return usuario

    return _dep
