import uuid

class RelationBaseMapper:
    @classmethod
    def _get_all_subclasses(cls):
        subs = []
        for c in cls.__subclasses__():
            subs.append(c)
            subs.extend(c._get_all_subclasses())
        return subs

    @classmethod
    def get_supported_tags(cls):
        tags = set()
        for sub_cls in cls._get_all_subclasses():
            tag = sub_cls().get_xml_tag("").split(':')[-1]
            tags.add(tag)
        # some tags like Connector might be base tags in get_xml_tag
        return list(tags)

    @classmethod
    def get_supported_xmi_types(cls):
        return [f"uml:{t}" for t in cls.get_supported_tags()]

    @classmethod
    def get_export_type_map(cls):
        mapping = {}
        for sub_cls in cls._get_all_subclasses():
            inst = sub_cls()
            # mapping logic might be complex here, so we will keep a static fallback map too
            pass
        return {
            'inheritance': 'uml:Generalization',
            'dependency': 'uml:Dependency',
            'realization': 'uml:Dependency',
            'instantiate': 'uml:Dependency',
            'substitution': 'uml:Dependency',
            'trace': 'uml:Dependency',
            'calls': 'uml:Dependency',
            'template_binding': 'uml:Dependency',
            'delegate': 'uml:Dependency',
            'abstraction': 'uml:Abstraction',
            'usage': 'uml:Usage',
            'information_flow': 'uml:InformationFlow',
            'association_class': 'uml:AssociationClass',
            'assembly': 'uml:Connector',
            'connector': 'uml:Connector',
            'association': 'uml:Association',
            'create': 'uml:Dependency',
            'send': 'uml:Dependency'
        }

    @classmethod
    def create(cls, xmi_type, stereotype=None):
        if stereotype:
            for sub_cls in cls._get_all_subclasses():
                inst = sub_cls()
                tag = inst.get_xml_tag("").split(':')[-1]
                if xmi_type.endswith(tag) and hasattr(inst, 'get_stereotype'):
                    if inst.get_stereotype().lower() == stereotype.lower():
                        return inst

        for sub_cls in cls._get_all_subclasses():
            inst = sub_cls()
            tag = inst.get_xml_tag("").split(':')[-1]
            if xmi_type.endswith(tag) and not hasattr(inst, 'get_stereotype'):
                return inst
        # special fallback logic for relationships sharing the same tag
        if xmi_type in ['uml:Association', 'uml:AssociationClass']:
            from .association_mapper import AssociationMapper
            return AssociationMapper()
        elif xmi_type in ['uml:Dependency', 'uml:Abstraction', 'uml:Usage', 'uml:TemplateBinding', 'uml:InformationFlow']:
            from .dependency_mapper import DependencyMapper
            return DependencyMapper()
        elif xmi_type == 'uml:Generalization':
            from .generalization_mapper import GeneralizationMapper
            return GeneralizationMapper()
        elif xmi_type == 'uml:Connector':
            from .connector_mapper import ConnectorMapper
            return ConnectorMapper()
        return cls()

    def parse(self, elem):
        rel_id = elem.attrib.get('{http://schema.omg.org/spec/XMI/2.1}id') or elem.attrib.get('xmi.id') or str(uuid.uuid4())
        name = elem.attrib.get('name', '')

        src = elem.attrib.get('client') or elem.attrib.get('child')
        tgt = elem.attrib.get('supplier') or elem.attrib.get('parent')

        src_lbl = ""
        tgt_lbl = ""
        
        rel_type = self.get_relation_type(elem)
        
        # Parse from AssociationEnds if any
        ends_uml = []
        for child in elem.iter():
            if child.tag.endswith('AssociationEnd') or child.tag.endswith('ownedEnd'):
                ends_uml.append(child)
                
        if len(ends_uml) == 2:
            src = ends_uml[0].attrib.get('type')
            tgt = ends_uml[1].attrib.get('type')
            
            agg = ends_uml[0].attrib.get('aggregation')
            if agg == 'composite':
                rel_type = "composition"
            elif agg == 'shared':
                rel_type = "aggregation"
                
            def get_mult(end_elem):
                for mr in end_elem.iter():
                    if mr.tag.endswith('MultiplicityRange'):
                        lower = mr.attrib.get('lower', '')
                        upper = mr.attrib.get('upper', '')
                        if lower == upper: return lower
                        if upper == '-1': return f"{lower}..*"
                        return f"{lower}..{upper}"
                return ""
                
            src_lbl = ends_uml[0].attrib.get('multiplicity') or get_mult(ends_uml[0])
            tgt_lbl = ends_uml[1].attrib.get('multiplicity') or get_mult(ends_uml[1])
        
        # Tagged Values fallback
        if not src and not tgt:
            for tag in elem.iter():
                if tag.tag.endswith('TaggedValue'):
                    if tag.attrib.get('tag') == 'ea_sourceID': src = tag.attrib.get('value')
                    if tag.attrib.get('tag') == 'ea_targetID': tgt = tag.attrib.get('value')
                    if tag.attrib.get('tag') == 'lb': src_lbl = tag.attrib.get('value')
                    if tag.attrib.get('tag') == 'rb': tgt_lbl = tag.attrib.get('value')
        
        if src and tgt:
            src = src.replace('EAID_', '')
            tgt = tgt.replace('EAID_', '')
            
            if src_lbl or tgt_lbl:
                src_clean = str(src_lbl).replace('*', 'N').replace('..N', '..*').lower() if src_lbl else ''
                tgt_clean = str(tgt_lbl).replace('*', 'N').replace('..N', '..*').lower() if tgt_lbl else ''
                
                if src_clean == '1' and tgt_clean == '1': rel_type = '1:1'
                elif src_clean == '1' and (tgt_clean == 'n' or tgt_clean == '*'): rel_type = '1:N'
                elif (src_clean == 'n' or src_clean == '*') and (tgt_clean == 'n' or tgt_clean == '*'): rel_type = 'N:M'
                elif src_clean == '0..1' and tgt_clean == '1': rel_type = '0..1:1'
                elif src_clean == '0..1' and (tgt_clean == 'n' or tgt_clean == '*'): rel_type = '0..1:N'
                elif src_clean == '0..*' and tgt_clean == '1': rel_type = '0..N:1'
                elif src_clean == '0..*' and (tgt_clean == 'n' or tgt_clean == '*'): rel_type = '0..N:M'
            
            return {
                "id": rel_id.replace('EAID_', ''),
                "type": rel_type,
                "sourceId": src,
                "targetId": tgt,
                "label": name,
                "sourceLabel": src_lbl,
                "targetLabel": tgt_lbl,
                "version": 0
            }
        return None

    def get_relation_type(self, elem):
        return "association"
        
    def to_xml(self, rel, pkg_owned, diag_elems, duid_map, i):
        import xml.etree.ElementTree as ET
        
        rel_type = rel.get('type', 'association')
        rel_id = rel.get('id', '')
        
        if rel_type in ['1:1', '1:N', 'N:M', '0..1:1', '0..1:N', '0..N:1', '0..N:M']:
            if not rel.get('sourceLabel') or not rel.get('targetLabel'):
                if rel_type == '1:1': rel['sourceLabel'], rel['targetLabel'] = '1', '1'
                elif rel_type == '1:N': rel['sourceLabel'], rel['targetLabel'] = '1', '*'
                elif rel_type == 'N:M': rel['sourceLabel'], rel['targetLabel'] = '*', '*'
                elif rel_type == '0..1:1': rel['sourceLabel'], rel['targetLabel'] = '0..1', '1'
                elif rel_type == '0..1:N': rel['sourceLabel'], rel['targetLabel'] = '0..1', '*'
                elif rel_type == '0..N:1': rel['sourceLabel'], rel['targetLabel'] = '0..*', '1'
                elif rel_type == '0..N:M': rel['sourceLabel'], rel['targetLabel'] = '0..*', '*'
            rel_type = 'association'
            
        elem_name = self.get_xml_tag(rel_type)
        ea_type = self.get_ea_type(rel_type)
        
        attribs = {
            "xmi.id": f"EAID_{rel_id}",
            "visibility": "public",
            "isRoot": "false", "isLeaf": "false", "isAbstract": "false"
        }
        
        self.apply_xml_attribs(attribs, rel)
        
        elem = ET.SubElement(pkg_owned, elem_name, attrib=attribs)
        tags = ET.SubElement(elem, "UML:ModelElement.taggedValue")
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "ea_type", "value": ea_type})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "direction", "value": "Source -> Destination"})
        
        self.apply_xml_tags(tags, rel, rel_type)
        
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "style", "value": "3"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "linemode", "value": "3"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "linecolor", "value": "0"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "linewidth", "value": "0"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "seqno", "value": "0"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "headStyle", "value": "0"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "lineStyle", "value": "0"})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "ea_sourceID", "value": str(rel.get('sourceId', ''))})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "ea_targetID", "value": str(rel.get('targetId', ''))})
        ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "virtualInheritance", "value": "0"})
        
        self.apply_xml_connections(elem, rel, rel_type)
        
        # Diagram info
        src_id = rel.get('sourceId', '')
        tgt_id = rel.get('targetId', '')
        soid = duid_map.get(src_id, '')
        eoid = duid_map.get(tgt_id, '')
        
        src_lbl = str(rel.get('sourceLabel') or '').replace(';', ',')
        tgt_lbl = str(rel.get('targetLabel') or '').replace(';', ',')
        mid_lbl = str(rel.get('label') or '').replace(';', ',')
        
        geometry_str = f"SX=0;SY=0;EX=0;EY=0;EDGE=2;$LLB={src_lbl};LLT=;LMT={mid_lbl};LMB=;LRT=;LRB={tgt_lbl};IRHS=;ILHS=;Path=;"
        
        ET.SubElement(diag_elems, "UML:DiagramElement", attrib={
            "geometry": geometry_str,
            "subject": f"EAID_{rel_id}",
            "style": f"Mode=3;EOID={eoid};SOID={soid};Color=-1;LWidth=0;Hidden=0;"
        })

    def get_xml_tag(self, rel_type):
        return "UML:Association"
        
    def get_ea_type(self, rel_type):
        return "Association"
        
    def apply_xml_attribs(self, attribs, rel):
        pass
        
    def apply_xml_tags(self, tags, rel, rel_type):
        pass
        
    def apply_xml_connections(self, elem, rel, rel_type):
        pass

    def _parse_mult(self, val):
        val = str(val).strip().replace('*', '-1').replace('N', '-1')
        if '..' in val:
            parts = val.split('..', 1)
            return parts[0], parts[1]
        return val, val
