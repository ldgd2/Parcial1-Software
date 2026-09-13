from .class_mapper import ClassMapper

class SpecificationMapper(ClassMapper):
    def get_node_type(self):
        return "specification"

    def get_xml_tag(self):
        return "UML:Class"

    def get_stereotype(self):
        return "Class"
        
    def get_stereotype(self):
        return "specification"

    def apply_xml_specific_properties(self, class_elem, cls):
        super().apply_xml_specific_properties(class_elem, cls)
        import xml.etree.ElementTree as ET
        stereo_tags = ET.SubElement(class_elem, "UML:ModelElement.stereotype")
        ET.SubElement(stereo_tags, "UML:Stereotype", attrib={"name": "specification"})
