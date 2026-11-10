import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.core.config import settings
from ..schemas.prompt_schemas import PromptRequest, PromptResponse, AudioRequest
from ..services.prompt_service import generar_diagrama_desde_prompt, transcribe_audio_with_gemini
from backend.modules.gestion_usuarios.dependencies import get_current_user_optional
from backend.core.permissions.proyecto import exigir_permiso_edicion

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/prompt", tags=["Asistencia IA - Prompt"])

@router.get("/config")
async def get_prompt_config():
    """Retorna la configuración activa de proveedores de IA definida en .env."""
    return {
        "default_provider": settings.AI_PROVIDER,
        "has_gemini": bool(settings.GEMINI_API),
        "has_openrouter": bool(settings.OPENROUTE_API),
        "has_kimi": bool(settings.KIMI_API or settings.OPENROUTE_API),
        "models": {
            "gemini": "gemini-2.5-flash",
            "openrouter": settings.OPENROUTER_MODEL or settings.IA_MODEL,
            "kimi": settings.KIMI_MODEL,
            "kimi_vision": settings.KIMI_VISION_MODEL
        }
    }

@router.post("/generar", response_model=PromptResponse)
async def generar_diagrama(
    request: PromptRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    # Un colaborador en modo Lector no puede generar cambios aunque llame directo a la API (CP51)
    await exigir_permiso_edicion(db, request.proyecto_id, current_user)
    try:
        # "Detener" en el chat corta la petición: si el cliente se desconecta, se cancela la
        # llamada a la IA (deja de generar y de gastar) y no se registra ninguna propuesta.
        tarea = asyncio.create_task(generar_diagrama_desde_prompt(
            prompt=request.prompt,
            context=request.context,
            image_base64=request.image_base64,
            image_mime_type=request.image_mime_type or "image/png",
            provider=request.provider,
            api_key=request.api_key,
            proyecto_id=request.proyecto_id,
            db=db,
            estado_antes=request.estado_antes,
            autor=request.autor or getattr(current_user, "nombre", None),
            cancelado=http_request.is_disconnected,
            correcciones=request.correcciones,
        ))
        while True:
            hecho, _ = await asyncio.wait({tarea}, timeout=0.5)
            if hecho:
                break
            if await http_request.is_disconnected():
                tarea.cancel()
                logger.info("[POST /prompt/generar] El usuario detuvo la IA; llamada cancelada")
                raise HTTPException(status_code=499, detail="Solicitud detenida por el usuario")
        resultado = tarea.result()
        return PromptResponse(
            nodes=resultado.get("nodes", []),
            relations=resultado.get("relations", []),
            summary=resultado.get("summary", ""),
            deletedNodes=resultado.get("deletedNodes"),
            deletedRelations=resultado.get("deletedRelations"),
            tasks=resultado.get("tasks"),
            provider_used=resultado.get("provider_used", settings.AI_PROVIDER),
            version_id=resultado.get("version_id"),
            uso_tokens=resultado.get("uso_tokens"),
        )
    except HTTPException as http_exc:
        logger.error(f"[POST /prompt/generar] HTTPException {http_exc.status_code}: {http_exc.detail}")
        raise http_exc
    except Exception as exc:
        logger.error(f"[POST /prompt/generar] Unexpected error: {exc}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Error inesperado al procesar prompt: {str(exc)}")

@router.post("/transcribe-audio")
async def transcribe_audio(
    request: AudioRequest,
    current_user = Depends(get_current_user_optional)
):
    transcripcion = await transcribe_audio_with_gemini(
        request.audio_base64,
        request.mime_type,
        request.api_key
    )
    return {"text": transcripcion}


# ─── CU36: requisitos en PDF → texto (luego /requisitos genera la propuesta) ──

from pydantic import BaseModel as _BaseModel  # noqa: E402

MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGINAS = 40
MAX_TEXTO_REQUISITOS = 15000


class ExtraerPdfRequest(_BaseModel):
    pdf_base64: str
    nombre: str = "requisitos.pdf"


@router.post("/extraer-texto-pdf")
async def extraer_texto_pdf(req: ExtraerPdfRequest, current_user = Depends(get_current_user_optional)):
    """Extrae el texto de un PDF de requisitos (sin IA). Límite: 10 MB y 40 páginas."""
    import base64
    import io
    from pypdf import PdfReader

    datos = req.pdf_base64.split(",", 1)[-1]
    try:
        contenido = base64.b64decode(datos, validate=False)
    except Exception:
        raise HTTPException(status_code=400, detail="El archivo no es un PDF válido")
    if len(contenido) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="El PDF supera los 10 MB")
    try:
        lector = PdfReader(io.BytesIO(contenido))
        paginas = lector.pages[:MAX_PDF_PAGINAS]
        texto = "\n".join((p.extract_text() or "").strip() for p in paginas).strip()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el PDF: {exc}")
    if not texto:
        raise HTTPException(status_code=422, detail="El PDF no tiene texto seleccionable (¿es una imagen escaneada?)")
    truncado = len(texto) > MAX_TEXTO_REQUISITOS or len(lector.pages) > MAX_PDF_PAGINAS
    return {
        "texto": texto[:MAX_TEXTO_REQUISITOS],
        "paginas": len(lector.pages),
        "truncado": truncado,
        "nombre": req.nombre,
    }
