import uuid
import random

class ClassMapper:
    @classmethod
    def _get_all_subclasses(cls):
        subs = []
        for c in cls.__subclasses__():
            subs.append(c)
            subs.extend(c._get_all_subclasses())
        return subs

    @classmethod
    def get_supported_tags(cls):
        tags = set()
        for sub_cls in cls._get_all_subclasses():
            tag = sub_cls().get_xml_tag()
            tags.add(tag.split(':')[-1])
        tags.add('Class')
        return list(tags)

    @classmethod
    def get_supported_xmi_types(cls):
        return [f"uml:{t}" for t in cls.get_supported_tags()]

    @classmethod
    def get_export_type_map(cls):
        mapping = {}
        for sub_cls in cls._get_all_subclasses():
            inst = sub_cls()
            mapping[inst.get_node_type()] = inst.get_xml_tag().replace('UML:', 'uml:')
        # Fallbacks
        mapping['class'] = 'uml:Class'
        return mapping

    @classmethod
    def create(cls, xmi_type, stereotype=None):
        # 1. Match xmi_type AND stereotype (for specialized mappers)
        if stereotype:
            for sub_cls in cls._get_all_subclasses():
                inst = sub_cls()
                if hasattr(inst, 'get_stereotype'):
                    if inst.get_stereotype().lower() == stereotype.lower():
                        return inst

        # 2. Match xmi_type ONLY (for generic mappers that don't enforce a stereotype)
        for sub_cls in cls._get_all_subclasses():
            inst = sub_cls()
            tag = inst.get_xml_tag().replace('UML:', 'uml:')
            if xmi_type == tag and not hasattr(inst, 'get_stereotype'):
                return inst

        return cls()

    def parse(self, elem, geometries):
        node_id = elem.attrib.get('{http://schema.omg.org/spec/XMI/2.1}id') or elem.attrib.get('xmi.id') or str(uuid.uuid4())
        name = elem.attrib.get('name', 'Elemento')
        node_type = self.get_node_type()

        is_abstract = elem.attrib.get('isAbstract') == 'true'
        if is_abstract and node_type == "class": node_type = "abstract"
        
        is_table = False
        for tag in elem.iter():
            if tag.tag.endswith('TaggedValue') and tag.attrib.get('tag') == 'stereotype' and tag.attrib.get('value') == 'table':
                is_table = True
        ext = elem.find('.//Extension')
        if ext is not None and ext.attrib.get('stereotype') == 'table':
            is_table = True
            
        atributos = self.parse_attributes(elem)
        metodos = self.parse_methods(elem)
                
        node_id_clean = node_id.replace('EAID_', '')
        
        x, y, width, height = self.get_geometry(node_id_clean, geometries)

        color_map = {
            "class": "#ed8936",
            "abstract": "#ed8936",
            "interface": "#b794f4",
            "datatype": "#ecc94b",
            "primitive": "#a3e635",
            "signal": "#fefcbf",
            "enum": "#68d391",
            "part": "#ecc94b",
            "port": "#ed8936"
        }
        
        node_color = color_map.get(node_type, "#ed8936")
        if is_table:
            node_color = "#1a5c3a"

        node_dict = {
            "id": node_id_clean,
            "type": node_type,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "nombre": name,
            "color": node_color,
            "atributos": atributos,
            "metodos": metodos,
            "version": 0,
            "estereotipo": "table" if is_table else None
        }
        
        self.apply_specific_properties(node_dict, elem)
        return node_dict

    def get_node_type(self):
        return "class"
        
    def parse_attributes(self, elem):
        atributos = []
        for attr in elem.iter():
            if attr.tag.endswith('Attribute') or attr.tag.endswith('ownedAttribute'):
                attr_name = attr.attrib.get('name', 'attr')
                vis = '+' if attr.attrib.get('visibility') == 'public' else '-'
                
                tipo = 'String'
                type_elem = attr.find('.//*type')
                if type_elem is not None:
                    href = type_elem.attrib.get('href', '')
                    if '#' in href: tipo = href.split('#')[-1]
                else:
                    for tag in attr.iter():
                        if tag.tag.endswith('TaggedValue') and tag.attrib.get('tag') == 'type':
                            tipo = tag.attrib.get('value', 'String')
                            break
                
                atributos.append({
                    "id": attr.attrib.get('{http://schema.omg.org/spec/XMI/2.1}id') or attr.attrib.get('xmi.id') or str(uuid.uuid4()),
                    "nombre": attr_name,
                    "visibilidad": vis,
                    "tipo": tipo,
                    "version": 0
                })
        return atributos

    def parse_methods(self, elem):
        metodos = []
        for met in elem.iter():
            if met.tag.endswith('Operation') or met.tag.endswith('ownedOperation'):
                met_name = met.attrib.get('name', 'metodo')
                vis = '+' if met.attrib.get('visibility') == 'public' else '-'
                
                metodos.append({
                    "id": met.attrib.get('{http://schema.omg.org/spec/XMI/2.1}id') or met.attrib.get('xmi.id') or str(uuid.uuid4()),
                    "nombre": met_name,
                    "visibilidad": vis,
                    "parametros": "",
                    "retorno": "void",
                    "version": 0
                })
        return metodos

    def get_geometry(self, node_id_clean, geometries):
        x = random.randint(100, 500)
        y = random.randint(100, 500)
        width = 220
        height = 100
        if node_id_clean in geometries:
            x = geometries[node_id_clean]['x']
            y = geometries[node_id_clean]['y']
            width = geometries[node_id_clean].get('width', 220)
            height = geometries[node_id_clean].get('height', 100)
        return x, y, width, height
        
    def apply_specific_properties(self, node_dict, elem):
        pass
        
    # --- EXPORT LOGIC ---
    def to_xml(self, cls, pkg_owned, proyecto_id):
        import xml.etree.ElementTree as ET
        cls_id = cls.get('id', '')
        
        elem_tag = self.get_xml_tag()
        
        class_elem = ET.SubElement(pkg_owned, elem_tag, attrib={
            "name": str(cls.get('nombre', 'Unnamed')) if self.get_node_type() != 'note' else '',
            "body": str(cls.get('contenido', cls.get('nombre', ''))) if self.get_node_type() == 'note' else '',
            "xmi.id": f"EAID_{cls_id}",
            "visibility": "public",
            "namespace": f"EAPK_{proyecto_id}",
            "isRoot": "false", "isLeaf": "false",
            "isAbstract": "true" if cls.get('type') == 'abstract' else "false",
            "isActive": "false"
        })
        
        tags = ET.SubElement(class_elem, "UML:ModelElement.taggedValue")
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "isSpecification", "value": "false"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "ea_stype", "value": self.get_stereotype()})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "ea_ntype", "value": "0"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "package", "value": f"EAPK_{proyecto_id}"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "package_name", "value": "ExportedModel"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "ea_eleType", "value": "element"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "style", "value": "BackColor=-1;BorderColor=-1;BorderWidth=-1;FontColor=-1;VSwimLanes=1;HSwimLanes=1;BorderStyle=0;"})
        
        if cls.get('estereotipo') == 'table':
            stereo_tags = ET.SubElement(class_elem, "UML:ModelElement.stereotype")
            ET.SubElement(stereo_tags, "UML:Stereotype", attrib={"name": "table"})
            ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "stereotype", "value": "table"})
            
        self.apply_xml_specific_properties(class_elem, cls)
            
        if cls.get('atributos') or cls.get('metodos'):
            feature = ET.SubElement(class_elem, "UML:Classifier.feature")
            for i_attr, attr in enumerate(cls.get('atributos', [])):
                attr_elem = ET.SubElement(feature, "UML:Attribute", attrib={
                    "name": str(attr.get('nombre', '')),
                    "visibility": "public" if attr.get('visibilidad') == '+' else ("protected" if attr.get('visibilidad') == '#' else "private"),
                    "ownerScope": "instance",
                    "targetScope": "instance",
                    "changeable": "none"
                })
                
                init_val = ET.SubElement(attr_elem, "UML:Attribute.initialValue")
                ET.SubElement(init_val, "UML:Expression")
                
                type_feat = ET.SubElement(attr_elem, "UML:StructuralFeature.type")
                ET.SubElement(type_feat, "UML:Classifier", attrib={"xmi.idref": "eaxmiid0"})
                
                attr_tags = ET.SubElement(attr_elem, "UML:ModelElement.taggedValue")
                ET.SubElement(attr_tags, "UML:TaggedValue", attrib={"tag": "type", "value": str(attr.get('tipo', 'int'))})
                ET.SubElement(attr_tags, "UML:TaggedValue", attrib={"tag": "derived", "value": "0"})
                ET.SubElement(attr_tags, "UML:TaggedValue", attrib={"tag": "length", "value": "0"})
                ET.SubElement(attr_tags, "UML:TaggedValue", attrib={"tag": "ordered", "value": "0"})
                ET.SubElement(attr_tags, "UML:TaggedValue", attrib={"tag": "precision", "value": "0"})
                ET.SubElement(attr_tags, "UML:TaggedValue", attrib={"tag": "scale", "value": "0"})
                ET.SubElement(attr_tags, "UML:TaggedValue", attrib={"tag": "static", "value": "0"})
                ET.SubElement(attr_tags, "UML:TaggedValue", attrib={"tag": "collection", "value": "false"})
                ET.SubElement(attr_tags, "UML:TaggedValue", attrib={"tag": "position", "value": str(i_attr)})
                ET.SubElement(attr_tags, "UML:TaggedValue", attrib={"tag": "lowerBound", "value": "1"})
                ET.SubElement(attr_tags, "UML:TaggedValue", attrib={"tag": "upperBound", "value": "1"})
                
            for i_met, met in enumerate(cls.get('metodos', [])):
                op_elem = ET.SubElement(feature, "UML:Operation", attrib={
                    "name": str(met.get('nombre', '')),
                    "visibility": "public" if met.get('visibilidad') == '+' else ("protected" if met.get('visibilidad') == '#' else "private"),
                    "ownerScope": "instance",
                    "isQuery": "false",
                    "concurrency": "sequential"
                })
                op_tags = ET.SubElement(op_elem, "UML:ModelElement.taggedValue")
                ET.SubElement(op_tags, "UML:TaggedValue", attrib={"tag": "const", "value": "false"})
                ET.SubElement(op_tags, "UML:TaggedValue", attrib={"tag": "synchronised", "value": "0"})
                ET.SubElement(op_tags, "UML:TaggedValue", attrib={"tag": "position", "value": str(i_met)})
                ET.SubElement(op_tags, "UML:TaggedValue", attrib={"tag": "returnarray", "value": "0"})
                ET.SubElement(op_tags, "UML:TaggedValue", attrib={"tag": "pure", "value": "0"})
        return class_elem

    def get_xml_tag(self):
        return "UML:Class"

    def get_stereotype(self):
        return "Class"
        
    def apply_xml_specific_properties(self, class_elem, cls):
        pass
