from .class_mapper import ClassMapper

class DestroyEventMapper(ClassMapper):
    def get_node_type(self):
        return "destroy_event"

    def get_xml_tag(self):
        return "UML:Event"

    def get_stereotype(self):
        return "Event"
        
    def get_stereotype(self):
        return "destroy"

    def apply_xml_specific_properties(self, class_elem, cls):
        super().apply_xml_specific_properties(class_elem, cls)
        import xml.etree.ElementTree as ET
        stereo_tags = ET.SubElement(class_elem, "UML:ModelElement.stereotype")
        ET.SubElement(stereo_tags, "UML:Stereotype", attrib={"name": "destroy"})
