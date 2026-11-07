from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_interoperabilidad.detectar_errores_xml.schemas.request import (
    DetectarErroresRequest,
    CorregirErroresRequest
)
from backend.modules.gestion_interoperabilidad.detectar_errores_xml.schemas.response import (
    DetectarErroresResponse,
    CorregirErroresResponse
)
from backend.modules.gestion_interoperabilidad.detectar_errores_xml.services.detector_service import (
    analizar_errores_logicos_bd
)
from backend.modules.gestion_interoperabilidad.detectar_errores_xml.services.corrector_service import (
    corregir_logica_bd
)

router = APIRouter(prefix="/api/interoperabilidad", tags=["Interoperabilidad - Detectar Errores BD"])


@router.post("/detectar-errores", response_model=DetectarErroresResponse)
async def detectar_errores_endpoint(
    req: DetectarErroresRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Detecta inconsistencias lógicas en el diseño de base de datos importado desde XML o presente en el lienzo.
    Reglas:
    - Tablas sin clave primaria (PK)
    - Claves foráneas huérfanas
    - Tipos de datos discordantes entre FK y PK
    - Dependencias circulares directas
    - Relaciones N:M directas sin tabla intermedia
    - Tablas aisladas sin conexión
    - Palabras reservadas SQL en nombres de tabla o columna
    """
    try:
        reporte = await analizar_errores_logicos_bd(
            xml_content=req.xml_content,
            nodes=req.nodes,
            relations=req.relations
        )
        return reporte
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar el esquema XML/BD: {str(e)}")


@router.post("/corregir-errores", response_model=CorregirErroresResponse)
async def corregir_errores_endpoint(
    req: CorregirErroresRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Subsanación automática de errores lógicos en el diseño de base de datos:
    - Inyecta PK +id:int en tablas carentes de identificador.
    - Transforma relaciones N:M directas en entidades asociativas con sus dos FKs.
    - Alinea tipos discordantes de FKs con la PK referenciada.
    - Desacopla dependencias circulares y enlaza tablas aisladas.
    - Devuelve nodos, relaciones y XML listos para el lienzo y persistencia.
    """
    try:
        resultado = await corregir_logica_bd(
            xml_content=req.xml_content,
            nodes=req.nodes,
            relations=req.relations,
            errores_ids=req.errores_ids
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al corregir lógica de base de datos: {str(e)}")

