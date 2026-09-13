from .class_mapper import ClassMapper

class ConstraintMapper(ClassMapper):
    def get_node_type(self) -> str:
        return 'constraint'

    def get_xml_tag(self) -> str:
        return 'UML:Class'

    def get_stereotype(self) -> str:
        return 'constraint'
