import os

base_dir = r"c:\Users\ldgd2\Documents\universidad\software 1\sem 2-2026\examen1\Examen\backend\modules\gestion_interoperabilidad\shared\xmi\elements"

mappers = {
    "auxillary": ("Auxillary", "Class", "auxillary"),
    "focus": ("Focus", "Class", "focus"),
    "implementation_class": ("ImplementationClass", "Class", "implementationClass"),
    "realization_class": ("RealizationClass", "Class", "realization"),
    "specification": ("Specification", "Class", "specification"),
    "type": ("Type", "Class", "type"),
    "utility": ("Utility", "Class", "utility"),
    "create_event": ("CreateEvent", "Event", "create"),
    "destroy_event": ("DestroyEvent", "Event", "destroy")
}

template = """from .class_mapper import ClassMapper

class {class_name}Mapper(ClassMapper):
    def get_node_type(self):
        return "{node_type}"

    def get_xml_tag(self):
        return "UML:{ea_type}"

    def get_ea_stype(self):
        return "{ea_type}"
        
    def get_stereotype(self):
        return "{stereotype}"

    def apply_xml_specific_properties(self, class_elem, cls):
        super().apply_xml_specific_properties(class_elem, cls)
        import xml.etree.ElementTree as ET
        stereo_tags = ET.SubElement(class_elem, "UML:ModelElement.stereotype")
        ET.SubElement(stereo_tags, "UML:Stereotype", attrib={{"name": "{stereotype}"}})
"""

for key, (cls_name, ea_type, stereotype) in mappers.items():
    content = template.format(class_name=cls_name, node_type=key, ea_type=ea_type, stereotype=stereotype)
    with open(os.path.join(base_dir, f"{key}_mapper.py"), "w") as f:
        f.write(content)

# Update __init__.py
init_file = os.path.join(base_dir, "__init__.py")
with open(init_file, "a") as f:
    for key, (cls_name, _, _) in mappers.items():
        f.write(f"\nfrom .{key}_mapper import {cls_name}Mapper")
