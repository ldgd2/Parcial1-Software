from .relation_base import RelationBaseMapper

class AssemblyMapper(RelationBaseMapper):
    def get_relation_type(self, elem):
        return "assembly"

    def get_xml_tag(self, rel_type):
        return "UML:Connector"

    def get_ea_type(self, rel_type):
        return "Assembly"
