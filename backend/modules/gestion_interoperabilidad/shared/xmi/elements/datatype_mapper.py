from .class_mapper import ClassMapper

class DataTypeMapper(ClassMapper):
    def get_node_type(self):
        return "datatype"

    def get_xml_tag(self):
        return "UML:DataType"
        
    def get_stereotype(self):
        return "DataType"
