from .class_mapper import ClassMapper

class NoteMapper(ClassMapper):
    def get_node_type(self):
        return "note"
        
    def get_xml_tag(self):
        return "UML:Comment"

    def get_stereotype(self):
        return "Note"

    def apply_specific_properties(self, node_dict, elem):
        node_dict['contenido'] = elem.attrib.get('body', 'Nota')
        node_dict['nombre'] = 'Nota'
