from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_interoperabilidad.exportar_a_xml.services import export_service

router = APIRouter(
    prefix="/interoperabilidad",
    tags=["Gestion Interoperabilidad"]
)

@router.get("/{proyecto_id}/exportar-ea")
async def exportar_xmi(
    proyecto_id: int,
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Exporta el diagrama del proyecto a un archivo XML en formato OMG XMI 2.1 
    compatible con Enterprise Architect.
    """
    xml_content = await export_service.generar_xmi(proyecto_id, user, db)
    if not xml_content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se pudo generar el XMI o proyecto no encontrado.")
    
    return Response(
        content=xml_content, 
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=diagrama_{proyecto_id}.xml"}
    )
