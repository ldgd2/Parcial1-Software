import os

base_dir = r"c:\Users\ldgd2\Documents\universidad\software 1\sem 2-2026\examen1\Examen\backend\modules\gestion_interoperabilidad\shared\xmi\relations"

mappers = {
    "create": ("Create", "Dependency", "create"),
    "send": ("Send", "Dependency", "send"),
}

template = """from .dependency_mapper import DependencyMapper

class {class_name}Mapper(DependencyMapper):
    def get_relation_type(self, elem):
        return "{node_type}"

    def get_ea_type(self, rel_type):
        return "{class_name}"
        
    def get_stereotype(self):
        return "{stereotype}"
        
    def apply_xml_tags(self, tags, rel, rel_type):
        super().apply_xml_tags(tags, rel, rel_type)
        import xml.etree.ElementTree as ET
        ET.SubElement(tags, "UML:TaggedValue", attrib={{"tag": "stereotype", "value": "{stereotype}"}})
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
