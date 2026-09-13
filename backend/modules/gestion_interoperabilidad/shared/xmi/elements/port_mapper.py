from .class_mapper import ClassMapper

class PortMapper(ClassMapper):
    def get_node_type(self):
        return "port"

    def get_xml_tag(self):
        return "UML:Port"

    def get_stereotype(self):
        return "Port"
