import json
import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.core.config import settings
from backend.modules.gestion_usuarios.models import TareaIA, Usuario, estimar_tarea
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

    first_id = req.desarrolladores[0].usuario_id if req.desarrolladores else 1
    second_id = req.desarrolladores[1].usuario_id if len(req.desarrolladores) > 1 else first_id

    return (
        f"Eres un Project Manager de software experimentado.\n"
        f"Proyecto: {req.descripcion_proyecto}\n\n"
        f"Desarrolladores disponibles:\n{devs_str}\n\n"
        f"HISTORIAL DE TAREAS YA EXISTENTES (No repitas estas tareas):\n{historial_str}\n\n"
        f"INSTRUCCIONES:\n"
        f"1. Analiza el proyecto y el historial. Tu objetivo es generar NUEVAS tareas que completen el desarrollo sin duplicar lo ya asignado.\n"
        f"2. Asigna tareas a los desarrolladores según sus etiquetas/habilidades. "
        f"Usa EXCLUSIVAMENTE los 'usuario_id' indicados en la lista de desarrolladores disponibles.\n"
        f"3. Cada tarea debe tener un 'tipo': 'diagrama' (para hacer dentro del diagramador UML) "
        f"o 'desarrollo' (tarea de código/implementación fuera del diagramador).\n"
        f"4. Incluye una descripción clara de contexto para que el desarrollador sepa exactamente qué hacer y por qué.\n"
        f"5. Asigna un 'orden' (entero) para priorizar las tareas de cada usuario.\n"
        f"6. Estima el esfuerzo: 'estimacion_horas' (entero, 1 a 40) y 'complejidad' ('baja', 'media' o 'alta').\n\n"
        f"RESPONDE ÚNICAMENTE con un JSON válido con esta estructura:\n"
        f'{{"tareas": ['
        f'{{"usuario_id": {first_id}, "titulo": "Modelar arquitectura en lienzo", "descripcion": "Crear entidades principales...", "tipo": "diagrama", "orden": 1, "estimacion_horas": 3, "complejidad": "media"}}, '
        f'{{"usuario_id": {second_id}, "titulo": "Implementar servicios y controladores", "descripcion": "Desarrollar la lógica de negocio...", "tipo": "desarrollo", "orden": 1, "estimacion_horas": 6, "complejidad": "alta"}}'
        f']}}'
    )


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned

async def _llamar_ia_equipo(prompt: str) -> dict:
    provider = (settings.AI_PROVIDER or "gemini").lower().strip()

    if provider == "kimi":
        key = settings.KIMI_API
        if not key:
            raise HTTPException(status_code=500, detail="KIMI_API no configurada en el archivo .env")
        model = settings.KIMI_MODEL or "kimi-k3.1-pro"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Eres un Project Manager de software senior. Devuelve únicamente JSON con las tareas asignadas."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 1.0 if "kimi-k" in model else 0.1,
            "max_tokens": 1500,
            "response_format": {"type": "json_object"}
        }
        if "kimi-k" in model:
            payload["reasoning_effort"] = "low"
        
        async with httpx.AsyncClient(timeout=90.0) as client:
            endpoints = [
                ("https://api.moonshot.ai/v1/chat/completions", model),
                ("https://api.moonshot.cn/v1/chat/completions", "moonshot-v1-8k")
            ]
            last_err = ""
            for ep_url, ep_model in endpoints:
                payload["model"] = ep_model
                payload["temperature"] = 1.0 if "kimi-k" in ep_model else 0.1
                try:
                    res = await client.post(ep_url, json=payload, headers={"Authorization": f"Bearer {key}"})
                    if res.status_code == 200:
                        data = res.json()
                        return json.loads(_clean_json_text(data["choices"][0]["message"]["content"]))
                    last_err = f"{res.status_code}: {res.text}"
                except Exception as ex:
                    last_err = str(ex)
            raise HTTPException(status_code=502, detail=f"Error Moonshot Kimi API: {last_err}")

    elif provider == "openrouter":
        key = settings.OPENROUTE_API
        if not key:
            raise HTTPException(status_code=500, detail="OPENROUTE_API no configurada")
        model = settings.OPENROUTER_MODEL or settings.IA_MODEL or "google/gemini-2.0-flash-exp:free"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Eres un Project Manager de software senior y asignas tareas en JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1500,
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            res = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {key}"})
            if res.status_code == 200:
                data = res.json()
                return json.loads(_clean_json_text(data["choices"][0]["message"]["content"]))

    # Fallback o proveedor por defecto: Gemini
    api_key = settings.GEMINI_API
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API no configurada")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1, "maxOutputTokens": 1500},
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
            return json.loads(_clean_json_text(texto))
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
    resultado = await _llamar_ia_equipo(prompt)

    tareas_data: list[dict] = resultado.get("tareas", [])
    if not tareas_data:
        raise HTTPException(status_code=500, detail="La IA no generó ninguna tarea")

    # Eliminado el bloque de borrado de tareas previas para preservar el historial

    res_users = await db.execute(select(Usuario.id))
    valid_uids = set(res_users.scalars().all())
    default_uid = next(iter(valid_uids)) if valid_uids else 1

    dev_ids = [d.usuario_id for d in req.desarrolladores if d.usuario_id in valid_uids]
    if not dev_ids:
        dev_ids = [default_uid]
    dev_id_set = set(dev_ids)

    nuevas_tareas: list[TareaIA] = []
    for idx, item in enumerate(tareas_data):
        raw_uid = item.get("usuario_id")
        try:
            uid = int(raw_uid) if raw_uid is not None else None
        except (ValueError, TypeError):
            uid = None

        if uid not in dev_id_set:
            if len(dev_ids) == 1:
                uid = dev_ids[0]
            elif isinstance(uid, int) and 1 <= uid <= len(dev_ids):
                uid = dev_ids[uid - 1]
            else:
                uid = dev_ids[idx % len(dev_ids)]

        if uid not in valid_uids:
            uid = default_uid

        tarea = TareaIA(
            proyecto_id=req.proyecto_id,
            usuario_id=uid,
            tipo=item.get("tipo", "desarrollo"),
            titulo=item.get("titulo", "Tarea de desarrollo"),
            descripcion=item.get("descripcion"),
            completada=False,
            orden=item.get("orden", idx + 1),
        )
        tarea.estimacion_horas, tarea.complejidad = estimar_tarea(
            tarea.tipo, tarea.titulo, tarea.descripcion, item.get("estimacion_horas"), item.get("complejidad")
        )
        if req.persistir:
            db.add(tarea)
        nuevas_tareas.append(tarea)

    # Con persistir=False la IA solo propone: las tareas se crean al aprobar la propuesta
    if req.persistir:
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
    return list(result.scalars().all())


async def obtener_tareas_proyecto(proyecto_id: int, db: AsyncSession) -> list[TareaIA]:
    result = await db.execute(
        select(TareaIA)
        .where(TareaIA.proyecto_id == proyecto_id)
        .order_by(TareaIA.usuario_id, TareaIA.orden)
    )
    return list(result.scalars().all())


async def marcar_tarea(tarea_id: int, usuario_id: int | None, completada: bool, db: AsyncSession) -> TareaIA:
    result = await db.execute(
        select(TareaIA).where(TareaIA.id == tarea_id)
    )
    tarea = result.scalar_one_or_none()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    tarea.completada = completada
    if usuario_id and tarea.usuario_id != usuario_id:
        tarea.usuario_id = usuario_id
    await db.commit()
    await db.refresh(tarea)
    return tarea
