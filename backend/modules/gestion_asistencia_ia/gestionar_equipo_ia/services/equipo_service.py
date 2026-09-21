import json
import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.core.config import settings
from backend.modules.gestion_usuarios.models import TareaIA
from backend.modules.gestion_asistencia_ia.gestionar_equipo_ia.schemas.request import (
    GenerarEquipoRequest,
    HabilidadDesarrollador,
)


def _construir_prompt(req: GenerarEquipoRequest, historial: list[TareaIA] = None) -> str:
    devs_str = "\n".join(
        f"- usuario_id={d.usuario_id}, nombre={d.nombre}, etiquetas=[{', '.join(d.etiquetas)}]"
        for d in req.desarrolladores
    )

    historial_str = "No hay tareas previas."
    if historial and len(historial) > 0:
        historial_str = "\n".join(
            f"- [Asignada a usuario_id={t.usuario_id}] {t.titulo} ({'Completada' if t.completada else 'Pendiente'})"
            for t in historial
        )

    return (
        f"Eres un Project Manager de software experimentado.\n"
        f"Proyecto: {req.descripcion_proyecto}\n\n"
        f"Desarrolladores disponibles:\n{devs_str}\n\n"
        f"HISTORIAL DE TAREAS YA EXISTENTES (No repitas estas tareas):\n{historial_str}\n\n"
        f"INSTRUCCIONES:\n"
        f"1. Analiza el proyecto y el historial. Tu objetivo es generar NUEVAS tareas que completen el desarrollo sin duplicar lo ya asignado.\n"
        f"2. Asigna tareas a los desarrolladores según sus etiquetas/habilidades. "
        f"Quien tenga más experiencia en un área recibe más responsabilidad en esa área.\n"
        f"3. Cada tarea debe tener un 'tipo': 'diagrama' (para hacer dentro del diagramador UML) "
        f"o 'desarrollo' (tarea de código/implementación fuera del diagramador).\n"
        f"4. Incluye una descripción clara de contexto para que el desarrollador sepa exactamente qué hacer y por qué.\n"
        f"5. Asigna un 'orden' (entero) para priorizar las tareas de cada usuario.\n\n"
        f"RESPONDE ÚNICAMENTE con un JSON válido con esta estructura:\n"
        f'{{"tareas": ['
        f'{{"usuario_id": 1, "titulo": "Modelar clase Usuario", "descripcion": "Crear la clase Usuario en el lienzo...", '
        f'"tipo": "diagrama", "orden": 1}}, '
        f'{{"usuario_id": 2, "titulo": "Implementar AuthService", "descripcion": "Desarrollar la lógica de autenticación...", '
        f'"tipo": "desarrollo", "orden": 1}}'
        f']}}'
    )


async def _llamar_gemini_equipo(prompt: str) -> dict:
    api_key = settings.GEMINI_API
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API no configurada en settings")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            response = await client.post(url, json=payload)
            data = response.json()

            if response.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Error Gemini API: {data}")

            if "candidates" not in data or not data["candidates"]:
                raise HTTPException(status_code=500, detail="Respuesta vacía de la IA")

            texto = data["candidates"][0]["content"]["parts"][0]["text"]

            if texto.startswith("```"):
                lines = texto.strip().split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                texto = "\n".join(lines)

            return json.loads(texto)

        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Error de red con Gemini: {exc}")
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=500, detail=f"Formato inválido de respuesta IA: {exc}")


async def generar_y_persistir_tareas(req: GenerarEquipoRequest, db: AsyncSession) -> list[TareaIA]:
    # Obtener historial para evitar repeticiones
    result = await db.execute(
        select(TareaIA).where(TareaIA.proyecto_id == req.proyecto_id)
    )
    tareas_existentes = result.scalars().all()

    prompt = _construir_prompt(req, list(tareas_existentes))
    resultado = await _llamar_gemini_equipo(prompt)

    tareas_data: list[dict] = resultado.get("tareas", [])
    if not tareas_data:
        raise HTTPException(status_code=500, detail="La IA no generó ninguna tarea")

    # Eliminado el bloque de borrado de tareas previas para preservar el historial

    nuevas_tareas: list[TareaIA] = []
    for item in tareas_data:
        tarea = TareaIA(
            proyecto_id=req.proyecto_id,
            usuario_id=item["usuario_id"],
            tipo=item.get("tipo", "desarrollo"),
            titulo=item["titulo"],
            descripcion=item.get("descripcion"),
            completada=False,
            orden=item.get("orden", 0),
        )
        db.add(tarea)
        nuevas_tareas.append(tarea)

    await db.commit()
    for t in nuevas_tareas:
        await db.refresh(t)

    return nuevas_tareas


async def obtener_tareas_usuario(proyecto_id: int, usuario_id: int, db: AsyncSession) -> list[TareaIA]:
    result = await db.execute(
        select(TareaIA)
        .where(TareaIA.proyecto_id == proyecto_id, TareaIA.usuario_id == usuario_id)
        .order_by(TareaIA.orden)
    )
    return result.scalars().all()


async def obtener_tareas_proyecto(proyecto_id: int, db: AsyncSession) -> list[TareaIA]:
    result = await db.execute(
        select(TareaIA)
        .where(TareaIA.proyecto_id == proyecto_id)
        .order_by(TareaIA.usuario_id, TareaIA.orden)
    )
    return result.scalars().all()


async def marcar_tarea(tarea_id: int, usuario_id: int, completada: bool, db: AsyncSession) -> TareaIA:
    result = await db.execute(
        select(TareaIA).where(TareaIA.id == tarea_id, TareaIA.usuario_id == usuario_id)
    )
    tarea = result.scalar_one_or_none()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    tarea.completada = completada
    await db.commit()
    await db.refresh(tarea)
    return tarea
