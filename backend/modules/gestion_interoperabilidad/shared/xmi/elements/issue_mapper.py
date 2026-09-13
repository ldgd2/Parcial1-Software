from .class_mapper import ClassMapper

class IssueMapper(ClassMapper):
    def get_node_type(self) -> str:
        return 'issue'

    def get_xml_tag(self) -> str:
        return 'UML:Class'

    def get_stereotype(self) -> str:
        return 'issue'
