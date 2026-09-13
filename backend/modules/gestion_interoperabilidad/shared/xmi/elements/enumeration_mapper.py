from .class_mapper import ClassMapper

class EnumerationMapper(ClassMapper):
    def get_node_type(self):
        return "enum"
        
    def get_stereotype(self):
        return "Enumeration"

    def apply_specific_properties(self, node_dict, elem):
        valores = []
        for lit in elem.iter():
            if lit.tag.endswith('EnumerationLiteral'):
                valores.append(lit.attrib.get('name', 'Valor'))
        node_dict['valores'] = valores

    def apply_xml_specific_properties(self, class_elem, cls):
        import xml.etree.ElementTree as ET
        for val in cls.get('valores', []):
            ET.SubElement(class_elem, "UML:EnumerationLiteral", attrib={"name": val})
