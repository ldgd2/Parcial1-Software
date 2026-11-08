import json
import httpx
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.core.config import settings
from backend.core.websockets.connection_manager import manager
from backend.modules.gestion_proyectos.models import Proyecto
from backend.modules.gestion_proyectos_asistida.repartir_roles.schemas.request import (
    RepartirRolesRequest,
    AsignarRolManualRequest,
)
from backend.modules.gestion_proyectos_asistida.repartir_roles.schemas.response import (
    ColaboradorRolOut,
    RepartirRolesResponse,
)
from backend.modules.gestion_proyectos_asistida.repartir_roles.repositories.roles_repository import (
    obtener_colaboradores_proyecto,
    obtener_usuarios_por_ids,
    asegurar_colaborador_proyecto,
    guardar_roles_colaboradores,
)

ROLES_CATALOG = [
    {
        "rol_ia": "Arquitecto Backend",
        "areas": ["backend", "api", "servicios"],
        "responsabilidades": ["Diseño de controladores REST", "Lógica de negocio", "Integración de servicios"],
    },
    {
        "rol_ia": "Líder Frontend & UI",
        "areas": ["frontend", "interfaz", "movil"],
        "responsabilidades": ["Componentes de interfaz", "Consumo de API", "Experiencia de usuario"],
    },
    {
        "rol_ia": "Especialista Base de Datos",
        "areas": ["base_de_datos", "persistencia", "migraciones"],
        "responsabilidades": ["Modelado relacional", "Optimización de consultas", "Migraciones Flyway"],
    },
    {
        "rol_ia": "Ingeniero de Calidad y Testing",
        "areas": ["testing", "calidad", "seguridad"],
        "responsabilidades": ["Pruebas unitarias", "Validación de contratos", "Auditoría de seguridad"],
    },
]


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


async def _consultar_ia_roles(prompt: str, provider: Optional[str] = None, api_key: Optional[str] = None) -> dict:
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
                                    "Role: Senior Software Team Architect. "
                                    "Assign engineering roles and areas to developers based on UML classes. "
                                    "Output STRICT MINIFIED JSON ONLY: {\"resumen\":str,\"asignaciones\":[{\"usuario_id\":int,\"rol_ia\":str,\"areas\":[],\"responsabilidades\":[],\"clases\":[]}]}"
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
                "X-Title": "UML Diagrammer Team Roles",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Role: Senior Team Architect. Output strictly JSON: {\"resumen\":str,\"asignaciones\":[{\"usuario_id\":int,\"rol_ia\":str,\"areas\":[],\"responsabilidades\":[],\"clases\":[]}]}"
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


async def ejecutar_reparticion_roles(
    req: RepartirRolesRequest,
    db: AsyncSession
) -> RepartirRolesResponse:
    # 1. Cargar proyecto
    result_proj = await db.execute(select(Proyecto).where(Proyecto.id == req.proyecto_id))
    proyecto = result_proj.scalar_one_or_none()
    if not proyecto:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    lienzo_data: dict = {}
    if proyecto.lienzo_json:
        try:
            lienzo_data = json.loads(proyecto.lienzo_json)
        except Exception:
            lienzo_data = {}

    nodos = lienzo_data.get("nodes", []) if isinstance(lienzo_data, dict) else []
    nombres_clases = [n.get("nombre") for n in nodos if n.get("nombre")]

    # 2. Obtener lista de colaboradores
    devs: List[Dict[str, Any]] = []
    if req.colaboradores and len(req.colaboradores) > 0:
        for c in req.colaboradores:
            devs.append({
                "usuario_id": c.usuario_id,
                "nombre": c.nombre,
                "etiquetas": c.etiquetas or ["modelado", "backend", "frontend"]
            })
    else:
        colabs_db = await obtener_colaboradores_proyecto(req.proyecto_id, db)
        uids = [c.usuario_id for c in colabs_db]
        usuarios_map = await obtener_usuarios_por_ids(uids, db)
        for c in colabs_db:
            u = usuarios_map.get(c.usuario_id)
            devs.append({
                "usuario_id": c.usuario_id,
                "nombre": u.nombre if u else f"Dev {c.usuario_id}",
                "etiquetas": u.etiquetas_habilidades if (u and u.etiquetas_habilidades) else ["general"]
            })

    if not devs:
        devs.append({
            "usuario_id": 1,
            "nombre": "Anfitrión",
            "etiquetas": ["backend", "frontend", "modelado"]
        })

    # 3. Consultar IA con prompt denso
    devs_desc = "; ".join(f"ID:{d['usuario_id']}|Nom:{d['nombre']}|Skills:{d.get('etiquetas', [])}" for d in devs)
    clases_desc = ", ".join(nombres_clases[:25]) if nombres_clases else "Entidades Principales"

    prompt = (
        f"Project: {proyecto.nombre}\n"
        f"Classes: [{clases_desc}]\n"
        f"Developers: [{devs_desc}]\n"
        f"Instructions: Assign roles and areas (backend, frontend, base_de_datos, testing). "
        f"Distribute UML classes among developers. "
        f"Format JSON: {{\"resumen\":str,\"asignaciones\":[{{\"usuario_id\":int,\"rol_ia\":str,\"areas\":[\"area1\"],\"responsabilidades\":[\"resp1\"],\"clases\":[\"Clase\"]}}]}}"
    )

    resultado_ia = await _consultar_ia_roles(prompt, req.provider, req.api_key)
    asignaciones_raw = resultado_ia.get("asignaciones", [])

    # Mapeo y validación estricta de IDs
    dev_ids = [d["usuario_id"] for d in devs]
    dev_map = {d["usuario_id"]: d["nombre"] for d in devs}

    roles_finales: List[ColaboradorRolOut] = []
    guardar_db_items: List[Dict[str, Any]] = []

    if asignaciones_raw and len(asignaciones_raw) > 0:
        for idx, item in enumerate(asignaciones_raw):
            raw_uid = item.get("usuario_id")
            uid = raw_uid if raw_uid in dev_ids else dev_ids[idx % len(dev_ids)]
            nombre = dev_map.get(uid, f"Dev {uid}")
            rol = item.get("rol_ia") or "Desarrollador Fullstack"
            areas = item.get("areas") or ["general"]
            resps = item.get("responsabilidades") or ["Implementación y modelado"]
            clases = item.get("clases") or []

            roles_finales.append(ColaboradorRolOut(
                usuario_id=uid,
                nombre=nombre,
                rol_ia=rol,
                areas=areas,
                responsabilidades=resps,
                clases_asignadas=clases
            ))

            guardar_db_items.append({
                "usuario_id": uid,
                "rol_ia": rol,
                "areas": areas,
                "responsabilidades": resps
            })
    else:
        # Fallback heurístico inteligente
        for idx, d in enumerate(devs):
            template = ROLES_CATALOG[idx % len(ROLES_CATALOG)]
            assigned_classes = [c for i, c in enumerate(nombres_clases) if i % len(devs) == idx]
            roles_finales.append(ColaboradorRolOut(
                usuario_id=d["usuario_id"],
                nombre=d["nombre"],
                rol_ia=template["rol_ia"],
                areas=template["areas"],
                responsabilidades=template["responsabilidades"],
                clases_asignadas=assigned_classes
            ))
            guardar_db_items.append({
                "usuario_id": d["usuario_id"],
                "rol_ia": template["rol_ia"],
                "areas": template["areas"],
                "responsabilidades": template["responsabilidades"]
            })

    # 4. Guardar roles y áreas permanentemente en la base de datos (colaboradores_proyecto)
    await guardar_roles_colaboradores(req.proyecto_id, guardar_db_items, db)

    # 5. Actualizar el lienzo_json con los responsables de cada clase
    if nodos:
        class_to_dev = {}
        for r in roles_finales:
            for c_name in r.clases_asignadas:
                class_to_dev[c_name.lower()] = r

        for nodo in nodos:
            c_name = str(nodo.get("nombre") or "").lower()
            if c_name in class_to_dev:
                asig = class_to_dev[c_name]
                nodo["responsable"] = asig.nombre
                nodo["responsabilidades"] = [asig.rol_ia] + asig.areas

        proyecto.lienzo_json = json.dumps(lienzo_data)
        await db.commit()

        # Notificar cambio del diagrama a los clientes conectados
        if proyecto.codigo_acceso:
            await manager.broadcast_to_sala({
                "type": "diagram_event",
                "payload": {"type": "roles_updated", "nodes": nodos}
            }, proyecto.codigo_acceso)

    # 6. Notificar por WebSocket que los roles fueron actualizados
    if proyecto.codigo_acceso:
        await manager.broadcast_to_sala({
            "type": "roles_actualizados",
            "proyecto_id": req.proyecto_id
        }, proyecto.codigo_acceso)

    resumen = resultado_ia.get("resumen") or (
        f"Se repartieron {len(roles_finales)} roles y áreas técnicas exitosamente en el proyecto."
    )

    return RepartirRolesResponse(
        proyecto_id=req.proyecto_id,
        resumen=resumen,
        roles=roles_finales
    )


async def asignar_rol_manualmente(
    req: AsignarRolManualRequest,
    db: AsyncSession
) -> ColaboradorRolOut:
    colab = await asegurar_colaborador_proyecto(req.proyecto_id, req.usuario_id, db)
    colab.rol_ia = req.rol_ia
    colab.areas = req.areas
    colab.responsabilidades = req.responsabilidades or []
    await db.commit()

    u_map = await obtener_usuarios_por_ids([req.usuario_id], db)
    user = u_map.get(req.usuario_id)
    nombre = user.nombre if user else f"Usuario {req.usuario_id}"

    # Notificar cambio por WebSocket
    result_proj = await db.execute(select(Proyecto).where(Proyecto.id == req.proyecto_id))
    proyecto = result_proj.scalar_one_or_none()
    if proyecto and proyecto.codigo_acceso:
        await manager.broadcast_to_sala({
            "type": "roles_actualizados",
            "proyecto_id": req.proyecto_id
        }, proyecto.codigo_acceso)

    return ColaboradorRolOut(
        usuario_id=req.usuario_id,
        nombre=nombre,
        rol_ia=req.rol_ia,
        areas=req.areas,
        responsabilidades=req.responsabilidades or [],
        clases_asignadas=[]
    )


async def listar_roles_proyecto(proyecto_id: int, db: AsyncSession) -> List[ColaboradorRolOut]:
    colabs = await obtener_colaboradores_proyecto(proyecto_id, db)
    uids = [c.usuario_id for c in colabs]
    users_map = await obtener_usuarios_por_ids(uids, db)

    roles_list: List[ColaboradorRolOut] = []
    for c in colabs:
        u = users_map.get(c.usuario_id)
        roles_list.append(ColaboradorRolOut(
            usuario_id=c.usuario_id,
            nombre=u.nombre if u else f"Usuario {c.usuario_id}",
            rol_ia=c.rol_ia,
            areas=c.areas if isinstance(c.areas, list) else [],
            responsabilidades=c.responsabilidades if isinstance(c.responsabilidades, list) else [],
            clases_asignadas=[]
        ))
    return roles_list

