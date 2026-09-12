import xml.etree.ElementTree as ET
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.modules.gestion_proyectos.models import Proyecto
from backend.modules.gestion_usuarios.models import Usuario

async def generar_xmi(proyecto_id: int, user: Usuario, db: AsyncSession) -> str:
    # 1. Obtener el lienzo actual del proyecto
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
    
    # 2. Construir XML (XMI 1.1 / UML 1.3 para EA)
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
    
    for cls in classes:
        cls_id = cls.get('id', '')
        class_elem = ET.SubElement(pkg_owned, "UML:Class", attrib={
            "name": str(cls.get('nombre', 'Unnamed')),
            "xmi.id": f"EAID_{cls_id}",
            "visibility": "public",
            "namespace": f"EAPK_{proyecto_id}",
            "isRoot": "false", "isLeaf": "false", "isAbstract": "false", "isActive": "false"
        })
        
        tags = ET.SubElement(class_elem, "UML:ModelElement.taggedValue")
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "isSpecification", "value": "false"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "ea_stype", "value": "Class"})
        
        if cls.get('estereotipo') == 'table':
            ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "stereotype", "value": "table"})
            
        if cls.get('atributos') or cls.get('metodos'):
            feature = ET.SubElement(class_elem, "UML:Classifier.feature")
            for attr in cls.get('atributos', []):
                attr_elem = ET.SubElement(feature, "UML:Attribute", attrib={
                    "name": str(attr.get('nombre', '')),
                    "visibility": "public" if attr.get('visibilidad') == '+' else "private",
                    "ownerScope": "instance",
                    "targetScope": "instance"
                })
                attr_tags = ET.SubElement(attr_elem, "UML:ModelElement.taggedValue")
                ET.SubElement(attr_tags, "UML:TaggedValue", attrib={"tag": "type", "value": str(attr.get('tipo', 'int'))})
                
            for met in cls.get('metodos', []):
                op_elem = ET.SubElement(feature, "UML:Operation", attrib={
                    "name": str(met.get('nombre', '')),
                    "visibility": "public" if met.get('visibilidad') == '+' else "private",
                    "ownerScope": "instance",
                    "isQuery": "false",
                    "concurrency": "sequential"
                })

    for rel in relations:
        rel_type = rel.get('type', 'association')
        rel_id = rel.get('id', '')
        
        def parse_mult(val):
            val = str(val).strip()
            if '..' in val:
                parts = val.split('..', 1)
                return parts[0], parts[1]
            return val, val
        
        if rel_type in ('inheritance', 'realization', 'dependency'):
            elem_name = "UML:Generalization" if rel_type == 'inheritance' else "UML:Dependency"
            ea_type = "Generalization" if rel_type == 'inheritance' else ("Realisation" if rel_type == 'realization' else "Dependency")
            
            attribs = {
                "xmi.id": f"EAID_{rel_id}",
                "visibility": "public",
                "isRoot": "false", "isLeaf": "false", "isAbstract": "false"
            }
            if rel_type == 'inheritance':
                attribs["child"] = f"EAID_{rel.get('sourceId', '')}"
                attribs["parent"] = f"EAID_{rel.get('targetId', '')}"
            else:
                attribs["client"] = f"EAID_{rel.get('sourceId', '')}"
                attribs["supplier"] = f"EAID_{rel.get('targetId', '')}"
                
            elem = ET.SubElement(pkg_owned, elem_name, attrib=attribs)
            
            tags = ET.SubElement(elem, "UML:ModelElement.taggedValue")
            ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "ea_type", "value": ea_type})
            ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "direction", "value": "Source -> Destination"})
            if rel_type == 'realization':
                ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "stereotype", "value": "realize"})
                
        else:
            assoc = ET.SubElement(pkg_owned, "UML:Association", attrib={
                "xmi.id": f"EAID_{rel_id}",
                "visibility": "public",
                "isRoot": "false", "isLeaf": "false", "isAbstract": "false"
            })
            
            ea_type = "Aggregation" if rel_type in ('aggregation', 'composition') else "Association"
            tags = ET.SubElement(assoc, "UML:ModelElement.taggedValue")
            ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "ea_type", "value": ea_type})
            if rel_type == 'directed':
                ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "direction", "value": "Source -> Destination"})
            
            if rel.get('label'):
                ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "mt", "value": str(rel.get('label'))})
            if rel.get('sourceLabel'):
                ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "lb", "value": str(rel.get('sourceLabel'))})
            if rel.get('targetLabel'):
                ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "rb", "value": str(rel.get('targetLabel'))})
            
            conn = ET.SubElement(assoc, "UML:Association.connection")
            
            agg_src = "none"
            if rel_type == 'aggregation': agg_src = "shared"
            if rel_type == 'composition': agg_src = "composite"
            
            end1_attrib = {
                "visibility": "public", "aggregation": agg_src, "isOrdered": "false", "targetScope": "instance", "changeable": "none", "isNavigable": "false" if rel_type == 'directed' else "true",
                "type": f"EAID_{rel.get('sourceId', '')}"
            }
            if rel.get('sourceLabel'):
                end1_attrib["multiplicity"] = str(rel.get('sourceLabel'))
                
            end1 = ET.SubElement(conn, "UML:AssociationEnd", attrib=end1_attrib)
            
            if rel.get('sourceLabel'):
                l, u = parse_mult(rel.get('sourceLabel'))
                mult = ET.SubElement(end1, "UML:AssociationEnd.multiplicity")
                mult_range = ET.SubElement(mult, "UML:Multiplicity")
                mult_range_comp = ET.SubElement(mult_range, "UML:Multiplicity.range")
                ET.SubElement(mult_range_comp, "UML:MultiplicityRange", attrib={"lower": l, "upper": u})
            
            end2_attrib = {
                "visibility": "public", "aggregation": "none", "isOrdered": "false", "targetScope": "instance", "changeable": "none", "isNavigable": "true",
                "type": f"EAID_{rel.get('targetId', '')}"
            }
            if rel.get('targetLabel'):
                end2_attrib["multiplicity"] = str(rel.get('targetLabel'))
                
            end2 = ET.SubElement(conn, "UML:AssociationEnd", attrib=end2_attrib)
            
            if rel.get('targetLabel'):
                l, u = parse_mult(rel.get('targetLabel'))
                mult = ET.SubElement(end2, "UML:AssociationEnd.multiplicity")
                mult_range = ET.SubElement(mult, "UML:Multiplicity")
                mult_range_comp = ET.SubElement(mult_range, "UML:Multiplicity.range")
                ET.SubElement(mult_range_comp, "UML:MultiplicityRange", attrib={"lower": l, "upper": u})
        
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
    
    import hashlib
    duid_map = {}
    
    for i, cls in enumerate(classes):
        cls_id = cls.get('id', '')
        duid = hashlib.md5(cls_id.encode('utf-8')).hexdigest()[:8].upper()
        duid_map[cls_id] = duid
        
        x = int(cls.get('x', 100))
        y = int(cls.get('y', 100))
        w = int(cls.get('width', 150))
        h = 100
        ET.SubElement(diag_elems, "UML:DiagramElement", attrib={
            "geometry": f"Left={x};Top={y};Right={x+w};Bottom={y+h};",
            "subject": f"EAID_{cls_id}",
            "seqno": str(i+1),
            "style": f"DUID={duid};"
        })
        
    for i, rel in enumerate(relations):
        rel_id = rel.get('id', '')
        src_id = rel.get('sourceId', '')
        tgt_id = rel.get('targetId', '')
        
        soid = duid_map.get(src_id, '')
        eoid = duid_map.get(tgt_id, '')
        
        src_lbl = str(rel.get('sourceLabel') or '').replace(';', ',')
        tgt_lbl = str(rel.get('targetLabel') or '').replace(';', ',')
        mid_lbl = str(rel.get('label') or '').replace(';', ',')
        
        geometry_str = f"SX=0;SY=0;EX=0;EY=0;EDGE=2;$LLB={src_lbl};LLT=;LMT={mid_lbl};LMB=;LRT=;LRB={tgt_lbl};IRHS=;ILHS=;Path=;"
        
        ET.SubElement(diag_elems, "UML:DiagramElement", attrib={
            "geometry": geometry_str,
            "subject": f"EAID_{rel_id}",
            "style": f"Mode=3;EOID={eoid};SOID={soid};Color=-1;LWidth=0;Hidden=0;"
        })
        
    ET.SubElement(xmi, "XMI.difference")
    ext = ET.SubElement(xmi, "XMI.extensions", attrib={"xmi.extender": "Enterprise Architect 2.5"})
    ET.SubElement(ext, "EAModel.paramSub")

    # Return XML as string
    xml_str = ET.tostring(xmi, encoding='utf-8', xml_declaration=True).decode('utf-8')
    return xml_str
