from .relation_base import RelationBaseMapper

class DependencyMapper(RelationBaseMapper):
    def get_relation_type(self, elem):
        xmi_type = elem.attrib.get('{http://schema.omg.org/spec/XMI/2.1}type')
        if not xmi_type: xmi_type = f"uml:{elem.tag.split('}')[-1]}"
        
        rel_type = "dependency"
        for tag in elem.iter():
            if tag.tag.endswith('TaggedValue') and tag.attrib.get('tag') == 'stereotype':
                st = tag.attrib.get('value', '').lower()
                if st == 'realize': rel_type = "realization"
                elif st == 'instantiate': rel_type = "instantiate"
                elif st == 'substitute': rel_type = "substitution"
                elif st == 'trace': rel_type = "trace"
                elif st == 'bind': rel_type = "template_binding"
                elif st == 'call': rel_type = "calls"
            if tag.tag.endswith('TaggedValue') and tag.attrib.get('tag') == 'ea_type':
                eat = tag.attrib.get('value', '').lower()
                if eat == 'realisation': rel_type = 'realization'
                elif eat == 'usage': rel_type = 'usage'
                elif eat == 'abstraction': rel_type = 'abstraction'
                elif eat == 'informationflow': rel_type = 'information_flow'
                
        if xmi_type == 'uml:Abstraction': rel_type = "abstraction"
        elif xmi_type == 'uml:Usage': rel_type = "usage"
        elif xmi_type == 'uml:TemplateBinding': rel_type = "template_binding"
        elif xmi_type == 'uml:InformationFlow': rel_type = "information_flow"
        return rel_type

    def get_xml_tag(self, rel_type):
        if rel_type in ('abstraction', 'usage', 'information_flow'):
            return f"UML:{rel_type.capitalize().replace('_', '')}"
        return "UML:Dependency"

    def get_ea_type(self, rel_type):
        if rel_type in ('abstraction', 'usage', 'information_flow'):
            return rel_type.capitalize().replace('_', '')
        if rel_type == 'realization': return "Realisation"
        return "Dependency"
        
    def apply_xml_attribs(self, attribs, rel):
        attribs["client"] = f"EAID_{rel.get('sourceId', '')}"
        attribs["supplier"] = f"EAID_{rel.get('targetId', '')}"
        
    def apply_xml_tags(self, tags, rel, rel_type):
        import xml.etree.ElementTree as ET
        stereotype = None
        if rel_type == 'realization': stereotype = "realize"
        elif rel_type == 'instantiate': stereotype = "instantiate"
        elif rel_type == 'substitution': stereotype = "substitute"
        elif rel_type == 'trace': stereotype = "trace"
        elif rel_type == 'calls': stereotype = "call"
        elif rel_type == 'template_binding': stereotype = "bind"
        
        if stereotype:
            ET.SubElement(tags, "UML:TaggedValue", attrib={"tag": "stereotype", "value": stereotype})
