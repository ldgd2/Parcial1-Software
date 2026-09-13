import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.modules.gestion_interoperabilidad.shared.xmi.elements.class_mapper import ClassMapper
from backend.modules.gestion_interoperabilidad.shared.xmi.relations.relation_base import RelationBaseMapper
import backend.modules.gestion_interoperabilidad.shared.xmi.elements
import backend.modules.gestion_interoperabilidad.shared.xmi.relations

print("ClassMapper tags:", ClassMapper.get_supported_tags())
print("RelationBaseMapper tags:", RelationBaseMapper.get_supported_tags())

mapper1 = ClassMapper.create('uml:Class')
mapper2 = ClassMapper.create('uml:Focus')
print("ClassMapper for uml:Focus:", type(mapper2).__name__)

rel_mapper1 = RelationBaseMapper.create('uml:Create')
print("RelationBaseMapper for uml:Create:", type(rel_mapper1).__name__)

