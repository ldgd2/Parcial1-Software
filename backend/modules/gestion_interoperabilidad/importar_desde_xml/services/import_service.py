import xml.etree.ElementTree as ET
from backend.modules.gestion_interoperabilidad.shared.xmi.elements.class_mapper import ClassMapper
from backend.modules.gestion_interoperabilidad.shared.xmi.relations.relation_base import RelationBaseMapper
import backend.modules.gestion_interoperabilidad.shared.xmi.elements
import backend.modules.gestion_interoperabilidad.shared.xmi.relations

async def parsear_xmi(xml_content: str) -> dict:
    try:
        root = ET.fromstring(xml_content)
    except Exception:
        return {"nodes": [], "relations": []}
    
    nodes = []
    relations = []
    
    valid_tags = ClassMapper.get_supported_tags() + RelationBaseMapper.get_supported_tags() + ['packagedElement']
    
    geometries = {}
    for elem in root.iter():
        if elem.tag.endswith('DiagramElement'):
            subject = elem.attrib.get('subject', '')
            geometry = elem.attrib.get('geometry', '')
            if subject and geometry:
                parts = {}
                for p in geometry.split(';'):
                    if '=' in p:
                        k, v = p.split('=', 1)
                        parts[k.strip().lower()] = v.strip()
                try:
                    left = int(parts.get('left', parts.get('l', 0)))
                    top = int(parts.get('top', parts.get('t', 0)))
                    right = int(parts.get('right', parts.get('r', 0)))
                    bottom = int(parts.get('bottom', parts.get('b', 0)))
                    
                    w_val = abs(right - left)
                    h_val = abs(bottom - top)
                    if w_val == 0: w_val = 220
                    if h_val == 0: h_val = 100

                    if left != 0 or top != 0:
                        geometries[subject.replace('EAID_', '')] = {
                            "x": left,
                            "y": abs(top),
                            "width": w_val,
                            "height": h_val
                        }
                except ValueError:
                    pass
    
    all_elements = []
    for elem in root.iter():
        tag_clean = elem.tag.split('}')[-1]
        if tag_clean in valid_tags:
            if elem.attrib.get('name') == 'EARootClass': continue
            all_elements.append(elem)
            
    class_xmi_types = ClassMapper.get_supported_xmi_types()
    relation_xmi_types = RelationBaseMapper.get_supported_xmi_types()
            
    for elem in all_elements:
        tag_clean = elem.tag.split('}')[-1]
        xmi_type = elem.attrib.get('{http://schema.omg.org/spec/XMI/2.1}type')
        if not xmi_type:
            xmi_type = f"uml:{tag_clean}"
            if xmi_type == 'uml:packagedElement': continue
            
        stereotype = None
        for tag_elem in elem.iter():
            if tag_elem.tag.endswith('TaggedValue') and tag_elem.attrib.get('tag') == 'stereotype':
                stereotype = tag_elem.attrib.get('value')
                break
                
        if not stereotype:
            ext = elem.find('.//Extension')
            if ext is not None and ext.attrib.get('stereotype'):
                stereotype = ext.attrib.get('stereotype')
            
        if xmi_type in class_xmi_types:
            node_id = elem.attrib.get('{http://schema.omg.org/spec/XMI/2.1}id') or elem.attrib.get('xmi.id')
            if node_id:
                node_id_clean = node_id.replace('EAID_', '')
                if geometries and node_id_clean not in geometries:
                    continue
                    
            mapper = ClassMapper.create(xmi_type, stereotype)
            node_dict = mapper.parse(elem, geometries)
            if node_dict:
                nodes.append(node_dict)
            
        elif xmi_type in relation_xmi_types:
            mapper = RelationBaseMapper.create(xmi_type, stereotype)
            rel_dict = mapper.parse(elem)
            if rel_dict:
                relations.append(rel_dict)
                
    return {
        "nodes": nodes,
        "relations": relations
    }
