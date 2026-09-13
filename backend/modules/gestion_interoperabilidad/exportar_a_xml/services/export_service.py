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

async def generar_xmi(proyecto_id: int, user: Usuario, db: AsyncSession) -> str:
    result = await db.execute(select(Proyecto).where(Proyecto.id == proyecto_id))
    proyecto = result.scalar_one_or_none()
    
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
        "xmi.id": f"MX_EAID_{proyecto_id}"
    })
    
    owned = ET.SubElement(model, "UML:Namespace.ownedElement")
    
    pkg = ET.SubElement(owned, "UML:Package", attrib={
        "name": "ExportedModel",
        "xmi.id": f"EAPK_{proyecto_id}",
        "isRoot": "false", "isLeaf": "false", "isAbstract": "false", "visibility": "public"
    })
    
    pkg_owned = ET.SubElement(pkg, "UML:Namespace.ownedElement")
    
    diagram = ET.SubElement(content, "UML:Diagram", attrib={
        "name": "ExportedModel",
        "xmi.id": f"EAID_DIAG_{proyecto_id}",
        "diagramType": "ClassDiagram",
        "owner": f"EAPK_{proyecto_id}",
        "toolName": "Enterprise Architect 2.5"
    })
    
    diag_tags = ET.SubElement(diagram, "UML:ModelElement.taggedValue")
    ET.SubElement(diag_tags, "UML:TaggedValue", attrib={"tag": "version", "value": "1.0"})
    ET.SubElement(diag_tags, "UML:TaggedValue", attrib={"tag": "author", "value": "AutoExporter"})
    ET.SubElement(diag_tags, "UML:TaggedValue", attrib={"tag": "package", "value": f"EAPK_{proyecto_id}"})
    ET.SubElement(diag_tags, "UML:TaggedValue", attrib={"tag": "type", "value": "Logical"})
    ET.SubElement(diag_tags, "UML:TaggedValue", attrib={"tag": "EAStyle", "value": "ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;Locked=0;Border=1;HighlightForeign=1;PackageContents=1;SequenceNotes=0;ScalePrintImage=0;PPgs.cx=0;PPgs.cy=0;DocSize.cx=827;DocSize.cy=1169;ShowDetails=0;Orientation=P;Zoom=100;ShowTags=0;OpParams=1;VisibleAttributeDetail=0;ShowOpRetType=1;ShowIcons=1;CollabNums=0;HideProps=0;ShowReqs=0;ShowCons=0;PaperSize=9;HideParents=0;UseAlias=0;HideAtts=0;HideOps=0;HideStereo=0;HideElemStereo=0;ShowTests=0;ShowMaint=0;ConnectorNotation=UML 2.1;ExplicitNavigability=0;ShowShape=1;AllDockable=0;AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;ShowNotes=0;SuppressBrackets=0;SuppConnectorLabels=0;PrintPageHeadFoot=0;ShowAsList=0;"})
    ET.SubElement(diag_tags, "UML:TaggedValue", attrib={"tag": "styleex", "value": "SaveTag=8EF2F3CE;ExcludeRTF=0;DocAll=0;HideQuals=0;AttPkg=1;ShowTests=0;ShowMaint=0;SuppressFOC=1;MatrixActive=0;SwimlanesActive=1;KanbanActive=0;MatrixLineWidth=1;MatrixLineClr=0;MatrixLocked=0;TConnectorNotation=UML 2.1;TExplicitNavigability=0;AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;MDGDgm=;STBLDgm=;ShowNotes=0;VisibleAttributeDetail=0;ShowOpRetType=1;SuppressBrackets=0;SuppConnectorLabels=0;PrintPageHeadFoot=0;ShowAsList=0;SuppressedCompartments=;Theme=:119;"})
    
    diag_elems = ET.SubElement(diagram, "UML:Diagram.element")
    
    duid_map = {}
    
    def get_duid(cid: str) -> str:
        return hashlib.md5(cid.encode('utf-8')).hexdigest()[:8]
    
    for i, cls in enumerate(classes):
        cls_id = cls.get('id', '')
        duid = get_duid(cls_id)
        duid_map[cls_id] = duid
        
        cls_type = cls.get('type', 'class')
        xmi_type_map = ClassMapper.get_export_type_map()
        xmi_type = xmi_type_map.get(cls_type, 'uml:Class')
        mapper = ClassMapper.create(xmi_type)
        mapper.to_xml(cls, pkg_owned, proyecto_id)
        
        x = int(cls.get('x', 100))
        y = int(cls.get('y', 100))
        w = int(cls.get('width', 220))
        
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
        
    for i, rel in enumerate(relations):
        rel_type = rel.get('type', 'association')
        xmi_type_map = RelationBaseMapper.get_export_type_map()
        xmi_type = xmi_type_map.get(rel_type, 'uml:Association')
        mapper = RelationBaseMapper.create(xmi_type)
        mapper.to_xml(rel, pkg_owned, diag_elems, duid_map, i)
        
    ET.SubElement(xmi, "XMI.difference")
    ext = ET.SubElement(xmi, "XMI.extensions", attrib={"xmi.extender": "Enterprise Architect 2.5"})
    ET.SubElement(ext, "EAModel.paramSub")

    xml_str = ET.tostring(xmi, encoding='utf-8', xml_declaration=True).decode('utf-8')
    return xml_str
