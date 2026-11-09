import json
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.core.config import settings
from backend.core.websockets.connection_manager import manager
from backend.modules.gestion_proyectos.models import Proyecto, ColaboradorProyecto
from backend.modules.gestion_usuarios.models import TareaIA, Usuario
from backend.modules.gestion_proyectos_asistida.repartir_tareas.schemas.request import (
    RepartirTareasRequest,
    CrearTareaRequest,
)
from backend.modules.gestion_proyectos_asistida.repartir_tareas.schemas.response import (
    TareaResponse,
    RepartirTareasResponse,
)
from backend.modules.gestion_proyectos_asistida.repartir_tareas.repositories.tareas_repository import (
    obtener_tareas_usuario,
    obtener_todas_tareas_proyecto,
    insertar_tareas,
    marcar_tarea_estado,
    borrar_tarea,
)


def _clean_json(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    import re
    match = re.search(r'(\{[\s\S]*\})', cleaned)
    if match:
        return match.group(1).strip()
    return cleaned


async def _anfitrion_id(proyecto_id: int, db: AsyncSession) -> Optional[int]:
    """Usuario anfitrión del proyecto (Proyecto no tiene `creador_id`; el dueño es el colaborador anfitrión)."""
    from backend.modules.gestion_proyectos.models import ColaboradorProyecto
    res = await db.execute(
        select(ColaboradorProyecto.usuario_id)
        .where(ColaboradorProyecto.proyecto_id == proyecto_id, ColaboradorProyecto.rol_proyecto == "anfitrion")
        .limit(1)
    )
    return res.scalar_one_or_none()


async def _llamar_ia_tareas(prompt: str, provider: Optional[str] = None, api_key: Optional[str] = None) -> dict:
    target_provider = (provider or settings.AI_PROVIDER or "kimi").lower().strip()
    if target_provider == "openroute":
        target_provider = "openrouter"

    # 1. Moonshot / KIMI
    if target_provider == "kimi" or (not provider and settings.KIMI_API):
        key = api_key or settings.KIMI_API
        if key:
            primary_model = settings.KIMI_MODEL or "kimi-k3.1-pro"
            endpoints_to_try = [
                ("https://api.moonshot.ai/v1/chat/completions", primary_model, 1.0 if "kimi-k" in primary_model else 0.1),
                ("https://api.moonshot.ai/v1/chat/completions", "kimi-k3", 1.0),
                ("https://api.moonshot.cn/v1/chat/completions", "moonshot-v1-8k", 0.1),
            ]

            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                for url, model_name, temp in endpoints_to_try:
                    payload = {
                        "model": model_name,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "Role: Senior Agile Lead. Distribute actionable development & modeling tasks. "
                                    "Output STRICT MINIFIED JSON ONLY: "
                                    "{\"tareas\":[{\"usuario_id\":int,\"tipo\":\"diagrama\"|\"desarrollo\",\"area\":str,\"titulo\":str,\"descripcion\":str,\"orden\":int}]}"
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": temp,
                        "max_tokens": 4096,
                        "response_format": {"type": "json_object"},
                    }

                    if "kimi-k" in model_name:
                        payload["reasoning_effort"] = "low"

                    try:
                        res = await client.post(url, json=payload, headers=headers)
                        if res.status_code == 200:
                            data = res.json()
                            msg = data["choices"][0]["message"]
                            raw = msg.get("content") or ""
                            if not raw and "reasoning_content" in msg:
                                raw = msg["reasoning_content"]
                            cleaned = _clean_json(raw)
                            if cleaned:
                                return json.loads(cleaned)
                    except Exception:
                        continue

    # 2. OpenRouter
    if target_provider == "openrouter" or (not provider and settings.OPENROUTE_API):
        key = api_key or settings.OPENROUTE_API
        if key:
            model = settings.OPENROUTER_MODEL or "google/gemini-2.0-flash-exp:free"
            headers = {
                "Authorization": f"Bearer {key}",
                "HTTP-Referer": "http://localhost:5173",
                "X-Title": "UML Diagrammer Team Tasks",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Role: Senior Agile Lead. Distribute actionable development & modeling tasks. Output STRICT MINIFIED JSON: {\"tareas\":[{\"usuario_id\":int,\"tipo\":\"diagrama\"|\"desarrollo\",\"area\":str,\"titulo\":str,\"descripcion\":str,\"orden\":int}]}"
                    },
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"}
            }
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    res = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        raw = data["choices"][0]["message"]["content"]
                        cleaned = _clean_json(raw)
                        if cleaned:
                            return json.loads(cleaned)
            except Exception:
                pass

    # 3. Google Gemini
    key_gemini = api_key if target_provider == "gemini" else (settings.GEMINI_API or api_key)
    if key_gemini:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key_gemini}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1, "maxOutputTokens": 4096},
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    raw = data["candidates"][0]["content"]["parts"][0]["text"]
                    cleaned = _clean_json(raw)
                    if cleaned:
                        return json.loads(cleaned)
        except Exception:
            pass

    return {}


async def ejecutar_reparticion_tareas(
    req: RepartirTareasRequest,
    db: AsyncSession
) -> RepartirTareasResponse:
    # 1. Cargar proyecto
    result_proj = await db.execute(select(Proyecto).where(Proyecto.id == req.proyecto_id))
    proyecto = result_proj.scalar_one_or_none()
    if not proyecto:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Obtener usuarios válidos en la base de datos para no violar Foreign Key
    res_all_users = await db.execute(select(Usuario.id))
    valid_uids = set(res_all_users.scalars().all())
    anfitrion_id = await _anfitrion_id(proyecto.id, db)
    default_uid = anfitrion_id if anfitrion_id in valid_uids else (next(iter(valid_uids)) if valid_uids else 1)

    # 2. Cargar colaboradores y sus roles guardados en el proyecto
    result_colabs = await db.execute(
        select(ColaboradorProyecto).where(ColaboradorProyecto.proyecto_id == req.proyecto_id)
    )
    colabs = list(result_colabs.scalars().all())

    uids = [c.usuario_id for c in colabs if c.usuario_id in valid_uids]
    usuarios_map: Dict[int, Usuario] = {}
    if uids:
        res_u = await db.execute(select(Usuario).where(Usuario.id.in_(uids)))
        usuarios_map = {u.id: u for u in res_u.scalars().all()}

    devs_info: List[Dict[str, Any]] = []
    if req.colaboradores and len(req.colaboradores) > 0:
        for c in req.colaboradores:
            target_uid = c.usuario_id if c.usuario_id in valid_uids else default_uid
            devs_info.append({
                "usuario_id": target_uid,
                "nombre": c.nombre,
                "rol_ia": c.rol_ia or "Desarrollador",
                "areas": c.areas or ["general"]
            })
    else:
        for c in colabs:
            target_uid = c.usuario_id if c.usuario_id in valid_uids else default_uid
            u = usuarios_map.get(target_uid)
            devs_info.append({
                "usuario_id": target_uid,
                "nombre": u.nombre if u else f"Dev {target_uid}",
                "rol_ia": c.rol_ia or "Desarrollador",
                "areas": c.areas if isinstance(c.areas, list) and c.areas else ["general"]
            })

    if not devs_info:
        devs_info.append({
            "usuario_id": default_uid,
            "nombre": "Anfitrión",
            "rol_ia": "Líder Técnico",
            "areas": ["backend", "frontend", "modelado"]
        })

    # Cargar historial de tareas para no duplicar
    historial = await obtener_todas_tareas_proyecto(req.proyecto_id, db)
    historial_titulos = set(t.titulo.lower() for t in historial)

    # 3. Construir prompt telegráfico
    devs_str = "; ".join(
        f"ID:{d['usuario_id']}|Nom:{d['nombre']}|Rol:{d.get('rol_ia', 'Dev')}|Areas:{d.get('areas', [])}"
        for d in devs_info
    )

    descripcion = req.descripcion_proyecto or proyecto.descripcion or proyecto.nombre or "Sistema de software"

    prompt = (
        f"Project: {descripcion}\n"
        f"Team: [{devs_str}]\n"
        f"Instructions: Create concrete development & modeling tasks assigned according to each member's Role & Areas. "
        f"Field 'tipo': 'diagrama' | 'desarrollo'. "
        f"Field 'area': 'backend' | 'frontend' | 'base_de_datos' | 'testing' | 'modelado'. "
        f"Output JSON: {{\"tareas\":[{{\"usuario_id\":int,\"tipo\":str,\"area\":str,\"titulo\":str,\"descripcion\":str,\"orden\":int}}]}}"
    )

    resultado_ia = await _llamar_ia_tareas(prompt, req.provider, req.api_key)
    tareas_raw: List[Dict[str, Any]] = resultado_ia.get("tareas", [])

    dev_ids = [d["usuario_id"] for d in devs_info]
    dev_id_set = set(dev_ids)

    nuevas_entidades: List[TareaIA] = []

    if tareas_raw and len(tareas_raw) > 0:
        for idx, item in enumerate(tareas_raw):
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

            titulo = str(item.get("titulo") or f"Tarea {idx + 1}").strip()
            if titulo.lower() in historial_titulos:
                continue

            target_uid = uid if uid in valid_uids else default_uid

            nueva_tarea = TareaIA(
                proyecto_id=req.proyecto_id,
                usuario_id=target_uid,
                tipo=item.get("tipo", "desarrollo"),
                area=item.get("area", "general"),
                titulo=titulo,
                descripcion=item.get("descripcion"),
                completada=False,
                orden=item.get("orden", idx + 1),
            )
            nuevas_entidades.append(nueva_tarea)
    else:
        # Fallback heurístico si no responde la IA
        for idx, d in enumerate(devs_info):
            area_principal = d["areas"][0] if d.get("areas") else "backend"
            target_uid = d["usuario_id"] if d["usuario_id"] in valid_uids else default_uid
            nuevas_entidades.append(TareaIA(
                proyecto_id=req.proyecto_id,
                usuario_id=target_uid,
                tipo="diagrama" if idx == 0 else "desarrollo",
                area=area_principal,
                titulo=f"Implementar módulos de {area_principal.capitalize()}",
                descripcion=f"Diseño y construcción de componentes correspondientes al área de {area_principal}.",
                completada=False,
                orden=idx + 1,
            ))

    # Con persistir=False la IA solo propone: las tareas se crean al aprobar la propuesta
    if req.persistir:
        if nuevas_entidades:
            await insertar_tareas(nuevas_entidades, db)

        # Notificar WebSocket para sincronización en tiempo real
        if proyecto.codigo_acceso:
            await manager.broadcast_to_sala({"type": "tareas_actualizadas"}, proyecto.codigo_acceso)

    resp_tareas = [
        TareaResponse(
            id=t.id,
            proyecto_id=t.proyecto_id,
            usuario_id=t.usuario_id,
            tipo=t.tipo,
            area=t.area or "general",
            titulo=t.titulo,
            descripcion=t.descripcion,
            completada=t.completada,
            orden=t.orden,
        )
        for t in nuevas_entidades
    ]

    return RepartirTareasResponse(
        proyecto_id=req.proyecto_id,
        tareas_generadas=len(resp_tareas),
        tareas=resp_tareas,
        resumen=(
            f"Se generaron y asignaron {len(resp_tareas)} tareas correctamente en el proyecto."
            if req.persistir else
            f"La IA propone {len(resp_tareas)} tareas para el equipo."
        ),
    )


async def listar_mis_tareas(proyecto_id: int, current_user_id: Optional[int], db: AsyncSession) -> List[TareaResponse]:
    if not current_user_id:
        todas = await obtener_todas_tareas_proyecto(proyecto_id, db)
        return [TareaResponse.model_validate(t) for t in todas]

    tareas = await obtener_tareas_usuario(proyecto_id, current_user_id, db)
    if not tareas:
        # Si no tiene tareas individuales asignadas, retornar las tareas de todo el proyecto
        todas = await obtener_todas_tareas_proyecto(proyecto_id, db)
        return [TareaResponse.model_validate(t) for t in todas]

    return [TareaResponse.model_validate(t) for t in tareas]


async def listar_todas_tareas(proyecto_id: int, db: AsyncSession) -> List[TareaResponse]:
    tareas = await obtener_todas_tareas_proyecto(proyecto_id, db)
    return [TareaResponse.model_validate(t) for t in tareas]


async def cambiar_estado_tarea(tarea_id: int, completada: bool, db: AsyncSession) -> TareaResponse:
    tarea = await marcar_tarea_estado(tarea_id, completada, db)
    if not tarea:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    # Notificar cambio por WebSocket
    result = await db.execute(select(Proyecto).where(Proyecto.id == tarea.proyecto_id))
    proyecto = result.scalar_one_or_none()
    if proyecto and proyecto.codigo_acceso:
        await manager.broadcast_to_sala({"type": "tareas_actualizadas"}, proyecto.codigo_acceso)

    return TareaResponse.model_validate(tarea)


async def registrar_tarea_manual(req: CrearTareaRequest, db: AsyncSession) -> TareaResponse:
    # Validar que el usuario_id exista para prevenir violaciones de llave foránea
    res_u = await db.execute(select(Usuario.id).where(Usuario.id == req.usuario_id))
    valid_uid = res_u.scalar_one_or_none()
    if not valid_uid:
        valid_uid = await _anfitrion_id(req.proyecto_id, db)
        if not valid_uid:
            first_u = await db.execute(select(Usuario.id).limit(1))
            valid_uid = first_u.scalar_one_or_none() or 1

    nueva = TareaIA(
        proyecto_id=req.proyecto_id,
        usuario_id=valid_uid,
        tipo=req.tipo or "desarrollo",
        area=req.area or "general",
        titulo=req.titulo,
        descripcion=req.descripcion,
        completada=False,
        orden=req.orden or 0,
    )
    guardadas = await insertar_tareas([nueva], db)
    t = guardadas[0]

    result = await db.execute(select(Proyecto).where(Proyecto.id == req.proyecto_id))
    proyecto = result.scalar_one_or_none()
    if proyecto and proyecto.codigo_acceso:
        await manager.broadcast_to_sala({"type": "tareas_actualizadas"}, proyecto.codigo_acceso)

    return TareaResponse.model_validate(t)


async def suprimir_tarea(tarea_id: int, db: AsyncSession) -> dict:
    exito = await borrar_tarea(tarea_id, db)
    if not exito:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return {"ok": True, "tarea_id": tarea_id}

