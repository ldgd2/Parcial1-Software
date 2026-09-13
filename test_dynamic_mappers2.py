import sys
import os
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.modules.gestion_interoperabilidad.shared.xmi.elements.class_mapper import ClassMapper
from backend.modules.gestion_interoperabilidad.shared.xmi.relations.relation_base import RelationBaseMapper
import backend.modules.gestion_interoperabilidad.shared.xmi.elements
import backend.modules.gestion_interoperabilidad.shared.xmi.relations

print("Testing dynamic parsing of stereotypes...")
mapper = ClassMapper.create("uml:Class", stereotype="focus")
print("Mapper for uml:Class with stereotype=focus:", type(mapper).__name__)

mapper2 = ClassMapper.create("uml:Event", stereotype="create")
print("Mapper for uml:Event with stereotype=create:", type(mapper2).__name__)

mapper3 = RelationBaseMapper.create("uml:Dependency", stereotype="create")
print("Relation mapper for uml:Dependency with stereotype=create:", type(mapper3).__name__)

