import json
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_salas.cargar_lienzo.repositories.cargar_repository import cargar_lienzo_repository
from backend.modules.gestion_salas.cargar_lienzo.schemas.response import LienzoResponse
from backend.modules.gestion_modelado.models import DiagramElement, DiagramRelation


class CargarLienzoService:
    async def cargar_lienzo(
        self, proyecto_id: int, user: Usuario, db: AsyncSession
    ) -> LienzoResponse:
        proyecto = await cargar_lienzo_repository.obtener_proyecto_con_colaboradores(db, proyecto_id)

        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado."
            )

        colaborador = next(
            (c for c in proyecto.colaboradores if c.usuario_id == user.id), None
        )
        # Si el usuario no es colaborador registrado pero tiene acceso a la sala o es consulta pública
        rol_proyecto = colaborador.rol_proyecto if colaborador else "viewer"

        # Parsear lienzo_json si existe
        lienzo_data = {}
        if proyecto.lienzo_json:
            try:
                lienzo_data = json.loads(proyecto.lienzo_json) if isinstance(proyecto.lienzo_json, str) else proyecto.lienzo_json
            except Exception:
                lienzo_data = {}

        nodes = list(lienzo_data.get("nodes", []))
        relations = list(lienzo_data.get("relations", []))

        # Consolidar elementos persistidos en la tabla diagram_elements
        el_res = await db.execute(select(DiagramElement).where(DiagramElement.proyecto_id == proyecto_id))
        db_elements = el_res.scalars().all()
        existing_node_ids = {str(n.get("id")) for n in nodes if n.get("id") is not None}

        for el in db_elements:
            if str(el.id) not in existing_node_ids:
                c = el.content or {}
                nodes.append({
                    "id": el.id,
                    "type": el.type,
                    "nombre": el.nombre,
                    "color": el.color or "#393E46",
                    "x": el.pos_x or 200,
                    "y": el.pos_y or 200,
                    "width": el.width or 220,
                    "atributos": c.get("atributos", []),
                    "metodos": c.get("metodos", []),
                    "valores": c.get("valores", []),
                    "contenido": c.get("contenido") or c.get("texto"),
                    "version": el.version,
                    "hash": el.hash,
                })

        # Consolidar relaciones persistidas en la tabla diagram_relations
        rel_res = await db.execute(select(DiagramRelation).where(DiagramRelation.proyecto_id == proyecto_id))
        db_relations = rel_res.scalars().all()
        existing_rel_ids = {str(r.get("id")) for r in relations if r.get("id") is not None}

        for rel in db_relations:
            if str(rel.id) not in existing_rel_ids:
                relations.append({
                    "id": rel.id,
                    "type": rel.type,
                    "sourceId": rel.source_id,
                    "targetId": rel.target_id,
                    "label": rel.label or "",
                    "sourceMultiplicity": rel.source_label or "",
                    "targetMultiplicity": rel.target_label or "",
                    "version": rel.version,
                    "hash": rel.hash,
                })

        lienzo_final = json.dumps({"nodes": nodes, "relations": relations})

        return LienzoResponse(
            proyecto_id=proyecto.id,
            proyecto_nombre=proyecto.nombre,
            codigo_acceso=proyecto.codigo_acceso,
            lienzo_json=lienzo_final,
            rol_proyecto=rol_proyecto,
            github_repo_url=proyecto.github_repo_url
        )


cargar_lienzo_service = CargarLienzoService()
