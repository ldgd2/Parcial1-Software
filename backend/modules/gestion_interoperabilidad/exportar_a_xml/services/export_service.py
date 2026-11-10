import xml.etree.ElementTree as ET
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.modules.gestion_proyectos.models import Proyecto
from backend.modules.gestion_usuarios.models import Usuario
from backend.modules.gestion_interoperabilidad.shared.xmi.elements.class_mapper import ClassMapper
from backend.modules.gestion_interoperabilidad.shared.xmi.relations.relation_base import RelationBaseMapper
import backend.modules.gestion_interoperabilidad.shared.xmi.elements
import backend.modules.gestion_interoperabilidad.shared.xmi.relations
import hashlib
import re
import uuid
from backend.modules.gestion_interoperabilidad.shared.xmi.relations.create_mapper import CreateMapper
from backend.modules.gestion_interoperabilidad.shared.xmi.relations.send_mapper import SendMapper
from backend.modules.gestion_interoperabilidad.shared.xmi.relations.delegate_mapper import DelegateMapper
from backend.modules.gestion_interoperabilidad.shared.xmi.relations.assembly_mapper import AssemblyMapper

_GUID_EA = re.compile(r'^[0-9A-F]{8}_[0-9A-F]{4}_[0-9A-F]{4}_[0-9A-F]{4}_[0-9A-F]{12}$')
# Relaciones que comparten etiqueta XMI con otra y necesitan su mapper propio
_MAPPER_RELACION = {'create': CreateMapper, 'send': SendMapper, 'delegate': DelegateMapper, 'assembly': AssemblyMapper}


def _guid_ea(valor: str) -> str:
    """EA interpreta todo xmi.id 'EAID_xxx' como un GUID con guiones bajos
    (EAID_XXXXXXXX_XXXX_XXXX_XXXX_XXXXXXXXXXXX). Los ids del lienzo ('e2e-sfy7q3qb', 'node-…')
    no lo son, así que se convierten de forma determinista para que clases y relaciones
    sigan apuntándose entre sí."""
    valor = str(valor or '')
    if _GUID_EA.match(valor):
        return valor
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"diagramador:{valor}")).upper().replace('-', '_')


async def generar_xmi(proyecto_id: int, user: Usuario, db: AsyncSession) -> str:
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar_one_or_none()
    nombre_paquete = (proyecto.nombre if proyecto and proyecto.nombre else "ExportedModel")

    if not proyecto or not proyecto.lienzo_json:
        classes = []
        relations = []
    else:
        import json
        try:
            lienzo = json.loads(proyecto.lienzo_json) if isinstance(proyecto.lienzo_json, str) else proyecto.lienzo_json
            classes = lienzo.get('nodes', [])
            relations = lienzo.get('relations', [])
        except Exception:
            classes = []
            relations = []

    # Copias con ids en formato GUID de EA (no se toca el lienzo guardado)
    classes = [dict(c, id=_guid_ea(c.get('id', ''))) for c in classes if isinstance(c, dict)]
    relations = [dict(r, id=_guid_ea(r.get('id', '')), sourceId=_guid_ea(r.get('sourceId', '')),
                      targetId=_guid_ea(r.get('targetId', '')))
                 for r in relations if isinstance(r, dict)]
    model_id = f"MX_EAID_{_guid_ea(f'modelo-{proyecto_id}')}"
    paquete_id = f"EAPK_{_guid_ea(f'paquete-{proyecto_id}')}"
    diagrama_id = f"EAID_{_guid_ea(f'diagrama-{proyecto_id}')}"

    xmi = ET.Element("XMI", attrib={
        "xmi.version": "1.1",
        "xmlns:UML": "omg.org/UML1.3"
    })
    
    header = ET.SubElement(xmi, "XMI.header")
    doc = ET.SubElement(header, "XMI.documentation")
    ET.SubElement(doc, "XMI.exporter").text = "Enterprise Architect"
    ET.SubElement(doc, "XMI.exporterVersion").text = "2.5"
    
    content = ET.SubElement(xmi, "XMI.content")
    
    model = ET.SubElement(content, "UML:Model", attrib={
        "name": "EA Model",
        "xmi.id": model_id
    })

    owned = ET.SubElement(model, "UML:Namespace.ownedElement")

    pkg = ET.SubElement(owned, "UML:Package", attrib={
        "name": nombre_paquete,
        "xmi.id": paquete_id,
        "isRoot": "false", "isLeaf": "false", "isAbstract": "false", "visibility": "public"
    })

    pkg_owned = ET.SubElement(pkg, "UML:Namespace.ownedElement")

    diagram = ET.SubElement(content, "UML:Diagram", attrib={
        "name": nombre_paquete,
        "xmi.id": diagrama_id,
        "diagramType": "ClassDiagram",
        "owner": paquete_id,
        "toolName": "Enterprise Architect 2.5"
    })

    diag_tags = ET.SubElement(diagram, "UML:ModelElement.taggedValue")
    ET.SubElement(diag_tags, "UML:TaggedValue", attrib={"tag": "version", "value": "1.0"})
    ET.SubElement(diag_tags, "UML:TaggedValue", attrib={"tag": "author", "value": "AutoExporter"})
    ET.SubElement(diag_tags, "UML:TaggedValue", attrib={"tag": "package", "value": paquete_id})
    ET.SubElement(diag_tags, "UML:TaggedValue", attrib={"tag": "type", "value": "Logical"})
    ET.SubElement(diag_tags, "UML:TaggedValue", attrib={"tag": "EAStyle", "value": "ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;Locked=0;Border=1;HighlightForeign=1;PackageContents=1;SequenceNotes=0;ScalePrintImage=0;PPgs.cx=0;PPgs.cy=0;DocSize.cx=827;DocSize.cy=1169;ShowDetails=0;Orientation=P;Zoom=100;ShowTags=0;OpParams=1;VisibleAttributeDetail=0;ShowOpRetType=1;ShowIcons=1;CollabNums=0;HideProps=0;ShowReqs=0;ShowCons=0;PaperSize=9;HideParents=0;UseAlias=0;HideAtts=0;HideOps=0;HideStereo=0;HideElemStereo=0;ShowTests=0;ShowMaint=0;ConnectorNotation=UML 2.1;ExplicitNavigability=0;ShowShape=1;AllDockable=0;AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;ShowNotes=0;SuppressBrackets=0;SuppConnectorLabels=0;PrintPageHeadFoot=0;ShowAsList=0;"})
    ET.SubElement(diag_tags, "UML:TaggedValue", attrib={"tag": "styleex", "value": "SaveTag=8EF2F3CE;ExcludeRTF=0;DocAll=0;HideQuals=0;AttPkg=1;ShowTests=0;ShowMaint=0;SuppressFOC=1;MatrixActive=0;SwimlanesActive=1;KanbanActive=0;MatrixLineWidth=1;MatrixLineClr=0;MatrixLocked=0;TConnectorNotation=UML 2.1;TExplicitNavigability=0;AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;MDGDgm=;STBLDgm=;ShowNotes=0;VisibleAttributeDetail=0;ShowOpRetType=1;SuppressBrackets=0;SuppConnectorLabels=0;PrintPageHeadFoot=0;ShowAsList=0;SuppressedCompartments=;Theme=:119;"})
    
    diag_elems = ET.SubElement(diagram, "UML:Diagram.element")
    
    duid_map = {}
    tipos = {}  # tipo de atributo -> xmi.id del UML:DataType declarado al final

    def get_duid(cid: str) -> str:
        return hashlib.md5(cid.encode('utf-8')).hexdigest()[:8].upper()

    for i, cls in enumerate(classes):
        cls_id = cls.get('id', '')
        duid = get_duid(cls_id)
        duid_map[cls_id] = duid

        # El mapper se elige por el tipo del nodo. Antes se buscaba por etiqueta XMI y toda
        # clase ('uml:Class') caía en DataTypeMapper: EA la importaba como DataType.
        mapper = ClassMapper.for_node_type(cls.get('type', 'class'))
        mapper.to_xml(cls, pkg_owned, proyecto_id, paquete_id=paquete_id,
                      paquete_nombre=nombre_paquete, tipos=tipos)

        x = int(float(cls.get('x') or 100))
        y = int(float(cls.get('y') or 100))
        w = int(float(cls.get('width') or 220))
        
        h = 45 + len(cls.get('atributos', [])) * 28 + len(cls.get('metodos', [])) * 28 + 40
        if cls.get('type') == 'note': h = 90
        elif cls.get('type') == 'enum': h = 45 + len(cls.get('valores', [])) * 28 + 20
        elif cls.get('type') in ['part', 'port', 'expose_interface']: h = 60
        
        ET.SubElement(diag_elems, "UML:DiagramElement", attrib={
            "geometry": f"Left={x};Top={y};Right={x+w};Bottom={y+h};",
            "subject": f"EAID_{cls_id}",
            "seqno": str(i+1),
            "style": f"DUID={duid};"
        })
        
    ids_clases = set(duid_map)
    for i, rel in enumerate(relations):
        # Una relación cuyo extremo no existe deja una referencia rota y EA rechaza la importación
        if rel['sourceId'] not in ids_clases or rel['targetId'] not in ids_clases:
            continue
        rel_type = rel.get('type', 'association')
        if rel_type in _MAPPER_RELACION:
            mapper = _MAPPER_RELACION[rel_type]()
        else:
            xmi_type_map = RelationBaseMapper.get_export_type_map()
            xmi_type = xmi_type_map.get(rel_type, 'uml:Association')
            mapper = RelationBaseMapper.create(xmi_type)
        mapper.to_xml(rel, pkg_owned, diag_elems, duid_map, i)

    # Tipos de los atributos: cada <UML:Classifier xmi.idref="eaxmiidN"/> debe resolver a un
    # elemento existente (antes todos apuntaban a "eaxmiid0", que no estaba definido).
    pos_diagrama = list(content).index(diagram)
    for nombre_tipo, tipo_id in tipos.items():
        content.insert(pos_diagrama, ET.Element("UML:DataType", attrib={
            "xmi.id": tipo_id, "name": nombre_tipo, "visibility": "private",
            "isRoot": "false", "isLeaf": "false", "isAbstract": "false"
        }))
        pos_diagrama += 1

    ET.SubElement(xmi, "XMI.difference")
    ext = ET.SubElement(xmi, "XMI.extensions", attrib={"xmi.extender": "Enterprise Architect 2.5"})
    ET.SubElement(ext, "EAModel.paramSub")

    xml_str = ET.tostring(xmi, encoding='utf-8', xml_declaration=True).decode('utf-8')
    return xml_str
