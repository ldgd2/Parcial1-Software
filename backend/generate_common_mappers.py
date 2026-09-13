import os

MAPPERS_DIR = "modules/gestion_interoperabilidad/shared/xmi/elements"

ELEMENTS = [
    ("constraint", "Constraint", "uml:Class", True),
    ("text", "Text", "uml:Class", True),
    ("artifact", "Artifact", "uml:Class", True),
    ("requirement", "Requirement", "uml:Class", True),
    ("issue", "Issue", "uml:Class", True),
    ("change", "Change", "uml:Class", True),
    ("information_item", "InformationItem", "uml:Class", True),
    ("boundary", "Boundary", "uml:Class", True),
]

TEMPLATE = """from .class_mapper import ClassMapper

class {class_name}Mapper(ClassMapper):
    def get_node_type(self) -> str:
        return '{frontend_type}'

    def get_xml_tag(self) -> str:
        return 'UML:Class'

    def get_stereotype(self) -> str:
        return '{frontend_type}'
"""

def main():
    if not os.path.exists(MAPPERS_DIR):
        print(f"Error: Directory {MAPPERS_DIR} not found.")
        return

    for frontend_type, class_name, xml_type, is_st in ELEMENTS:
        file_name = f"{frontend_type}_mapper.py"
        file_path = os.path.join(MAPPERS_DIR, file_name)
        
        content = TEMPLATE.format(
            class_name=class_name,
            frontend_type=frontend_type
        )
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Generado {file_path}")

    # Ahora añadimos al __init__.py
    init_path = os.path.join(MAPPERS_DIR, "__init__.py")
    with open(init_path, "a", encoding="utf-8") as f:
        f.write("\n# Common\n")
        for frontend_type, class_name, _, _ in ELEMENTS:
            f.write(f"from .{frontend_type}_mapper import {class_name}Mapper\n")

if __name__ == "__main__":
    main()
