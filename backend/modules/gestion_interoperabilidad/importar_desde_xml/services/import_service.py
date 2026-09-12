import xml.etree.ElementTree as ET
import uuid
import random

async def parsear_xmi(xml_content: str) -> dict:
    root = ET.fromstring(xml_content)
    
    # namespaces
    ns = {
        'uml': 'http://schema.omg.org/spec/UML/2.1',
        'xmi': 'http://schema.omg.org/spec/XMI/2.1'
    }
    
    nodes = []
    relations = []
    
    # Buscar todos los packagedElement
    for elem in root.findall('.//packagedElement'):
        xmi_type = elem.attrib.get('{http://schema.omg.org/spec/XMI/2.1}type')
        if xmi_type == 'uml:Class':
            node_id = elem.attrib.get('{http://schema.omg.org/spec/XMI/2.1}id') or str(uuid.uuid4())
            name = elem.attrib.get('name', 'Clase Importada')
            
            is_table = False
            ext = elem.find('Extension')
            if ext is not None and ext.attrib.get('stereotype') == 'table':
                is_table = True
                
            atributos = []
            for attr in elem.findall('ownedAttribute'):
                attr_name = attr.attrib.get('name', 'attr')
                vis = '+' if attr.attrib.get('visibility') == 'public' else '-'
                
                # Try to extract type
                tipo = 'String'
                type_elem = attr.find('type')
                if type_elem is not None:
                    href = type_elem.attrib.get('href', '')
                    if '#' in href:
                        tipo = href.split('#')[-1]
                
                atributos.append({
                    "id": attr.attrib.get('{http://schema.omg.org/spec/XMI/2.1}id') or str(uuid.uuid4()),
                    "nombre": attr_name,
                    "visibilidad": vis,
                    "tipo": tipo,
                    "version": 0
                })
                
            metodos = []
            for met in elem.findall('ownedOperation'):
                met_name = met.attrib.get('name', 'metodo')
                vis = '+' if met.attrib.get('visibility') == 'public' else '-'
                
                metodos.append({
                    "id": met.attrib.get('{http://schema.omg.org/spec/XMI/2.1}id') or str(uuid.uuid4()),
                    "nombre": met_name,
                    "visibilidad": vis,
                    "parametros": "",
                    "retorno": "void",
                    "version": 0
                })
                
            nodes.append({
                "id": node_id,
                "type": "class",
                "x": random.randint(100, 500),
                "y": random.randint(100, 500),
                "nombre": name,
                "color": "#393E46" if not is_table else "#1a5c3a",
                "atributos": atributos,
                "metodos": metodos,
                "version": 0,
                "estereotipo": "table" if is_table else None
            })
            
        elif xmi_type == 'uml:Association':
            rel_id = elem.attrib.get('{http://schema.omg.org/spec/XMI/2.1}id') or str(uuid.uuid4())
            name = elem.attrib.get('name', '')
            
            ends = elem.findall('ownedEnd')
            if len(ends) == 2:
                src = ends[0].attrib.get('type')
                tgt = ends[1].attrib.get('type')
                
                relations.append({
                    "id": rel_id,
                    "type": "association",
                    "sourceId": src,
                    "targetId": tgt,
                    "label": name,
                    "sourceLabel": "",
                    "targetLabel": "",
                    "version": 0
                })
                
    return {
        "nodes": nodes,
        "relations": relations
    }
