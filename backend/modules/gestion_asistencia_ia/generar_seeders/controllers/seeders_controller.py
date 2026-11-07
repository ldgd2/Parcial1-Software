from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_asistencia_ia.generar_seeders.schemas.request import GenerarSeedersRequest
from backend.modules.gestion_asistencia_ia.generar_seeders.schemas.response import GenerarSeedersResponse
from backend.modules.gestion_asistencia_ia.generar_seeders.services.seeders_service import generar_script_seeders
from backend.modules.gestion_asistencia_ia.generar_seeders.repositories.seeders_repository import SeedersRepository

router = APIRouter(prefix="/api/ia/seeders", tags=["IA - Generación de Seeders"])


@router.post("/generar", response_model=GenerarSeedersResponse)
async def generar_seeders_endpoint(
    req: GenerarSeedersRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Genera seeders con datos randómicos coherentes y ordenamiento topológico
    para poblar la base de datos PostgreSQL generada en Spring Boot.
    """
    try:
        nodes = []
        relations = []

        if req.diagram_json:
            nodes = req.diagram_json.get("nodes", [])
            relations = req.diagram_json.get("relations", []) or req.diagram_json.get("edges", [])
        elif req.proyecto_id:
            repo = SeedersRepository(db)
            lienzo = await repo.obtener_diagrama_por_proyecto_id(req.proyecto_id)
            if lienzo:
                nodes = lienzo.get("nodes", [])
                relations = lienzo.get("relations", []) or lienzo.get("edges", [])

        if not nodes:
            raise HTTPException(
                status_code=400,
                detail="No se encontraron tablas o nodos en el diagrama para generar seeders."
            )

        resultado = generar_script_seeders(
            nodes=nodes,
            relations=relations,
            cantidad_por_tabla=req.cantidad_por_tabla,
            formato=req.formato
        )
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar seeders de prueba: {str(e)}"
        )
