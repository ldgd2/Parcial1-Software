from .class_mapper import ClassMapper

class PartMapper(ClassMapper):
    def get_node_type(self):
        return "part"

    def get_xml_tag(self):
        return "UML:Part"

    def get_stereotype(self):
        return "Part"
