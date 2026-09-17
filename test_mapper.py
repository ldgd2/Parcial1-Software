import os
import sys

# Add backend directory to sys.path so we can import modules
sys.path.append(os.path.abspath("backend"))

from backend.modules.gestion_interoperabilidad.shared.xmi.elements.class_mapper import ClassMapper
import backend.modules.gestion_interoperabilidad.shared.xmi.elements

mapper = ClassMapper.create("uml:Class", "DataType")
print(f"Created mapper: {type(mapper)}")
print(f"Subclasses: {ClassMapper._get_all_subclasses()}")
