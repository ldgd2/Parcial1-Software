from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
import re

from backend.core.database import get_db
from backend.core.permissions.proyecto import requiere_proyecto, usuario_requerido, verificar_permiso
from backend.modules.gestion_usuarios.dependencies import get_current_user_optional
from backend.modules.gestion_asistencia_ia.generar_app_movil.schemas.request import (
    GenerarAppMovilRequest,
    RefinarVistaRequest,
)
from backend.modules.gestion_asistencia_ia.generar_app_movil.schemas.response import (
    AppMovilResponse,
    RefinarVistaResponse,
)
from backend.modules.gestion_asistencia_ia.generar_app_movil.repositories.app_movil_repository import (
    obtener_diagrama_proyecto,
    obtener_proyecto_nombre,
)
from backend.modules.gestion_asistencia_ia.generar_app_movil.services.flutter_generator_service import (
    generar_app_flutter_completa,
    crear_zip_app_flutter,
)
from backend.modules.gestion_asistencia_ia.generar_app_movil.services.flutter_ia_refinement_service import (
    refinar_codigo_con_ia,
)


router = APIRouter(prefix="/api/ia/app-movil", tags=["IA - Generar App Móvil Flutter"])


@router.post("/generar", response_model=AppMovilResponse)
async def generar_app_movil(
    req: GenerarAppMovilRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(usuario_requerido()),
) -> AppMovilResponse:
    await verificar_permiso(db, usuario, req.proyecto_id, "lector")
    diagram_json = req.diagram_json
    if not diagram_json:
        diagram_json = await obtener_diagrama_proyecto(req.proyecto_id, db)

    if not diagram_json or not diagram_json.get("nodes"):
        raise HTTPException(
            status_code=400,
            detail="El proyecto no contiene elementos ni clases en el diagrama para generar la aplicación móvil."
        )

    app_name = req.app_name
    if not app_name or app_name == "app_movil":
        db_name = await obtener_proyecto_nombre(req.proyecto_id, db)
        app_name = re.sub(r"[^a-zA-Z0-9_]", "_", db_name).strip("_").lower() or "app_movil"

    archivos = generar_app_flutter_completa(
        diagram_json=diagram_json,
        output_dir="",
        app_name=app_name,
        api_base_url=req.api_base_url or "http://localhost:8080"
    )

    return AppMovilResponse(
        proyecto_id=req.proyecto_id,
        app_name=app_name,
        archivos_generados=len(archivos),
        resumen=f"Aplicación Flutter '{app_name}' generada con éxito ({len(archivos)} archivos creados).",
        archivos=archivos,
    )


@router.post("/refinar", response_model=RefinarVistaResponse)
async def refinar_vista(
    req: RefinarVistaRequest,
    _ = Depends(usuario_requerido()),
) -> RefinarVistaResponse:
    codigo_refinado, resumen = await refinar_codigo_con_ia(
        vista_nombre=req.vista_nombre,
        codigo_actual=req.codigo_actual,
        instrucciones=req.instrucciones,
        api_endpoint=req.api_endpoint or "",
    )

    return RefinarVistaResponse(
        codigo_refinado=codigo_refinado,
        resumen_cambios=resumen,
    )


@router.get("/preview/{proyecto_id}", response_model=AppMovilResponse)
async def preview_app_movil(
    proyecto_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("lector")),
) -> AppMovilResponse:
    diagram_json = await obtener_diagrama_proyecto(proyecto_id, db)
    if not diagram_json:
        raise HTTPException(status_code=404, detail="Diagrama no encontrado para el proyecto especificado.")

    nombre = await obtener_proyecto_nombre(proyecto_id, db)
    app_name = re.sub(r"[^a-zA-Z0-9_]", "_", nombre).strip("_").lower() or "app_movil"

    archivos = generar_app_flutter_completa(
        diagram_json=diagram_json,
        output_dir="",
        app_name=app_name,
        api_base_url="http://localhost:8080"
    )

    return AppMovilResponse(
        proyecto_id=proyecto_id,
        app_name=app_name,
        archivos_generados=len(archivos),
        resumen=f"Vista previa de {len(archivos)} archivos Flutter generados.",
        archivos=archivos,
    )


@router.get("/descargar/{proyecto_id}")
async def descargar_zip_app_movil(
    proyecto_id: int,
    api_base_url: str = "http://10.0.2.2:8080/api",
    db: AsyncSession = Depends(get_db),
    _ = Depends(requiere_proyecto("lector")),
):
    diagram_json = await obtener_diagrama_proyecto(proyecto_id, db)
    if not diagram_json or not diagram_json.get("nodes"):
        raise HTTPException(
            status_code=400,
            detail="El proyecto no contiene clases en el diagrama para empaquetar la app."
        )

    db_name = await obtener_proyecto_nombre(proyecto_id, db)
    app_name = re.sub(r"[^a-zA-Z0-9_]", "_", db_name).strip("_").lower() or "app_movil"

    zip_bytes = crear_zip_app_flutter(
        diagram_json=diagram_json,
        app_name=app_name,
        api_base_url=api_base_url
    )

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{app_name}_flutter.zip"'
        }
    )


