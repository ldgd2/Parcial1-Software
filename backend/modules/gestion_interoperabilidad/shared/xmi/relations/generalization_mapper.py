from .relation_base import RelationBaseMapper

class GeneralizationMapper(RelationBaseMapper):
    def get_relation_type(self, elem):
        return "inheritance"

    def get_xml_tag(self, rel_type):
        return "UML:Generalization"

    def get_ea_type(self, rel_type):
        return "Generalization"
        
    def apply_xml_attribs(self, attribs, rel):
        attribs["subtype"] = f"EAID_{rel.get('sourceId', '')}"
        attribs["supertype"] = f"EAID_{rel.get('targetId', '')}"
