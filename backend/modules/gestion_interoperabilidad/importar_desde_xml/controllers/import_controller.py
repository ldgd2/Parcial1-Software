from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.modules.gestion_usuarios.dependencies import get_current_user
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_interoperabilidad.importar_desde_xml.services import import_service

router = APIRouter(
    prefix="/interoperabilidad",
    tags=["Gestion Interoperabilidad"]
)

@router.post("/{proyecto_id}/importar-ea")
async def importar_xmi(
    proyecto_id: int,
    file: UploadFile = File(...),
    user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Recibe un archivo XML (XMI 2.1) de Enterprise Architect,
    lo parsea y retorna los nodos y relaciones extraídos.
    """
    if not file.filename.endswith('.xml'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un XML.")
        
    contents = await file.read()
    try:
        # EA XMI suele venir en windows-1252, intentamos utf-8 primero, luego fallback
        try:
            text_content = contents.decode('utf-8')
        except UnicodeDecodeError:
            text_content = contents.decode('windows-1252')
            
        diagram_data = await import_service.parsear_xmi(text_content)
        return {"status": "success", "data": diagram_data}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error parseando XMI: {str(e)}")
