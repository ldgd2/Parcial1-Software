from .class_mapper import ClassMapper

class InterfaceMapper(ClassMapper):
    def get_node_type(self):
        return "interface"
        
    def get_stereotype(self):
        return "Interface"
