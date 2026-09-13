from .class_mapper import ClassMapper

class SignalMapper(ClassMapper):
    def get_node_type(self):
        return "signal"
        
    def get_stereotype(self):
        return "Signal"
