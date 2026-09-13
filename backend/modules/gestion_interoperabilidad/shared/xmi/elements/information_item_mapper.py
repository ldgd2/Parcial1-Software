from .class_mapper import ClassMapper

class InformationItemMapper(ClassMapper):
    def get_node_type(self) -> str:
        return 'information_item'

    def get_xml_tag(self) -> str:
        return 'UML:Class'

    def get_stereotype(self) -> str:
        return 'information_item'
