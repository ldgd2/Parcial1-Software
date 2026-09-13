from .class_mapper import ClassMapper

class TextMapper(ClassMapper):
    def get_node_type(self) -> str:
        return 'text'

    def get_xml_tag(self) -> str:
        return 'UML:Class'

    def get_stereotype(self) -> str:
        return 'text'
