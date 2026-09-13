from .class_mapper import ClassMapper

class PrimitiveMapper(ClassMapper):
    def get_node_type(self):
        return "primitive"
        
    def get_stereotype(self):
        return "PrimitiveType"
