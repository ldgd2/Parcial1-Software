from .class_mapper import ClassMapper

class ExposeInterfaceMapper(ClassMapper):
    def get_node_type(self):
        return "expose_interface"

    def get_xml_tag(self):
        return "UML:ProvidedInterface"

    def get_stereotype(self):
        return "ProvidedInterface"
