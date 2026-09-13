from .relation_base import RelationBaseMapper

class AssociationMapper(RelationBaseMapper):
    def get_relation_type(self, elem):
        rel_type = "association"
        ends_uml = []
        for child in elem.iter():
            if child.tag.endswith('AssociationEnd') or child.tag.endswith('ownedEnd'):
                ends_uml.append(child)
        if len(ends_uml) == 2:
            agg = ends_uml[0].attrib.get('aggregation')
            if agg == 'composite': rel_type = "composition"
            elif agg == 'shared': rel_type = "aggregation"
            
        xmi_type = elem.attrib.get('{http://schema.omg.org/spec/XMI/2.1}type')
        if xmi_type == 'uml:AssociationClass':
            rel_type = "association_class"
            
        # check tagged values for specific ea variations
        for tag in elem.iter():
            if tag.tag.endswith('TaggedValue') and tag.attrib.get('tag') == 'ea_type':
                val = tag.attrib.get('value', '').lower()
                if val == 'associationclass':
                    rel_type = 'association_class'
                    
        return rel_type

    def get_ea_type(self, rel_type):
        if rel_type in ('aggregation', 'composition'): return "Aggregation"
        if rel_type == 'association_class': return "AssociationClass"
        return "Association"

    def apply_xml_tags(self, tags, rel, rel_type):
        import xml.etree.ElementTree as ET
        if rel_type == 'directed':
            ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "direction", "value": "Source -> Destination"})
        if rel.get('label'):
            ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "mt", "value": str(rel.get('label'))})
        if rel.get('sourceLabel'):
            ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "lb", "value": str(rel.get('sourceLabel'))})
        if rel.get('targetLabel'):
            ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "rb", "value": str(rel.get('targetLabel'))})

    def apply_xml_connections(self, elem, rel, rel_type):
        import xml.etree.ElementTree as ET
        conn = ET.SubElement(elem, "UML:Association.connection")
        
        agg_src = "none"
        if rel_type == 'aggregation': agg_src = "shared"
        elif rel_type == 'composition': agg_src = "composite"
        
        end1_attrib = {
            "visibility": "public", "aggregation": agg_src, "isOrdered": "false", "targetScope": "instance", "changeable": "none", "isNavigable": "false" if rel_type == 'directed' else "true",
            "type": f"EAID_{rel.get('sourceId', '')}"
        }
        if rel.get('sourceLabel'):
            end1_attrib["multiplicity"] = str(rel.get('sourceLabel'))
            
        end1 = ET.SubElement(conn, "UML:AssociationEnd", attrib=end1_attrib)
        
        end1_tags = ET.SubElement(end1, "UML:ModelElement.taggedValue")
        ET.SubElement(end1_tags, "UML:TaggedValue", attrib={"tag": "sourcestyle", "value": "Owned=0;Navigable=Navigable;" if rel_type != 'directed' else "Owned=0;Navigable=Non-Navigable;"})
        ET.SubElement(end1_tags, "UML:TaggedValue", attrib={"tag": "ea_end", "value": "source"})
        
        if rel.get('sourceLabel'):
            l, u = self._parse_mult(rel.get('sourceLabel'))
            mult = ET.SubElement(end1, "UML:AssociationEnd.multiplicity")
            mult_range = ET.SubElement(mult, "UML:Multiplicity")
            mult_range_comp = ET.SubElement(mult_range, "UML:Multiplicity.range")
            ET.SubElement(mult_range_comp, "UML:MultiplicityRange", attrib={"lower": l, "upper": u})
        
        end2_attrib = {
            "visibility": "public", "aggregation": "none", "isOrdered": "false", "targetScope": "instance", "changeable": "none", "isNavigable": "true",
            "type": f"EAID_{rel.get('targetId', '')}"
        }
        if rel.get('targetLabel'):
            end2_attrib["multiplicity"] = str(rel.get('targetLabel'))
            
        end2 = ET.SubElement(conn, "UML:AssociationEnd", attrib=end2_attrib)
        
        end2_tags = ET.SubElement(end2, "UML:ModelElement.taggedValue")
        ET.SubElement(end2_tags, "UML:TaggedValue", attrib={"tag": "deststyle", "value": "Owned=0;Navigable=Non-Navigable;" if rel_type != 'directed' else "Owned=0;Navigable=Navigable;"})
        ET.SubElement(end2_tags, "UML:TaggedValue", attrib={"tag": "ea_end", "value": "target"})
        
        if rel.get('targetLabel'):
            l, u = self._parse_mult(rel.get('targetLabel'))
            mult = ET.SubElement(end2, "UML:AssociationEnd.multiplicity")
            mult_range = ET.SubElement(mult, "UML:Multiplicity")
            mult_range_comp = ET.SubElement(mult_range, "UML:Multiplicity.range")
            ET.SubElement(mult_range_comp, "UML:MultiplicityRange", attrib={"lower": l, "upper": u})
