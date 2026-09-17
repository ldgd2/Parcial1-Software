import xml.etree.ElementTree as ET

xml = """
<UML:Class name="DataType1" xmi.id="EAID_123">
    <UML:ModelElement.stereotype>
        <UML:Stereotype name="DataType"/>
    </UML:ModelElement.stereotype>
</UML:Class>
"""

root = ET.fromstring(xml)
stereotype = None
for s_elem in root.iter():
    print(f"Found tag: {s_elem.tag}")
    if s_elem.tag.endswith('Stereotype'):
        stereotype = s_elem.attrib.get('name')
        print(f"Match! Stereotype: {stereotype}")
        break

print(f"Result: {stereotype}")
