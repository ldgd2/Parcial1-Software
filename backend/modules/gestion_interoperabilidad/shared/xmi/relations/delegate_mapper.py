from .dependency_mapper import DependencyMapper

class DelegateMapper(DependencyMapper):
    def get_relation_type(self, elem):
        return "delegate"

    def get_ea_type(self, rel_type):
        return "Delegate"
        
    def apply_xml_tags(self, tags, rel, rel_type):
        super().apply_xml_tags(tags, rel, rel_type)
        import xml.etree.ElementTree as ET
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "stereotype", "value": "delegate"})
